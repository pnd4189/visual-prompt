"""I/O utilities — checked writes for crash-safe persistence."""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any


def _is_cloud_mount_path(path: Path) -> bool:
    text = str(path)
    return '/cloud/gdrive/' in text or '/.cache/rclone/' in text


def _fsync_if_safe(file_obj, path: Path) -> None:
    if not _is_cloud_mount_path(path):
        os.fsync(file_obj.fileno())


# A cold read on a Drive mount costs a network round-trip — measured at 0.5-0.9s
# for the files this pipeline handles, against 0.001s once the mount has them
# cached. The timeout is there for a genuinely hung stale file, but a single
# latency spike past it used to kill the whole step: one re-assemble died on a
# chapter that read back in 0.52s a minute later (observed 2026-08-13). Retrying
# tells a spike apart from a hang without giving up the fast failure.
_CLOUD_READ_ATTEMPTS = 3


def read_text_checked(path: Path, *, timeout_seconds: int = 3) -> str:
    """Read UTF-8 text, failing fast on cloud mounts that hang on stale files."""
    path = Path(path)
    if not _is_cloud_mount_path(path):
        return path.read_text(encoding='utf-8')
    if shutil.which('timeout') and shutil.which('cat'):
        for attempt in range(1, _CLOUD_READ_ATTEMPTS + 1):
            result = subprocess.run(
                ['timeout', f'{timeout_seconds}s', 'cat', str(path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if result.returncode == 0 or attempt == _CLOUD_READ_ATTEMPTS:
                break
            time.sleep(0.5)
        if result.returncode == 0:
            return result.stdout.decode('utf-8')
        if result.returncode == 124:
            raise RuntimeError(
                f"Timed out reading {path} after {_CLOUD_READ_ATTEMPTS} attempts "
                f"of {timeout_seconds}s")
        message = result.stderr.decode('utf-8', errors='replace').strip()
        if result.returncode == 1 and 'No such file' in message:
            raise FileNotFoundError(path)
        raise RuntimeError(f"Failed reading {path}: {message or result.returncode}")
    if not hasattr(signal, 'SIGALRM'):
        return path.read_text(encoding='utf-8')

    def _timeout(_signum, _frame):
        raise TimeoutError

    old_handler = signal.signal(signal.SIGALRM, _timeout)
    signal.setitimer(signal.ITIMER_REAL, timeout_seconds)
    try:
        return path.read_text(encoding='utf-8')
    except TimeoutError as exc:
        raise RuntimeError(f"Timed out reading {path} after {timeout_seconds}s") from exc
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)


def atomic_write_json(path: Path, data: Any, **json_kwargs) -> None:
    """Write JSON through the same verified text path used by prompt outputs."""
    atomic_write_text(path, json.dumps(data, **json_kwargs))


def _matches_expected_text(path: Path, text: str) -> bool:
    try:
        return read_text_checked(path) == text
    except (OSError, RuntimeError):
        return False


def _write_text_direct(path: Path, text: str) -> None:
    """Direct-write fallback for mounts where replace can silently misbehave."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        f.write(text)
        f.flush()
        _fsync_if_safe(f, path)
    if not _matches_expected_text(path, text):
        raise RuntimeError(f"Write verification failed for {path}")


def atomic_write_text(path: Path, text: str) -> None:
    """Write UTF-8 text atomically, then verify and fall back when needed.

    Some FUSE/cloud mounts can report a successful replace while leaving a stale
    or empty destination. Verification keeps final prompt files from silently
    becoming zero-byte artifacts.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f'.{path.name}.', suffix='.tmp', dir=str(path.parent)
    )
    tmp = Path(tmp_name)
    atomic_error: Exception | None = None
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(text)
            f.flush()
            _fsync_if_safe(f, path)
        os.replace(tmp, path)
        if _matches_expected_text(path, text):
            return
        atomic_error = RuntimeError(f"Atomic write verification failed for {path}")
    except Exception:
        atomic_error = sys.exc_info()[1]
    finally:
        tmp.unlink(missing_ok=True)

    try:
        _write_text_direct(path, text)
    except Exception as direct_error:
        if atomic_error is not None:
            raise RuntimeError(
                f"Failed to write {path} via atomic and direct fallback"
            ) from direct_error
        raise


@contextmanager
def exclusive_file_lock(path: Path, *, timeout_seconds: float = 10.0):
    """Serialize a short cross-process read-modify-write operation."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_seconds
    lock_file = path.open('a+b')
    acquired = False
    while not acquired:
        try:
            if os.name == 'nt':
                import msvcrt
                if path.stat().st_size == 0:
                    lock_file.write(b'0')
                    lock_file.flush()
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except (BlockingIOError, OSError):
            if time.monotonic() >= deadline:
                lock_file.close()
                raise RuntimeError(f"Timed out waiting for lock: {path}")
            time.sleep(0.05)
    try:
        yield
    finally:
        try:
            if os.name == 'nt':
                import msvcrt
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        finally:
            lock_file.close()
