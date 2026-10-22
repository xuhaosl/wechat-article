#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公众号排版 · 章节清晰度 & 行文密度自检
2026-09-16 创建（用户指出「章节不够清晰、目录撤掉后更杂乱、行文冗长赘述」）

用法:
    python layout-check.py <文章.html> [--json]

检查项:
  A 章节结构   每章是否被 section 包住 / 标题形态是否统一
  B 标题层级   >=16px 且加粗的元素数必须等于章节数（卡片标题不许抢层级）
  C 正文边距   段落左右 margin 必须为 0
  D 行文密度   段落长度 / 口水词密度 / 净字数
  E 重复短语   同一层意思反复说（n-gram 重复）
  F 禁用样式   flex/gap、background-color、linear-gradient、<a href>、<table>、<ul>/<ol>/<li>
  G 页面干净度 浅色底种数 / 正文灰混用 / 满宽粗分隔线 / 卡片套卡片 / 全篇色值数
               （2026-09-16 新增，用户要「页面再干净一点」）
  H 导读卡     存在性 / 字数 / 首句泛论 / 首句禁代词起头
               （2026-10-09 反转：原「首句有无『你』」与「首句先立主体」冲突，用户否 OWUI 01 导语）
  I 手机显示   标题字符数 / 图注字数 / 并排双卡 / 标题区留白 / 伪清单串行
  J 标签配对    section/p/span/pre 开闭配对、<p> 嵌套、重复闭合
             （2026-09-20 新增，防「插段落把 </p> 挤歪」，全库 101 篇仅 1 篇真实命中）
（2026-09-17 新增，用户定：标题 ≤17 字符、图注 ≤15 字、禁并排双卡、并列项禁串行）

