#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""在已裁好的公众号封面上叠加**真实品牌图标**（Pillow 精确叠加，绝不让生图模型画 LOGO）。

用法：
  python add_brand_icons.py <封面.png> <输出.png> \
      --icon <图标.png> <cx> <cy> <size> <style> [--icon ...]

参数：
  cx cy     图标中心坐标（相对封面左上角，像素）
  size      图标显示边长
  style     叠加方式，默认 tile：
              tile    白色圆角方块 App 块，图标等比内嵌居中（默认就用这个）
              ring    白色圆环垫底 + 图标居中（图标本身是圆形徽标时才用）
  可选：--pad-ratio 0.12（tile/ring 内嵌留白比例）、--radius-ratio 0.225（圆角半径比）、
        --shadow-alpha 90、--shadow-blur 9、--shadow-offset 5
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFilter


def white_tile(size: int, radius: int, color=(255, 255, 255, 255)) -> Image.Image:
    """透明背景的白色圆角方块"""
    S = size * 4
    m = Image.new('L', (S, S), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, S - 1, S - 1), radius=radius * 4, fill=255)
    m = m.resize((size, size), Image.LANCZOS)
    t = Image.new('RGBA', (size, size), color)
    t.putalpha(m)
    return t


def white_ring(size: int, color=(255, 255, 255, 255)) -> Image.Image:
    """透明背景的白色圆盘（用于圆形徽标垫底）"""
    S = size * 4
    m = Image.new('L', (S, S), 0)
    ImageDraw.Draw(m).ellipse((0, 0, S - 1, S - 1), fill=255)
    m = m.resize((size, size), Image.LANCZOS)
    t = Image.new('RGBA', (size, size), color)
    t.putalpha(m)
    return t


def contain(icon: Image.Image, box: int) -> Image.Image:
    """等比缩放到最长边等于 box"""
    w, h = icon.size
    k = box / max(w, h)
    return icon.resize((max(1, round(w * k)), max(1, round(h * k))), Image.LANCZOS)


def add_shadow(icon: Image.Image, blur=9, offset=5, alpha=90, color=(120, 52, 12)) -> Image.Image:
    pad = blur * 3
    w, h = icon.size
    canvas = Image.new('RGBA', (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    a = icon.split()[3]
    sh = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    sh.paste(Image.new('RGBA', icon.size, color + (alpha,)), (pad, pad + offset), a)
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    canvas.alpha_composite(icon, (pad, pad))
    return canvas


def build(path, size, style, pad_ratio, radius_ratio):
    src = Image.open(path).convert('RGBA')
    pad = round(size * pad_ratio)
    if style == 'ring':
        base = white_ring(size)
    elif style == 'tile':
        base = white_tile(size, round(size * radius_ratio))
    else:
        raise ValueError('未知 style：%s' % style)
    inner = contain(src, size - pad * 2)
    base.alpha_composite(inner, ((size - inner.size[0]) // 2,
                                 (size - inner.size[1]) // 2))
    return base


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('cover')
    ap.add_argument('out')
    ap.add_argument('--icon', nargs=5, action='append', metavar=('IMG', 'CX', 'CY', 'SIZE', 'STYLE'),
                    required=True)
    ap.add_argument('--pad-ratio', type=float, default=0.12)
    ap.add_argument('--radius-ratio', type=float, default=0.225)
    ap.add_argument('--shadow-alpha', type=int, default=90)
    ap.add_argument('--shadow-blur', type=int, default=9)
    ap.add_argument('--shadow-offset', type=int, default=5)
    args = ap.parse_args()

    base = Image.open(args.cover).convert('RGBA')
    for img, cx, cy, size, style in args.icon:
        if style not in ('tile', 'ring'):
            print('[错误] style 只认 tile / ring，收到：%s' % style)
            return 2
        icon = build(img, int(size), style, args.pad_ratio, args.radius_ratio)
        icon = add_shadow(icon, blur=args.shadow_blur, offset=args.shadow_offset,
                          alpha=args.shadow_alpha)
        base.alpha_composite(icon, (int(float(cx) - icon.size[0] / 2),
                                    int(float(cy) - icon.size[1] / 2)))
        print('  + %s  center=(%s,%s) size=%s style=%s' % (img, cx, cy, size, style))
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    base.convert('RGB').save(args.out)
    print('saved', args.out, base.size)
    return 0


if __name__ == '__main__':
    sys.exit(main())
