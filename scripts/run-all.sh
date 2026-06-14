#!/usr/bin/env bash
#
# run-all.sh — batch-drive /visual-prompt across MANY series at once.
#
# Each immediate subfolder of <parent> that contains chapter .txt files is one
# series; run-folder.sh handles it (its own locked style + isolated bible). A
# failing series is reported but does not block the others — re-running resumes.
#
# Usage:   run-all.sh <parent-folder>
# Env:     same as run-folder.sh (VP_MODEL, VP_MUSIC, VP_DRYRUN)

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

[ $# -eq 1 ] || { echo "Usage: run-all.sh <parent-folder>" >&2; exit 1; }
PARENT="${1%/}"
[ -d "$PARENT" ] || { echo "❌ Không phải thư mục: $PARENT" >&2; exit 1; }

mapfile -t DIRS < <(find "$PARENT" -mindepth 1 -maxdepth 1 -type d | sort)

failed=()
for d in "${DIRS[@]}"; do
  # only treat a subfolder as a series if it holds at least one chapter .txt
  if ! find "$d" -maxdepth 1 -type f -name '*.txt' \
        ! -name '*_qa.txt' ! -name '*_image_prompts.txt' \
        ! -name '*_video_prompts.txt' ! -name '*_music_prompts.txt' \
        | grep -q .; then
    echo "⏭  Bỏ qua (không có file truyện): $d"
    continue
  fi
  echo "================================================================"
  if bash "$HERE/run-folder.sh" "$d"; then
    :
  else
    echo "⚠ Bộ lỗi, tiếp tục bộ kế: $d" >&2
    failed+=("$d")
  fi
done

echo "================================================================"
if [ ${#failed[@]} -gt 0 ]; then
  echo "✖ ${#failed[@]} bộ chưa xong (chạy lại run-all.sh để resume):" >&2
  printf '   - %s\n' "${failed[@]}" >&2
  exit 1
fi
echo "✔ Tất cả các bộ đã hoàn tất."
