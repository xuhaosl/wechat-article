#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fact-diff.py —— 去 AI 味前后的「事实漂移」比对

用途：④ 去 AI 味这一步直接改正文，改完没人查事实还在不在。
本脚本抽出去 AI 味之前的全部可核验事实项（数字、版本号、命令、界面元素、英文专名），
改完逐条搜一遍：消失了是删过界，多出来是编了新事实。

用法：
    # 两个文件直接比
    fact-diff.py <去味前.html> <去味后.html>

    # 单文件工作流：先存基线，改完再比
    fact-diff.py --snapshot <文章.html>      # 生成 <文章.html>.facts.json
    fact-diff.py --check    <文章.html>      # 与基线比

退出码：
    0  没发现事实消失或新增
    1  有消失或新增，看一眼（不是一定错，删掉的可能是废话里的数字）
"""

import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------------------------------------------------------------- 抽取

RE_TAG = re.compile(r"<[^>]+>")
RE_SCRIPT = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S)
RE_CODE = re.compile(r"`([^`]+)`")
RE_CODE_TAG = re.compile(r"<code[^>]*>(.*?)</code>", re.S)
RE_PRE = re.compile(r"<pre[^>]*>(.*?)</pre>", re.S)
RE_QUOTE = re.compile(r"「([^」]{2,30})」")

# 版本号：带 v 前缀，或三段以上。两段裸数字太容易是小数，不当版本号
RE_VERSION = re.compile(r"\bv\d+\.\d+(?:\.\d+)*\b|\b\d+\.\d+\.\d+(?:\.\d+)*\b", re.I)
RE_ENGLISH = re.compile(r"\b[A-Za-z][A-Za-z0-9_\-/().]{1,30}\b")
# 带单位或小数的数字才当事实，裸的小整数多是序号
RE_NUM_UNIT = re.compile(
    r"\d[\d,\.]*\s*(?:%|％|GB|MB|KB|TB|ms|秒|分钟|小时|天|周|个月|年|"
    r"块钱|元|篇|条|个|次|人|轮|倍|台|核|层|张|份|页|字)",
    re.I,
)
RE_NUM_FLOAT = re.compile(
    r"(?<![A-Za-z0-9.])\d{1,3}(?:,\d{3})+(?:\.\d+)?(?![0-9])"
    r"|(?<![A-Za-z0-9.])\d+\.\d+(?![0-9.])"
)

# 英文停用词 / 常见非事实词
STOP_EN = set(
    """a an the of to in on at is are was were be been by for and or not no
    if then else this that these those it its as from with you your we our
    i me my he she they them his her their but so can will just""".split()
)


def to_text(raw: str) -> str:
    """HTML / Markdown 统一成纯文本，保留 code 与 pre 的内容。"""
    t = raw
    if "<" in t and ">" in t:
        t = RE_SCRIPT.sub(" ", t)
        t = RE_PRE.sub(lambda m: "\n" + m.group(1) + "\n", t)
        t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
        t = re.sub(r"</(p|div|section|li|h\d)>", "\n", t, flags=re.I)
        t = RE_TAG.sub(" ", t)
    # HTML 实体粗解
    for a, b in [("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"),
                 ("&gt;", ">"), ("&quot;", '"'), ("&#39;", "'")]:
        t = t.replace(a, b)
    return t


def extract(raw: str) -> dict:
    """返回 {类别: [项, ...]}，项保持原样，便于人读。"""
    text = to_text(raw)
    buckets = {"版本号": [], "命令与代码": [], "数字": [], "英文专名": [], "界面元素": []}

    for m in RE_CODE.finditer(raw):
        s = m.group(1).strip()
        if 1 < len(s) <= 60:
            buckets["命令与代码"].append(s)
    for m in RE_CODE_TAG.finditer(raw):
        s = to_text(m.group(1)).strip()
        if 1 < len(s) <= 60:
            buckets["命令与代码"].append(s)
    for m in RE_PRE.finditer(raw):
        for line in to_text(m.group(1)).splitlines():
            s = line.strip()
            if 2 < len(s) <= 80:
                buckets["命令与代码"].append(s)

    for m in RE_VERSION.finditer(text):
        buckets["版本号"].append(m.group(0))

    for m in RE_NUM_UNIT.finditer(text):
        buckets["数字"].append(re.sub(r"\s+", "", m.group(0)))
    for m in RE_NUM_FLOAT.finditer(text):
        buckets["数字"].append(m.group(0))

    for m in RE_ENGLISH.finditer(text):
        s = m.group(0)
        if s.lower() in STOP_EN or len(s) < 2:
            continue
        buckets["英文专名"].append(s)

    for m in RE_QUOTE.finditer(text):
        buckets["界面元素"].append(m.group(1))

    # 去重保顺序
    for k in buckets:
        seen, out = set(), []
        for x in buckets[k]:
            key = x.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(x)
        buckets[k] = out
    return buckets


# ---------------------------------------------------------------- 比对


def _squash(s: str) -> str:
    return re.sub(r"\s+", "", s).lower()


def count_occurrences(haystack: str, needle: str) -> int:
    """去空白比对：原文「20 轮」与抽取的「20轮」视为同一件事，不误报。"""
    if not needle:
        return 0
    return _squash(haystack).count(_squash(needle))


def _drop_fragments(items: list) -> list:
    """v2.9.1 顺带抽出 9.1、3.8 倍顺带抽出 3.8 —— 同一个事实别报三遍。"""
    out = []
    for it in sorted(items, key=len, reverse=True):
        if any(_squash(it) in _squash(o) for o in out):
            continue
        out.append(it)
    return out


def diff(before: dict, after_raw: str) -> list:
    after_text = to_text(after_raw)
    rows = []
    for cat, items in before.items():
        for it in items:
            n = count_occurrences(after_text, it)
            if n == 0:
                rows.append({"state": "消失", "cat": cat, "item": it})
    # 新增：改后出现、改前没有的具体事实
    all_before = set()
    for items in before.values():
        all_before |= {_squash(x) for x in items}
    after_buckets = extract(after_raw)
    for cat, items in after_buckets.items():
        if cat not in ("版本号", "数字", "命令与代码"):
            continue
        fresh = [it for it in items if _squash(it) not in all_before]
        for it in _drop_fragments(fresh):
            rows.append({"state": "新增", "cat": cat, "item": it})
    return rows


def baseline_path(path: str) -> str:
    """基线放在同目录、点前缀，扫目录时不会混进文章清单。"""
    d, b = os.path.split(os.path.abspath(path))
    return os.path.join(d, "." + b + ".facts.json")


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 0

    if argv[1] == "--snapshot":
        if len(argv) < 3:
            print("用法: fact-diff.py --snapshot <文章.html>")
            return 2
        path = argv[2]
        raw = open(path, encoding="utf-8").read()
        data = extract(raw)
        out = baseline_path(path)
        json.dump(data, open(out, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        n = sum(len(v) for v in data.values())
        print(f"基线已存：{out}（{n} 个事实项）")
        for k, v in data.items():
            if v:
                print(f"  {k} {len(v)} 项")
        return 0

    if argv[1] == "--check" or len(argv) == 2:
        path = argv[2] if len(argv) > 2 else argv[1]
        base = baseline_path(path)
        if not os.path.exists(base):
            print(f"没有基线：{base}\n先跑 --snapshot")
            return 1
        before = json.load(open(base, encoding="utf-8"))
        after_raw = open(path, encoding="utf-8").read()
    else:
        before = extract(open(argv[1], encoding="utf-8").read())
        path = argv[2]
        after_raw = open(path, encoding="utf-8").read()

    rows = diff(before, after_raw)
    gone = [r for r in rows if r["state"] == "消失"]
    new = [r for r in rows if r["state"] == "新增"]

    print(f"事实比对 · {os.path.basename(path)}")
    print("=" * 68)
    gap = [r for r in gone if r["cat"] in ("版本号", "命令与代码")]
    gap_keys = {_squash(r["item"]) for r in gap}
    # 命令串已经整条报过的，就不再把它拆成 hermes / gateway / run 报三遍
    rest = [
        r for r in gone
        if r not in gap and not any(_squash(r["item"]) in g for g in gap_keys)
    ]
    keep, seen = [], set()
    for r in sorted(rest, key=lambda x: -len(x["item"])):
        k = _squash(r["item"])
        if k in seen:
            continue
        seen.add(k)
        keep.append(r)
    other_gone = sorted(keep, key=lambda x: (x["cat"], -len(x["item"])))

    if gap:
        print(f"!! 命令/版本号消失 {len(gap)} 项 —— 这类删了基本就是改坏，逐条看")
        for r in gap:
            print(f"   [{r['cat']}] {r['item']}")
    if other_gone:
        print(f"?  其他事实项消失 {len(other_gone)} 项 —— 可能是连同废话一起删掉了")
        for r in other_gone[:40]:
            print(f"   [{r['cat']}] {r['item']}")
        if len(other_gone) > 40:
            print(f"   ……还有 {len(other_gone) - 40} 项")
    if new:
        print(f"!! 新出现的事实 {len(new)} 项 —— 去 AI 味只该做减法，多出来的是编的")
        for r in new[:40]:
            print(f"   [{r['cat']}] {r['item']}")
        if len(new) > 40:
            print(f"   ……还有 {len(new) - 40} 项")
    if not gone and not new:
        print("  事实项全部还在，没有新增")

    print("=" * 68)
    if gap or new:
        print(f"结论: 硬要看 {len(gap) + len(new)} 项 ⚠️")
        return 1
    if other_gone:
        print(f"结论: 提示 {len(other_gone)} 项（对照上文看一眼即可）")
        return 1
    print("结论: 无漂移 ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
