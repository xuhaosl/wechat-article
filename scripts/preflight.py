#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preflight.py — 公众号交付前统一预检

一条命令跑完四项，把同居 scripts/ 的几个闸门串起来：

  ① 排版自检   layout-check.py
  ② 文件规范   命名是否合规
  ③ 内容安检   content-check.py
  ④ 封面       是否已生成

为什么要有这个脚本：闸门各自都很硬，参数还不一样。跨会话时最容易漏掉其中一条，
而漏掉哪一条都是带病发布。

**md 的定位（2026-10-21 用户拍板）**：`.md` 是写稿时的过程材料，不是交付物。
唯一真相源是 `.html`。html 生成后 md 就该删掉，不留在产物目录里，也不对账。

退出码：0 全通过 · 1 有警告（可发但该看一眼）· 2 有硬失败（不能发）

用法：
  python preflight.py "$WECHAT_HOME/output/Hermes/28_2026-10-19_Hermes_goal持续目标.html"
  python preflight.py <html> --no-cover        # 还没做封面时

路径约定：WECHAT_HOME 默认 /opt/data/wechat，三个闸门脚本与本文件同居 scripts/。
"""

import argparse
import json
import os
import re
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

WECHAT_HOME = os.environ.get("WECHAT_HOME", "/opt/data/wechat")
HERE = os.path.dirname(os.path.abspath(__file__))

LAYOUT = os.path.join(HERE, "layout-check.py")
CONTENT = os.path.join(HERE, "content-check.py")

COVERS = os.path.join(WECHAT_HOME, "output", "covers")

NAME_RE = re.compile(r"^(?P<nn>\d{2})_(?P<date>\d{4}-\d{2}-\d{2})_(?P<title>.+)\.html$", re.I)


def run(script, args):
    """跑一个闸门脚本，返回 (退出码, 输出)。脚本不存在算硬失败。"""
    if not os.path.isfile(script):
        return 2, f"[缺失] 找不到脚本：{script}"
    try:
        p = subprocess.run(
            [sys.executable, script] + args,
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except OSError as e:
        return 2, f"[无法执行] {e}"
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def tail(text, n=14):
    lines = [l for l in text.strip().split("\n") if l.strip()]
    return "\n".join("    " + l for l in lines[-n:])


def check_layout(html):
    code, out = run(LAYOUT, [html])
    # layout-check: 0 全过 / 1 仅警告 / 2 有硬错误
    return code, out


def check_content(html, legacy=False):
    """content-check 走 --json：除了退出码，还要拿到句式命中的明细。

    以前用 --quiet，只回一行汇总，对偶拆分 / 不是 A 而是 B 这些全被吞掉——
    规则写了、脚本能抓，但预检不显示，等于没拦。

    按级别分开返回：第 23 条②／第 50 条是「一处都不许留」（phrase），
    第 45 条含糊指代用户定的是中危（hint），两者不能同档——
    混在一起会把「另一种做法是先备份」这种正常句子也拦成 ❌。
    返回 (code, out, 硬句式, 解析是否成功, 中危提示)，解析失败必须能被看见。
    """
    code, out = run(CONTENT, [html, "--json"] + (["--legacy"] if legacy else []))
    phrase, hint, parsed = [], [], False
    if code < 2:
        data = {}
        try:
            data = json.loads(out)
            parsed = True
        except ValueError:
            # stderr 混进 stdout 时退一步：截第一个 { 到最后一个 } 再试一次
            a, b = out.find("{"), out.rfind("}")
            if 0 <= a < b:
                try:
                    data = json.loads(out[a:b + 1])
                    parsed = True
                except ValueError:
                    data = {}
        for v in (data.get("vague") or []):
            why = v[2] if len(v) > 2 else ""
            if len(v) > 4:
                # 有级别就只认级别。再加关键词兜底会让 --legacy 失效：
                # soft 的「对偶拆分」会被关键词捞回 phrase，旧稿模式照样判必须改。
                (phrase if v[4] == "hard" else hint).append(v)
            elif "对偶" in why or "否定绕弯" in why or "前者/后者" in why:
                # 老结构（4 元组）没有 level，只能按关键词兜底
                phrase.append(v)
    return code, out, phrase, parsed, hint


def check_naming(html):
    """文件名规范：NN_YYYY-MM-DD_标题.html。md 不在判定范围内。"""
    bn = os.path.basename(html)
    m = NAME_RE.match(bn)
    notes = []
    level = 0
    if not m:
        notes.append(f"文件名不合规范（应 NN_YYYY-MM-DD_标题.html）：{bn}")
        level = 1
    return level, notes, (m.group("nn") if m else None)


def check_cover(html, nn):
    """封面放 output/covers/：在系列子目录里用「系列名_NN_主题.png」，直接放 output/ 下用「NN_主题.png」。"""
    if not os.path.isdir(COVERS):
        return 1, ["covers 目录不存在"]
    parent = os.path.dirname(os.path.abspath(html))
    output_root = os.path.abspath(os.path.join(WECHAT_HOME, "output"))
    series = "" if parent == output_root else os.path.basename(parent)
    if series:
        want = re.compile(r"^%s_%s(_|\.|$)" % (re.escape(series), nn)) if nn else None
    else:
        want = re.compile(r"^%s(_|\.|$)" % nn) if nn else None
    hits = []
    for f in os.listdir(COVERS):
        if not f.lower().endswith((".png", ".jpg", ".jpeg")):
            continue
        if want and not want.match(f):
            continue
        hits.append(f)
    if not hits:
        pat = ("%s_%s_*.png" % (series, nn or "NN")) if series else ("%s_*.png" % (nn or "NN"))
        return 1, ["没找到 %s 封面（按 SKILL.md 的 Step 11 做，调 agnes 出底图后 crop_cover.py 裁切）" % pat]
    return 0, ["封面已存在：%s" % h for h in hits[:3]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--no-cover", action="store_true", help="还没做封面，跳过封面检查")
    ap.add_argument("--legacy", action="store_true",
                    help="旧稿重推：句式降为提示，只查排版与结构（新写的稿别加）")
    args = ap.parse_args()

    html = args.html
    if not os.path.isfile(html):
        print(f"[错误] 文件不存在：{html}")
        return 2

    print("=" * 70)
    print("交付前预检 · preflight")
    print(f"  文件 {os.path.basename(html)}")
    print("=" * 70)

    severe = 0
    warn = 0
    style_hits = 0   # 第 23 条②／第 50 条句式命中：必须改，不适用「说明一下为什么不修」
    rows = []   # (环节, 状态标记, 说明)

    # ① 排版
    lc, lout = check_layout(html)
    if lc == 0:
        rows.append(("排版自检", "✅", "硬错误 0 / 警告 0"))
    elif lc == 1:
        rows.append(("排版自检", "⚠️", "有警告，需看一眼"))
        warn += 1
    else:
        rows.append(("排版自检", "❌", "有硬错误，必须修"))
        severe += 1
    if lc != 0:
        print("\n── 排版自检明细 ──")
        print(tail(lout))

    # ② 文件名
    nlevel, nnotes, nn = check_naming(html)
    if nlevel:
        rows.append(("文件规范", "⚠️", nnotes[0]))
        warn += 1
    else:
        rows.append(("文件规范", "✅", "命名合规（NN_日期_标题.html）"))

    # ③ 内容安检
    cc, cout, phrase, parsed, hint = check_content(html, args.legacy)
    if cc == 0:
        if not parsed:
            rows.append(("内容安检", "⚠️", "结果解析不了，句式没查成——手工跑 content-check.py"))
            warn += 1
        elif phrase:
            sample = "、".join(sorted(set(p[1] for p in phrase))[:3])
            rows.append(("内容安检", "❌", f"句式命中 {len(phrase)} 处（第 23／50 条）：{sample}"))
            style_hits = len(phrase)
            warn += 1
            print("\n── 句式明细（对偶拆分 / 不是 A 而是 B）──")
            for p in phrase[:6]:
                print(f"    第{p[0]}块「{p[1]}」 {p[2]}")
                if len(p) > 3 and p[3]:
                    print(f"      …{p[3]}…")
            if len(phrase) > 6:
                print(f"    ……另有 {len(phrase) - 6} 处，跑 content-check.py 看全量")
        else:
            rows.append(("内容安检", "✅", "脚本侧无高危"))
        if hint:
            sample = "、".join(sorted(set(p[1] for p in hint))[:3])
            rows.append(("中危提示", "⚠️", f"{len(hint)} 处（第 45／50 条边界）：{sample}"))
            warn += 1
            print("\n── 中危提示（第 45 条指代 / 疑似劈两半：看语境，不是硬拦）──")
            for p in hint[:4]:
                print(f"    第{p[0]}块「{p[1]}」 {p[2]}")
    elif cc == 1:
        rows.append(("内容安检", "❌", "有高危，先改再推"))
        severe += 1
        print("\n── 安检明细（高危）──")
        try:
            data = json.loads(cout)
        except ValueError:
            data = {}
        shown = 0
        for key in ("high", "privacy", "induce", "placeholders", "html"):
            for it in (data.get(key) or []):
                if shown >= 8:
                    break
                print(f"    {it[2]}｜{it[1]}")
                shown += 1
        if not shown:
            print(tail(cout, 8))
    else:
        rows.append(("内容安检", "❌", "脚本执行失败"))
        severe += 1

    # ④ 封面
    if args.no_cover:
        rows.append(("封面", "➖", "已跳过（--no-cover）"))
    else:
        vlevel, vnotes = check_cover(html, nn)
        if vlevel == 0:
            rows.append(("封面", "✅", vnotes[0]))
        else:
            rows.append(("封面", "⚠️", vnotes[0]))
            warn += 1

    print("\n" + "-" * 70)
    # 中文按两格算，否则「内容安检」和「文件规范」后面错位
    import unicodedata
    _w = lambda s: sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)
    width = max(_w(n) for n, _, _ in rows)
    for name, mark, msg in rows:
        print("  %s %s %s" % (mark, name + " " * (width - _w(name)), msg))
    print("-" * 70)
    if severe:
        print(f"❌ 不能发：{severe} 项硬失败，{warn} 项警告")
    elif style_hits:
        # 第 23 条②／第 50 条：句式命中不是「看一眼」级别。2026-10-22 用户定「必须改，不当警告」。
        # 退出码仍给 1（不阻断已发布旧稿的重推），但结论必须说清「改完再发」。
        print(f"❌ 句式命中 {style_hits} 处，改完再发（第 23 条②／第 50 条）"
              + (f"｜另有 {warn - 1} 项普通警告" if warn > 1 else ""))
    elif warn:
        print(f"⚠️ 可发但先看一眼：{warn} 项警告")
    else:
        print("✅ 全通过，可以交付")
    print()
    print("注：机器能判的只到这里。事实真假、数据出处、语气像不像人，")
    print("    还要人过一遍——预检通过不等于稿子能发。")
    return 2 if severe else (1 if warn else 0)


if __name__ == "__main__":
    sys.exit(main())
