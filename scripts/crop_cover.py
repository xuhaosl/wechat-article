#!/usr/bin/env python3
"""
公众号封面裁剪脚本：把 Agnes 生成的宽幅底图居中裁剪为 2.35:1 并缩放。
零依赖（仅 Pillow，已装在 venv）。

用法：
  python crop_cover.py <输入图.png> <输出图.png> [--ratio 2.35] [--width 900] [--height 383]

默认：比例 2.35:1，输出 900x383（公众号封面规范）。
居中裁剪：上下裁掉多余部分，保留画面中央主体。
"""

import argparse
import os
import sys
from PIL import Image


def crop_to_ratio(img: Image.Image, ratio: float) -> Image.Image:
    """按目标宽高比居中裁剪（裁掉上下多余部分）。"""
    w, h = img.size
    target_h = int(w / ratio)
    if target_h >= h:
        # 原图已经比目标比例更"窄高"，改为按高度裁宽度
        target_w = int(h * ratio)
        left = (w - target_w) // 2
        return img.crop((left, 0, left + target_w, h))
    top = (h - target_h) // 2
    return img.crop((0, top, w, top + target_h))


def main():
    parser = argparse.ArgumentParser(description="公众号封面裁剪工具（2.35:1 居中裁剪 + 缩放）")
    parser.add_argument("input", help="输入图片路径（Agnes 生成的宽幅底图）")
    parser.add_argument("output", help="输出图片路径（裁剪后保存位置）")
    parser.add_argument("--ratio", type=float, default=2.35, help="目标宽高比（默认 2.35）")
    parser.add_argument("--width", type=int, default=900, help="输出宽度（默认 900）")
    parser.add_argument("--height", type=int, default=383, help="输出高度（默认 383）")
    args = parser.parse_args()

    try:
        img = Image.open(args.input).convert("RGB")
    except Exception as e:
        print(f"错误：无法打开图片 {args.input}: {e}", file=sys.stderr)
        sys.exit(1)

    # 居中裁剪到目标比例
    img = crop_to_ratio(img, args.ratio)
    # 缩放到目标尺寸
    img = img.resize((args.width, args.height), Image.LANCZOS)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    img.save(args.output)

    print(f"✅ 封面已裁剪：{args.output}（{args.width}x{args.height}，比例 {args.ratio}:1）")


if __name__ == "__main__":
    main()
