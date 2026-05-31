"""Resize an image to 16:9 Full HD (1920x1080) using Lanczos or Real-ESRGAN.

Usage:
    python3 resize_16_9.py --src <file> --dest <file> --method lanczos|esrgan

Lanczos path: PIL center-crop + LANCZOS resize (fast, 0 extra deps).
ESRGAN path:  realesrgan-ncnn-vulkan x4 upscale → crop → resize (sharper, needs binary).
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image


TARGET_W, TARGET_H = 1920, 1080
TARGET_ASPECT = TARGET_W / TARGET_H  # 16/9 ≈ 1.7778
BLACK_THRESHOLD = 15  # avg pixel value below this = letterbox bar


def detect_letterbox(img):
    """Return (top, bottom) rows that are near-black letterbox bars."""
    w, h = img.size
    pixels = img.load()
    sample_cols = [w // 4, w // 2, 3 * w // 4]

    def row_is_black(y):
        total = 0
        for x in sample_cols:
            r, g, b = pixels[x, y][:3]
            total += (r + g + b) / 3
        return (total / len(sample_cols)) < BLACK_THRESHOLD

    top = 0
    for y in range(h // 3):
        if row_is_black(y):
            top = y + 1
        else:
            break

    bottom = h
    for y in range(h - 1, h - h // 3, -1):
        if row_is_black(y):
            bottom = y
        else:
            break

    return top, bottom


def crop_to_16_9(img):
    """Center-crop image to 16:9 aspect ratio after removing letterbox bars."""
    w, h = img.size

    # Remove letterbox black bars
    top, bottom = detect_letterbox(img)
    if top > 0 or bottom < h:
        img = img.crop((0, top, w, bottom))
        w, h = img.size

    # Center-crop to 16:9
    current_aspect = w / h
    if current_aspect < TARGET_ASPECT:
        new_h = int(w / TARGET_ASPECT)
        crop_top = (h - new_h) // 2
        img = img.crop((0, crop_top, w, crop_top + new_h))
    elif current_aspect > TARGET_ASPECT:
        new_w = int(h * TARGET_ASPECT)
        crop_left = (w - new_w) // 2
        img = img.crop((crop_left, 0, crop_left + new_w, h))

    return img


def resize_lanczos(src, dest):
    """Crop + resize using PIL Lanczos resampling."""
    with Image.open(src) as img:
        img = img.convert("RGB")
        img = crop_to_16_9(img)
        resampling = getattr(Image, "Resampling", Image).LANCZOS
        img = img.resize((TARGET_W, TARGET_H), resampling)
        img.save(dest)


def resize_esrgan(src, dest):
    """Upscale with Real-ESRGAN, then crop + resize to 1920x1080."""
    binary = shutil.which("realesrgan-ncnn-vulkan")
    if not binary:
        print(
            "⚠ realesrgan-ncnn-vulkan not found in PATH. Falling back to Lanczos.",
            file=sys.stderr,
        )
        resize_lanczos(src, dest)
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        upscaled = os.path.join(tmpdir, "upscaled.png")
        cmd = [
            binary,
            "-i", src,
            "-o", upscaled,
            "-s", "4",
            "-n", "realesrgan-x4plus",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 or not os.path.exists(upscaled):
            print(
                f"⚠ Real-ESRGAN failed (rc={result.returncode}). Falling back to Lanczos.",
                file=sys.stderr,
            )
            if result.stderr:
                print(f"  stderr: {result.stderr.strip()}", file=sys.stderr)
            resize_lanczos(src, dest)
            return

        with Image.open(upscaled) as img:
            img = img.convert("RGB")
            img = crop_to_16_9(img)
            resampling = getattr(Image, "Resampling", Image).LANCZOS
            img = img.resize((TARGET_W, TARGET_H), resampling)
            img.save(dest)


def main():
    parser = argparse.ArgumentParser(
        description="Resize image to 16:9 Full HD (1920x1080)"
    )
    parser.add_argument("--src", required=True, help="Source image path")
    parser.add_argument("--dest", required=True, help="Destination image path")
    parser.add_argument(
        "--method",
        choices=["lanczos", "esrgan"],
        default="lanczos",
        help="Upscaling method (default: lanczos)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.src):
        print(f"Error: source file not found: {args.src}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(os.path.abspath(args.dest)), exist_ok=True)

    if args.method == "esrgan":
        resize_esrgan(args.src, args.dest)
    else:
        resize_lanczos(args.src, args.dest)

    print(f"✅ {os.path.basename(args.dest)} → {TARGET_W}x{TARGET_H} ({args.method})")


if __name__ == "__main__":
    main()