退出码: 0 通过 / 1 有警告 / 2 有硬错误
"""
import re
import sys
import json
import os
from collections import Counter

# ---------------- 阈值 ----------------
# ⚠️ 2026-09-24 20:55 用户纠正「字数不要设限」→ 段落长度 / 净字数 一律不设上限。
#    保留常量是为了「提示」而不是「卡人」：只在极端离谱时才 warning，永不报 error。
T_PARA_MAX = 99999       # 单段字数上限：不设限（原 80，已撤）
T_PARA_LONG = 80         # 超长段提示线（仅提示，不判错）
T_PARA_LONG_ALLOW = 3    # 超长段全篇允许个数
T_AVG_PARA = 45          # 平均段长提示线（原 35，放宽；仅提示）
T_FILLER_RATE = 0.25     # 口水词密度上限（每百字）—— 这条保留，它是「垫话」指标不是「长度」指标
T_WORDS_MIN, T_WORDS_MAX = 0, 999999    # 净字数区间：不设限（原 1500–2500，已撤）
T_TITLE_MAX = 17         # 标题字符数上限（中文字/标点/英文字母/数字各计 1）
T_TITLE_WIDTH = 15       # 标题显示宽度上限（中文/全角 1，英文/数字/半角 0.5）
T_CAP_MAX = 15           # 图注字符数上限（去掉 ▲ 和 emoji 后）
T_TITLE_GAP = 30         # 标题区 → 导读卡 的留白合计上限（px）
FILLERS = ["其实", "然后", "而且", "也就是说", "换句话说", "说白了", "本质上",
           "顺便", "同时", "你会发现", "值得注意的是", "值得一提",
           "这样一来", "反过来", "道理就这些", "说回正题",
           # 2026-09-24 用户「不要瞎编非读者的体会」新增
           "你会觉得", "你可能觉得", "别嫌", "不用担心", "放心", "很好用", "特别顺手"]

BANNED = [
    (r"display:\s*flex", "flex 布局（微信不兼容）"),
    (r"gap:\s*\d", "gap 属性（微信不兼容）"),
    (r"background-color:", "background-color（用 background）"),
    (r"linear-gradient", "linear-gradient（微信不支持）"),
    (r"<a\s+[^>]*href=", "<a href>（微信不支持）"),
    (r"<table", "<table>（改上下堆叠的单栏卡，禁并排双卡）"),
    (r"<ul|<ol|<li", "<ul>/<ol>/<li>（改 p 或 section）"),
]


# ---------------- 颜色工具（G 项用）----------------
def _rgb(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def luma(h):
    """相对明度 0~1。浅色底 > 0.92，实心主色 < 0.7"""
    r, g, b = _rgb(h)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def is_gray(h, tol=40):
    """灰阶判定：RGB 三通道最大差 ≤ tol。用于把「文字灰」和「主题色」分开"""
    r, g, b = _rgb(h)
    return max(r, g, b) - min(r, g, b) <= tol


def strip_noise(html):
    """去掉代码块/图片/属性，返回纯文本（保留段落分隔）"""
    h = html
    h = re.sub(r'<pre[^>]*>.*?</pre>', '\n@@PRE@@\n', h, flags=re.S)
    h = re.sub(r'<img[^>]*>', '\n@@IMG@@\n', h)
    h = re.sub(r'<script[^>]*>.*?</script>', '', h, flags=re.S)
    h = re.sub(r'<style[^>]*>.*?</style>', '', h, flags=re.S)
    h = re.sub(r'<!--.*?-->', '', h, flags=re.S)
    h = re.sub(r'<[^>]+>', '', h)
    h = h.replace('&nbsp;', ' ').replace('&amp;', '&')
    h = re.sub(r'&[a-zA-Z#0-9]+;', '', h)
    return h


def paras(html):
    """按 <p> 提段落（排除图注/注释/短装饰）"""
    out = []
    for m in re.finditer(r'<p\b([^>]*)>(.*?)</p>', html, re.S):
        attrs, body = m.group(1), m.group(2)
        if '@@IMG@@' in body or '<img' in body:
            continue
        t = strip_noise(body)
        t = re.sub(r'@@\w+@@', '', t)
        t = re.sub(r'\s+', '', t)
        if len(t) < 8:
            continue
        if 'color:#999' in attrs.replace(' ', '') or 'font-size:12.5px' in attrs.replace(' ', ''):
            continue  # 图注
        out.append(t)
    return out


def split_sents(t):
    return [s for s in re.split(r'[。！？!?；;]', t) if len(s) >= 4]


def main():
    if len(sys.argv) < 2:
        print("用法: python layout-check.py <文章.html> [--json]")
        return 2
    path = sys.argv[1]
    as_json = "--json" in sys.argv
    if not os.path.exists(path):
        print(f"[错误] 文件不存在: {path}")
        return 2

    html = open(path, encoding='utf-8').read()
    problems, warnings, ok = [], [], []

    # ---------- 定位"正文起点"（第一个章节标题处）----------
    # 标题区、导读、关键词标签、目录都在第一章之前，算 n-gram 时必须切掉，
    # 否则「标题在标题区重复」「目录列了章节名」会被误报成同义复述。
    body_start = 0
    m = re.search(r'<(\w+)\b[^>]*font-size:1[78]px[^>]*font-weight:(?:bold|700)[^>]*>', html)
    if not m:
        m = re.search(r'<h2\b[^>]*>', html)
    if m:
        body_start = m.start()

    # ---------- A 章节结构 ----------
    SYM = re.compile(r'^[\W_]*$')
    heads, dirty = [], []
    for m in re.finditer(r'<(\w+)\b([^>]*?)>', html):
        tag, attrs = m.group(1), m.group(2)
        if tag in ('h1',):
            continue
        a = attrs.replace(' ', '')
        fs = re.search(r'font-size:(\d+(?:\.\d+)?)px', a)
        if not fs:
            continue
        size = float(fs.group(1))
        if not (16 <= size <= 20) or not re.search(r'font-weight:(bold|700|600)', a):
            continue
        # 取该元素的文字，纯符号（●▲emoji）不算章节
        seg = html[m.end():m.end() + 400]
        txt = re.sub(r'<[^>]+>', '', seg.split('</')[0] if '</' in seg else seg)
        txt = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', txt)
        if len(txt) < 2:
            continue
        col = re.search(r'color:(#[0-9a-fA-F]{3,6})', a)
        colv = (col.group(1).lower() if col else '')
        GREY = {'#1a1a1a', '#000', '#000000', '#3d3d3d', '#333', '#333333',
                '#666', '#666666', '#888', '#888888', '#999', '#999999',
                '#bbb', '#bbbbbb', '#374151', '#1f2937'}
        if colv in GREY:
            # 文末「引导关注」区常有 16px 纯黑标题，不算伪章节（它在全文 90% 之后）
            if m.start() < len(html) * 0.9:
                dirty.append((txt[:20], size, colv))
        else:
            heads.append((tag, size, m.start()))

    n_chap = len(heads)
    if n_chap == 0:
        problems.append("[A] 找不到任何章节标题（16-20px 加粗且带主题色的元素数为 0）")
    else:
        dist = ", ".join(f"{t}×{sum(1 for x in heads if x[0] == t)}"
                         for t in sorted({x[0] for x in heads}))
        ok.append(f"[A] 章节数 {n_chap}，标题标签分布: {dist}")
        tags_used = {x[0] for x in heads}
        if len(tags_used) > 1:
            warnings.append(f"[A] 章节标题混用了多种标签 {sorted(tags_used)}，全篇应只用一种形态")
        sizes = {x[1] for x in heads}
        if len(sizes) > 1:
            warnings.append(f"[A] 章节标题字号不统一: {sorted(sizes)}")

    # 章容器：section 里包着标题
    n_sec = len(re.findall(r'<section[^>]*style="[^"]*margin:0\s+0\s+(2[6-9]|3\d)px', html))
    if n_chap and n_sec < n_chap:
        problems.append(f"[A] 只有 {n_sec} 个章节容器 section（应 ≥ {n_chap}）——"
                        f"每章要用 <section style=\"margin:0 0 30px\"> 包住，否则章与章之间没有块级边界")

    # ---------- B 层级打架 ----------
    if dirty:
        problems.append(f"[B] 发现 {len(dirty)} 处 16-20px 的纯黑/灰加粗「伪章节标题」"
                        f"（{', '.join(f'{t}({s}px)' for t, s, _ in dirty[:4])}）"
                        f"——会和章节标题抢层级，降到 14px 并改用主题色")

    # ---------- C 正文边距 ----------
    bad_margin = re.findall(r'<p style="margin:0 ([1-9]\d*px)', html)
    if bad_margin:
        problems.append(f"[C] 有 {len(bad_margin)} 个段落左右 margin 非 0（如 margin:0 {bad_margin[0]}…）"
                        f"——留白必须交给容器 padding，否则整篇比别的系列多缩进，一行少两个字")

    # ---------- D 行文密度 ----------
    ps = paras(html)
    if ps:
        total = sum(len(t) for t in ps)
        avg = total / len(ps)
        longs = [t for t in ps if len(t) > T_PARA_LONG]
        sents = []
        for t in ps:
            sents += split_sents(t)
        avg_sent = sum(len(s) for s in sents) / len(sents) if sents else 0
        fc = {w: sum(t.count(w) for t in ps) for w in FILLERS}
        fc = {k: v for k, v in fc.items() if v}
        ft = sum(fc.values())
        frate = ft / total * 100 if total else 0

        ok.append(f"[D] 段落 {len(ps)} 段 / 净字数 {total} / 平均段长 {avg:.1f} 字 / 平均句长 {avg_sent:.1f} 字")
        if avg > T_AVG_PARA:
            warnings.append(f"[D] 平均段长 {avg:.1f} 字 > {T_AVG_PARA}，段落偏胖（爆款实测 30 字左右）")
        if len(longs) > T_PARA_LONG_ALLOW:
            warnings.append(f"[D] >{T_PARA_LONG} 字的长段 {len(longs)} 个"
                            f"（仅提示，看一眼能不能拆，不用为它删内容）")
        if frate > T_FILLER_RATE:
            problems.append(f"[D] 口水词密度 {frate:.2f}% > {T_FILLER_RATE}%"
                            f"（爆款 0.16~0.25%）→ {fc}")
        else:
            ok.append(f"[D] 口水词密度 {frate:.2f}%（阈值 {T_FILLER_RATE}%）")
        # 净字数不判（2026-10-20 用户：不是硬性要求）。T_WORDS_MIN/MAX 留作占位，
        # 原来的两条 <MIN / >MAX 警告是死代码（0 / 999999 永不触发），已删。
    else:
        warnings.append("[D] 没提取到正文段落")

    # ---------- E 重复短语（同义复述代理指标）----------
    # 只在正文区(第一章之后)算，标题区/导读/目录都切掉，避免误报
    body = strip_noise(html[body_start:])
    body = re.sub(r'@@\w+@@', '', body)
    body = re.sub(r'[\s\W_]+', '', body)
    N = 9
    grams = {}
    for i in range(len(body) - N):
        g = body[i:i + N]
        if re.search(r'[0-9a-zA-Z]', g):
            continue          # 跳含英文/数字的
        grams[g] = grams.get(g, 0) + 1
    rep = sorted([(g, c) for g, c in grams.items() if c >= 2],
                 key=lambda x: (-x[1], -len(x[0])))
    # 合并被包含的短串
    merged = []
    for g, c in rep:
        if any(g in m[0] and m[1] >= c for m in merged):
            continue
        merged.append((g, c))
    if merged:
        top = merged[:8]
        warnings.append(f"[E] 正文有 {len(merged)} 处 9 字以上短语重复（同义复述嫌疑）："
                        + " / ".join(f"「{g}」×{c}" for g, c in top[:5]))
    else:
        ok.append("[E] 正文无 9 字以上短语重复")

    # E2 高频短短语（>=3 次）= 车轱辘话代理指标。
    # 注意：n-gram 只能抓字面重复；「换个说法又讲一遍」（如 Hermes 04 把
    # 「它一直开着」用 4 种说法讲 5 遍）机器抓不到，必须靠人工/AI 在写作阶段审。
    N2 = 6
    g2 = {}
    for i in range(len(body) - N2):
        s = body[i:i + N2]
        if re.search(r'[0-9a-zA-Z]', s):
            continue
        g2[s] = g2.get(s, 0) + 1
    hot = sorted([(s, c) for s, c in g2.items() if c >= 3],
                 key=lambda x: (-x[1], -len(x[0])))
    hotm = []
    for s, c in hot:
        if any(s in m[0] and m[1] >= c for m in hotm):
            continue
        hotm.append((s, c))
    if hotm:
        warnings.append(f"[E2] 有 {len(hotm)} 个 6 字短语在正文出现 ≥3 次（车轱辘话嫌疑）："
                        + " / ".join(f"「{s}」×{c}" for s, c in hotm[:6])
                        + " —— 同一层意思只该说一次，换个说法再说一遍也算重复")

    # ---------- F 禁用样式 ----------
    for pat, desc in BANNED:
        n = len(re.findall(pat, html))
        if n:
            problems.append(f"[F] 禁用样式命中 {desc} × {n}")

    # ---------- G 页面干净度（2026-09-16 新增）----------
    # 依据：爆款实测「有色背景种数」3~4 种，WB13/Hermes 是 5~6 种。
    # 底色是比字号、emoji 更重的视觉信号——一篇里三种浅底并存，读者说不清
    # 为什么这儿是蓝的、那儿是绿的，观感就是"花"。
    CODEBG = {"#1f2937", "#374151", "#ff5f57", "#febc2e", "#28c840",
              "#ff5f56", "#ffbd2e", "#27c93f"}
    NEUTRALBG = {"#fff", "#ffffff", "#f8fafc", "#fafaff", "#f5f3ff",
                 "#f9fafb", "#f1f5f9", "#f3f4f6", "#f6f8fa"}
    bgs = Counter(x.lower() for x in
                  re.findall(r'background:\s*(#[0-9a-fA-F]{6}|#fff)\b', html))
    # 浅色底：只算「明度 > 0.92 的彩色底」——实心主色（#14b8a6/#0f766e/#e8590c）是徽标/竖条，
    # 不算底色；白/近白中性色也不算。
    tint = {k: v for k, v in bgs.items()
            if k not in CODEBG and k not in NEUTRALBG and luma(k) > 0.92}
    if len(tint) > 3:
        warnings.append(
            f"[G] 浅色底 {len(tint)} 种（红线 >3，理想 1 种 + 警示底）: "
            + " / ".join(f"{k}×{v}" for k, v in sorted(tint.items(), key=lambda x: -x[1]))
            + " —— 底色收敛到 1 种（+ 警示卡琥珀底 ≤2 处），功能提示改走左侧 3px 竖条")
    else:
        ok.append(f"[G] 浅色底 {len(tint)} 种"
                  + ("（" + " / ".join(tint) + "）" if tint else ""))

    # 正文灰混用：只在「灰」之间比（主题色不参与），第二灰 ≥5 次且占比 >25% 才算混用
    bodyc = Counter()
    for m in re.finditer(r'<p\b([^>]*)>', html):
        a = m.group(1)
        fs = re.search(r'font-size:\s*([\d.]+)px', a)
        cl = re.search(r'color:\s*(#[0-9a-fA-F]{6})', a)
        if fs and cl and 13.5 <= float(fs.group(1)) <= 15.5:
            bodyc[cl.group(1).lower()] += 1
    grays = sorted({c: n for c, n in bodyc.items() if is_gray(c)}.items(),
                   key=lambda x: -x[1])
    if len(grays) >= 2:
        main_c, main_n = grays[0]
        for second_c, second_n in grays[1:]:
            if second_n >= 5 and second_n / max(main_n, 1) > 0.25:
                warnings.append(
                    f"[G] 正文灰混用：{main_c}×{main_n} 与 {second_c}×{second_n} 同时在用"
                    " —— 正文只许一种灰（#3d3d3d），次要文字只用 #999")
                break

    # 满宽 4px 粗分隔线（禁；改居中短线 60×3）
    wide_hr = len(re.findall(
        r'<section(?=[^>]*height:\s*4px)(?=[^>]*background:)[^>]*>', html))
    if wide_hr:
        problems.append(f"[G] {wide_hr} 条满宽 4px 粗分隔线 —— 改居中短线 60×3"
                        "（满宽粗线与章节标题条重量相当，两个锚点互抢）")

    # 卡片套卡片（只有「彩色底容器」算卡片；白/近白容器不算，页面外层就是白的）
    nest, stack = 0, []
    for m in re.finditer(r'<section\b([^>]*)>|</section>', html):
        if m.group(0) == '</section>':
            if stack:
                stack.pop()
            continue
        attrs = m.group(1) or ''
        bm = re.search(r'background:\s*(#[0-9a-fA-F]{6}|#fff)\b', attrs)
        bg = bm.group(1).lower() if bm else None
        card = bg if (bg and bg not in NEUTRALBG) else None
        prev = [s for s in stack if s]
        # 代码块的 #1F2937 + #374151 是组件本身，白名单放行
        if card and prev and not (card == "#374151" and prev[-1] == "#1f2937"):
            nest += 1
        stack.append(card)
    if nest:
        warnings.append(f"[G] {nest} 处卡片套卡片 —— 内层改裸文字，或拆成并列卡")

    # 有色文字色种数（剔除 <pre> 的语法高亮色，也剔除灰阶）
    html_nopre = re.sub(r'<pre\b.*?</pre>', '', html, flags=re.S)
    allc = {c.lower() for c in re.findall(r'color:\s*(#[0-9a-fA-F]{6})', html_nopre)}
    colored = {c for c in allc if not is_gray(c)}
    if len(colored) > 4:
        warnings.append(f"[G] 有色文字色 {len(colored)} 种（目标 ≤4，爆款实测 3 种）: "
                        + " ".join(sorted(colored)))
    else:
        ok.append(f"[G] 有色文字色 {len(colored)} 种")

    # ---------- H 导读卡（2026-09-16 新增：标题区 → 导读卡 → 第 1 章 三段直落）----------
    # 导读卡 = 关键词标签之前、**最后一张不带左边框的浅底卡**
    # （不能取"文字最长的"：Pi 04 标题区里还有一张 #F8FAFC 功能卡，长度超过真导读；
    #   也不能取第一张：前面还可能有「↩️ 上一篇」卡 / 系列卡）
    head_area = html[:body_start] if body_start else html
    # 关键词标签区 = 第一个内含「# 药丸 span」的 section。
    # 注意：不能再用「含 font-size:0 的 section」来判断——标题区那条居中分隔线
    # 也带 font-size:0（2026-09-17 为压缩留白加的），会把 scan 截在它前面，
    # 导读卡反被判成"不存在"。
    kwm = None
    for mm in re.finditer(r'<section\b[^>]*>(.*?)</section>', head_area, re.S):
        if re.search(r'<span\b[^>]*border-radius:12px[^>]*>\s*#', mm.group(1)):
            kwm = mm
            break
    scan = head_area[:kwm.start()] if kwm else head_area
    dk = None
    for mm in re.finditer(r'<section\b([^>]*)>(.*?)</section>', scan, re.S):
        attrs, inner = mm.group(1), mm.group(2)
        bm = re.search(r'background:\s*(#[0-9a-fA-F]{6})', attrs)
        if not bm or 'border-left' in attrs.replace(' ', ''):
            continue
        try:
            if luma(bm.group(1)) < 0.72:    # 不是浅底
                continue
        except Exception:
            continue
        txt = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', inner)).strip()
        if txt and not txt.startswith('#'):
            dk = txt                         # 持续覆盖 → 结果是最后一张
    if not dk:
        problems.append("[H] 标题区下方找不到导读卡（浅色底 section）——结构必须是"
                        "「标题区 → 导读卡 → 第 1 章」，中间不许有目录框/系列卡/引子")
    else:
        n_dk = len(dk)
        if n_dk > 200:
            problems.append(f"[H] 导读卡 {n_dk} 字（红线 200）——超长导读在手机上是一堵墙，"
                            f"砍到 120 字以内，只留读者痛点")
        elif n_dk > 150:
            warnings.append(f"[H] 导读卡 {n_dk} 字，超过 150（爆款实测 140-151）——再紧一点")
        elif n_dk < 40:
            warnings.append(f"[H] 导读卡只 {n_dk} 字（应为 40-150 字）——"
                            f"疑似系列卡/目录残留，导读必须说清读者痛点 + 这篇给什么")
        else:
            ok.append(f"[H] 导读卡 {n_dk} 字")
        VAGUE = ['在当今', '随着', '越来越', '最大的毛病', '众所周知', '普遍存在', '不可否认']
        sents = split_sents(dk)
        first = sents[0] if sents else dk
        hit = [w for w in VAGUE if w in first]
        if hit:
            warnings.append(f"[H] 导读卡首句是泛论定性（命中「{'、'.join(hit)}」）——"
                            "首句必须给读者一个亲历过的具体画面，禁「XX 最大的毛病是…」这种讲道理开场")
        # 2026-10-09 反转本条：原写「首句必须带『你』」，与 skill 的
        # 「首句先立主体（产品名），不要一上来就用代词」直接冲突，
        # 用户否 OpenWebUI 01 导语时原话「又是你啊、它啊之类的语言」——
        # 他给的正样本（逛逛GitHub）首句是「Rakazo 可以搭建…」，主语就是产品名。
        # 所以本条从「必须有你」改成「不许用代词起头」。
        PRONOUN_HEAD = ['你', '您', '它', '她', '他', '这', '那']
        head = first.lstrip()
        if head[:1] in PRONOUN_HEAD:
            warnings.append(f"[H] 导读卡首句用代词「{head[:1]}」起头——"
                            "首句必须先把主体（产品名／名词）立起来，"
                            "读者还没建立指代关系，代词留到后文再用")
        # 注：「导读与第 1 章重复」不做自动检测。实测该指标无区分度——
        # 爆款 Pi 02 触发 7 处、Pi 04 触发 2 处，而真出问题的 WB13 只有 4 处。
        # 判定只能人工读：导读讲结论、第 1 章又讲一遍同一句才叫重复。

    # ---------- I 手机显示友好度（2026-09-17 新增）----------
    # 用户定：①标题 ≤17 字符 ②图注 ≤15 字 ③禁并排双卡 ④禁串行（并列项一项一行）
    #         ⑤标题区留白 ≤30px
    # 基准样本：《又从头讲一遍？Hermes替你记住》= 17 字符（手机上一行刚好放得下）
    # ③④ 是一件事的两面：用户先否「两栏排版」，又否「把清单压成一行」——
    # 正确形态＝上下堆叠的单栏卡 + 卡内一项一个 <p> 竖排。

    # I1 标题长度
    # 主口径（用户 2026-09-17 定）：总字符数 ≤17 —— 基准样本
    # 《又从头讲一遍？Hermes替你记住》= 17 字符，手机上刚好一行放得下。
    # 辅口径：显示宽度 ≤15（中文/全角 1，英文字母·数字·半角 0.5）。
    # 因为中文字宽是英文的两倍——纯中文 17 字其实比中英混排 17 字符更宽，会折行。
    mh = re.search(r'<h1\b[^>]*>(.*?)</h1>', html, re.S)
    if mh:
        t = re.sub(r'<[^>]+>', '', mh.group(1)).strip()
        t = re.sub(r'\s+', '', t)
        wid = sum(1 if ord(c) > 0x2000 else 0.5 for c in t)
        if len(t) > T_TITLE_MAX:
            problems.append(f"[I] 标题 {len(t)} 字符 > {T_TITLE_MAX}：「{t}」"
                            f"——手机上放不下一行会折行，看着乱")
        elif wid > T_TITLE_WIDTH:
            warnings.append(f"[I] 标题 {len(t)} 字符 / 显示宽 {wid:g} > {T_TITLE_WIDTH}"
                            f"：「{t}」——字符数没超，但中文字宽大，仍可能折行")
        else:
            ok.append(f"[I] 标题 {len(t)} 字符 / 显示宽 {wid:g}（上限 {T_TITLE_MAX} 字符"
                      f"·{T_TITLE_WIDTH} 宽）：「{t}」")
    else:
        warnings.append("[I] 没找到 h1 主标题")

    # I2 图注字数（图注 = 图下「居中 + 灰字」的 p；去掉 ▲ 和 emoji 后计数）
    # 判据是「居中 + #999」两个条件同时成立，但要再排掉标题区的副标题 ——
    # 副标题也是「居中 + 13px + #999」，若只按字号过滤会把它误判成图注
    # （2026-09-22 修误报：副标题「GitHub 项目不知道怎么跑？直接丢给 AI」被当成 21 字图注报硬错误）。
    # 定式：先切掉「标题区块」section，图注只在该区块之外找。
    body_for_cap = html
    mtt = re.search(r'<!--\s*标题区块\s*-->(.*?)</section>', html, re.S)
    if mtt:
        body_for_cap = html.replace(mtt.group(0), '', 1)
    cap_bad, cap_n = [], 0
    for mc in re.finditer(r'<p\b([^>]*)>(.*?)</p>', body_for_cap, re.S):
        a = mc.group(1).replace(' ', '')
        if 'text-align:center' not in a or 'color:#999' not in a:
            continue
        fs = re.search(r'font-size:([\d.]+)px', a)
        if fs and float(fs.group(1)) > 13.5:
            continue
        txt = re.sub(r'<[^>]+>', '', mc.group(2))
        txt = re.sub(r'[\s\u2000-\u303f\u2190-\u2bff\U0001F000-\U0001FAFF]', '', txt)
        txt = re.sub(r'[▲●◆·]+', '', txt)
        if not txt:
            continue
        cap_n += 1
        if len(txt) > T_CAP_MAX:
            cap_bad.append((txt, len(txt)))
    if cap_bad:
        problems.append(f"[I] {len(cap_bad)} 条图注超过 {T_CAP_MAX} 字："
                        + " / ".join(f"「{t}」{n}字" for t, n in cap_bad[:3])
                        + " —— 图注长了在手机上是三行小字，压到 15 字以内")
    elif cap_n:
        ok.append(f"[I] {cap_n} 条图注均 ≤ {T_CAP_MAX} 字")

    # I3 并排双卡（禁：inline-block + 半宽，手机上挤成细柱）
    # 2026-10-21 放宽：原来只认 <section>，用 <span> 写并排就整段漏过（Pi 01 实测 4 处）。
    # 判据改成「任何标签 + inline-block + 宽度 40~60%」——满宽 100% 的卡不算并排，不误报。
    side = []
    for mt in re.finditer(r'<(\w+)\b[^>]*>', html):
        s = mt.group(0)
        if not re.search(r'display:\s*inline-block', s):
            continue
        mw = re.search(r'width:\s*(\d{1,3})%', s)
        if mw and 40 <= int(mw.group(1)) <= 60:
            side.append(mt.group(1))
    if side:
        problems.append(f"[I] {len(side)} 处并排双卡（{side[0]} + inline-block + 半宽）——"
                        "手机上两栏会挤成细柱，改「上下堆叠的单栏卡」")

    # I4 标题区 → 导读卡 的留白合计
    gaps = []
    mg = re.search(r'<section\s+style="text-align:center;padding:\d+px\s+0\s+(\d+)px;"', html)
    if mg:
        gaps.append(('标题区pb', int(mg.group(1))))
    mg = re.search(r'<p\s+style="font-size:13px;color:#999;margin:0\s+0\s+(\d+)px;"', html)
    if mg:
        gaps.append(('副标题mb', int(mg.group(1))))
    mg = re.search(r'<section\s+style="text-align:center;margin:0\s+0\s+(\d+)px;[^"]*">\s*'
                   r'<span[^>]*width:60px;height:3px', html)
    if mg:
        gaps.append(('分隔线mb', int(mg.group(1))))
    if gaps:
        tot = sum(v for _, v in gaps)
        detail = " + ".join(f"{k} {v}" for k, v in gaps)
        if tot > T_TITLE_GAP:
            warnings.append(f"[I] 标题区→导读卡留白合计 {tot}px（{detail}，上限 {T_TITLE_GAP}）"
                            " —— 手机上标题和导语之间空太大，第一屏被白白吃掉")
        else:
            ok.append(f"[I] 标题区→导读卡留白 {tot}px（{detail}）")

    # I5 伪清单（用户 2026-09-17 二次纠正）：并列项被压进同一个 <p> 用 「 · 」 串联
    #     判据：一个 <p> 里出现 ≥2 个 「 · 」 分隔符，且该段无句号（不是正常句子）
    fake = []
    for mc in re.finditer(r'<p\b[^>]*>(.*?)</p>', html, re.S):
        txt = re.sub(r'<[^>]+>', '', mc.group(1))
        txt = txt.replace('&nbsp;', ' ').strip()
        if txt.count(' · ') >= 2 and '。' not in txt:
            fake.append(txt)
    if fake:
        warnings.append(f"[I] {len(fake)} 处「伪清单」——并列项被压进同一个 <p> 用「 · 」串联："
                        + " / ".join(f"「{t[:26]}…」" for t in fake[:2])
                        + " —— 看着像一句长话，读者扫不出有几项，须一项一个 <p> 竖排")
    else:
        ok.append("[I] 无「伪清单」（并列项均已一项一行）")

    # ---------- J 标签配对 / 结构完整性（2026-09-20 新增）----------
    # 起因：往已排好的 HTML 里插段落时，若 old_string 取的是纯文本（不含 </p>），
    # 新段落的 <p> 会落在旧 </p> 之前 → 变成 <p> 套 <p>。浏览器会自动补闭合，
    # 肉眼完全看不出来，只有标签计数对不上（实测 71 开 / 69 闭）。
    # 定式：插段落的 old_string 必须带上 </p>，或整段连标签一起换。
    pair_bad = []
    for tag in ("section", "p", "span", "pre"):
        a = len(re.findall(r"<%s\b" % tag, html))
        b = len(re.findall(r"</%s>" % tag, html))
        if a != b:
            pair_bad.append(f"{tag} {a} 开 / {b} 闭")
    if pair_bad:
        problems.append("[J] 标签未配对：" + "，".join(pair_bad)
                        + " —— 多半是插段落时把 </p> 挤歪了，"
                          "浏览器会自动补全，肉眼看不出来")
    else:
        ok.append("[J] 标签配对正常（section / p / span / pre）")

    nest = len(re.findall(r"<p\b[^>]*>\s*<p\b", html))
    dbl = html.count("</p></p>")
    if nest:
        problems.append(f"[J] 发现 {nest} 处 <p> 嵌套（<p> 里又开 <p>）"
                        " —— 段落插入位置错了，改成平级")
    if dbl:
        problems.append(f"[J] 发现 {dbl} 处 </p></p>"
                        " —— 多出来的闭合，说明有段落被套住了")
    if not nest and not dbl:
        ok.append("[J] 无 <p> 嵌套、无重复闭合")

    # ---------- 输出 ----------
    report = {
        "file": os.path.basename(path),
        "章节数": n_chap,
        "净字数": sum(len(t) for t in ps) if ps else 0,
        "问题": problems,
        "警告": warnings,
        "通过": ok,
    }

    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        line = "=" * 68
        print(line)
        print(f"排版自检 · {report['file']}")
        print(line)
        for p in problems:
            print("  [硬错误] " + p)
        for w in warnings:
            print("  [ 警告 ] " + w)
        for o in ok:
            print("  [ 通过 ] " + o)
        print(line)
        print(f"结论: 硬错误 {len(problems)} / 警告 {len(warnings)}"
              + ("  ✅ 可发布" if not problems and not warnings
                 else "  ⚠️ 需修" if not problems else "  ❌ 必须修"))

    return 2 if problems else (1 if warnings else 0)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    sys.exit(main())
