#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
content-check.py — 公众号发布前安检（可机械化的那部分）

把内容安检里**能用规则判**的部分做成闸门（9 类），
剩下的语义判断仍归模型。分工：

  本脚本负责（有确定性答案的）：
    · 隐私信息：邮箱 / 手机号 / 真实本地路径 / IP / 密钥 / 密码赋值
    · 违禁词与夸大词：命中后按语境分高危/提示，不机械计数
    · 平台诱导：转发朋友圈 / 关注后领取 / 点赞在看 等
    · 学术诚信：代写论文 / 论文包过 / 编造数据
    · 无出处数字：N 倍 / N% 提升 / 翻 N 倍（提示，需人工确认出处）
    · 占位符残留：TODO / [图：/ {{ }} / 待补 —— 真·发布阻断项
    · 发布阻断项：HTTP 图片（微信会拦）、禁用标签 table/div/ul/li/a href
    · 句式：对偶拆分、「不是 A 而是 B」「不是 A，是 B」——第 23 条②／第 50 条，**必须改**
    · 指代与边界：这块／那类／另一种、是两回事——第 45 条，中危按语境判

  句式分两档（legacy 参数控制）：默认 hard，命中即报「改完再发」；
  加 --legacy（旧稿重推）全部降为 soft，只给提示，不阻断。

  模型负责（脚本判不了）：
    · 事实性风险（数据是否真有出处）
    · 语境是否安全（脚本给提示，最终由人确认）
    · 学术诚信的隐含表述

退出码：0 = 无高危（可交付）1 = 有高危 2 = 文件读不了

用法：
  python content-check.py <文章.html>
  python content-check.py <文章.html> --json
  python content-check.py <文章.html> --quiet   # 只打印结论
"""

import argparse
import html as html_mod
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
WORDS_FILE = os.path.join(os.path.dirname(HERE), "references", "forbidden-words.md")

# ── 内置词表：脚本自身是唯一执行源，forbidden-words.md 是给人看的词库，
#    两边都会生效（脚本追加词库里的词），所以词库更新不需要改代码。
# 无歧义的高危词：在技术文里几乎不可能是正常描述，命中即报
BUILTIN_HIGH = [
    "顶级", "极致", "国家级", "世界级", "独家", "首创",
    "百分之百", "史无前例", "空前绝后",
    "王者", "巅峰", "霸主", "绝对有效", "绝对安全", "保证有效", "保证成功",
]
# 要按语境判的词。这些词在技术文里大量正常出现：
# 「第一轮」「最底层」「唯一有权限的模型」「万能转接头」「永久黑名单」
# ——机械计数必然误报，必须看搭配。
CONTEXT_WORDS = ["最", "第一", "绝对", "唯一", "完美", "全网", "全球", "万能", "永久"]

BUILTIN_MID = ["神器", "秒懂", "必学", "必备", "重磅", "干货满满", "看完就会",
               "一键搞定", "包教包会", "零基础速成", "翻倍", "暴涨"]

BUILTIN_INDUCE = ["转发到朋友圈", "分享到朋友圈", "关注后领取", "点赞收藏",
                  "在看+转发", "加微信领取", "点击下方有惊喜", "送资料包"]

BUILTIN_ACADEMIC = ["代写论文", "一键生成论文", "论文包过", "代发表", "随便编个数据"]

# 安全语境：描述性用法，不算违禁
SAFE_PATTERNS = [
    r"第[一二三四五六七八九十百\d]+[步篇次站天年周月件条种个轮版期章节层级维档回]",
    r"第一(反应|时间|眼|感觉|印象|想法|直觉|时间|天|周|版|批)",
    r"最(推荐|关键|需要|简单|容易|省|怕|震撼|重要|大|小|好|快|慢|近|后|初|终|新|佳|多|少|低|高|先|晚|早|常|难|易|直接|明显|通用|常见|常用|主流|普遍|典型|基础|基本)",
    r"最[一二三四五六七八九十\d]",
    r"绝对(路径|值|坐标|地址|引用|定位|偏差)",   # 技术术语，不是承诺
    # 方位/序位描述：「最底层」「最外层」「最开始」都是正常写法
    r"最(底层|外层|上层|内层|顶层|开始|初|上面|下面|里面|外面|前面|后面|基础|根本|核心|外围|内部|外部)",
    r"最(值钱|值得|实用|好用|管用|有用|花时间|麻烦|坑|费劲|容易踩)",
    # 「最好还发一条」「最好别」「最好能」是建议语气，不是「最好」的宣示义
    r"最好(还|能|是|别|不要|用|在|先|提前|留)",
    # 技术术语里的「永久」：黑名单、存储、删除、挂载
    r"永久(黑名单|名单|删除|保存|存储|记录|地址|链接|配置|保留|封禁|禁用|挂载|重定向|有效端口)",
    # 技术语境里的「万能」通常是比喻：转接头 / 适配层
    r"万能(转接头|适配|接口|插头|入口)",
    # 否定绝对化 / 叮嘱语气，都不构成广告法问题
    r"(没有|不存在|并非|不是|哪来|谈不上)绝对",
    r"绝对(不|别|勿)",
]
# 风险语境分两层。这个区分来自 111 篇已发文章的全量回归：
# 第一版把「最好的工具」「全球最大的代码托管平台」全判高危，误报 33 处。
# 广告法真正管的是「商家对自身商品的身份/荣誉主张」，
# 作者评价第三方工具属于程度描述，风险低一档，交人工判断。
RISK_IDENTITY = [   # 高危：身份/荣誉主张
    r"(行业|国内|全球|全网|世界|全国)第一",
    r"第一(品牌|名|人)",
    r"(行业|国内|全球|全网|世界|全国)首个",
    r"百分",
    r"保证(有效|成功|通过|赚钱)",
    r"绝对(有效|安全|没错|管用)",
]
RISK_CLAIM = [      # 中危：程度性绝对化（多为评价，需人工判断）
    r"最(好|强|优|棒|牛|顶级|厉害|先进)",
    r"第一梯队",
    r"唯一(选择|推荐|答案|方案)",
    r"完美(解决|方案|兼容|适配)",
    r"万能(公式|方案|钥匙|法则)",
    r"永久(免费|有效|保证|不变)",
    r"全网(最|第一|首发|独家|最低)",
    r"全球(第一|领先|首发|首创|最)",
]

# (名称, 正则, 级别)。级别区分说明见 check_privacy。
PRIVACY_PATTERNS = [
    ("邮箱", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "high"),
    ("手机号", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "high"),
    ("身份证", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"), "high"),
    # Windows 用户目录、macOS /Users 基本等于真人名字 → 高危
    ("本地路径（用户目录）", re.compile(
        r"[A-Za-z]:\\Users\\(?!xxx|your|username|你的|用户名)[^\s\\]+"), "high"),
    ("本地路径（macOS 家目录）", re.compile(
        r"/Users/(?!user\b|username|yourname|你的|shared\b)[A-Za-z0-9_-]+"), "high"),
    # Linux /home 在教程里常是容器用户或示例用户 → 降为中危
    ("本地路径（Linux 家目录）", re.compile(
        r"/home/(?!user\b|username|yourname|你的|node\b|app\b)[A-Za-z0-9_-]+"), "mid"),
    ("IP 地址", re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])"), "high"),
    ("API 密钥", re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|AIza[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{20,}|xox[bap]-[A-Za-z0-9-]{10,})"), "high"),
    ("密码赋值", re.compile(r"(?:密码|口令|password|passwd|token|secret)\s*[:=]\s*[^\s，。]{6,}", re.I), "high"),
]

# 无出处数字：只作提示，脚本判不了有没有出处
VAGUE_NUM = re.compile(r"(\d+(?:\.\d+)?\s*(?:倍|%|％))|(?:翻|增长|提升|提高|快了)\s*\d+(?:\.\d+)?\s*倍")
VAGUE_SRC = re.compile(r"(研究表明|数据显示|有研究|据调查|据统计)")

# 占位符：只放**不可能出现在正常中文里**的串。
# 教训：第一版放了「略」，结果「检索策略」「战略」「省略」全被扫成发布阻断项。
PLACEHOLDERS = ["TODO", "FIXME", "待补", "{{", "}}", "[图：", "[图:", "【图：", "待填"]

BAD_TAGS = {
    "<table": "素材是表格不许排 <table>，转上下堆叠卡片",
    "<div": "公众号编辑器会吃掉 div，只用 section",
    "<ul": "禁用列表标签，卡内并列清单一项一个 p",
    "<ol": "禁用列表标签",
    "<li": "禁用列表标签",
}


# ── 词库读取 ────────────────────────────────────────────────────────────

def load_lexicon():
    """从 forbidden-words.md 里补词。按所在小节标题分档。"""
    extra = {"high": [], "mid": [], "induce": [], "academic": []}
    if not os.path.isfile(WORDS_FILE):
        return extra
    try:
        with open(WORDS_FILE, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().split("\n")
    except OSError:
        return extra

    bucket = None
    for line in lines:
        if line.startswith("## "):
            h = line[3:]
            if "诱导" in h or "平台违规" in h:
                bucket = "induce"
            elif "学术" in h:
                bucket = "academic"
            elif "高危" in h:
                bucket = "high"
            elif "中危" in h:
                bucket = "mid"
            else:
                bucket = None  # 金融/医疗/教育等领域红线，按中危提示
                if any(k in h for k in ("金融", "医疗", "教育", "技术")):
                    bucket = "mid"
            continue
        if not line.startswith("|") or bucket is None:
            continue
        cell = line.strip("|").split("|")[0].strip()
        if not cell or cell in ("词", "词/模式") or set(cell) <= set("-: "):
            continue
        if len(cell) > 14:
            continue
        if cell not in extra[bucket]:
            extra[bucket].append(cell)
    return extra


# ── 正文提取 ────────────────────────────────────────────────────────────

def extract_blocks(raw_html):
    """返回 [(段号, 文本)]，按块切，用于定位。"""
    s = re.sub(r"<script.*?</script>", "", raw_html, flags=re.S | re.I)
    s = re.sub(r"<style.*?</style>", "", s, flags=re.S | re.I)
    # 代码块单独占一块，标出来
    s = re.sub(r"<pre.*?</pre>", "\n@@PRE@@\n", s, flags=re.S | re.I)
    s = re.sub(r"</(p|section|h[1-6]|blockquote|figcaption|td|th|li|tr|pre)>",
               "\n", s, flags=re.I)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = html_mod.unescape(s)
    blocks = []
    for chunk in s.split("\n"):
        t = chunk.strip()
        if t:
            blocks.append(t)
    return blocks


def is_pre(block):
    return block.strip() == "@@PRE@@"


# ── 检查项 ──────────────────────────────────────────────────────────────

def ctx(text, start, end, pad=14):
    return text[max(0, start - pad): min(len(text), end + pad)]


def check_lexicon(blocks, lex):
    high, mid = [], []
    # ⚠️ 词库里也有「最 / 第一 / 全球 / 绝对」，这些必须走语境判断。
    # 曾经没排除，导致词库补进来的「第一」绕过了语境规则，
    # 把「第一轮立刻开始」判成广告法高危——误报。
    ctx_set = set(CONTEXT_WORDS)
    high_words = [w for w in dict.fromkeys(BUILTIN_HIGH + lex["high"]) if w not in ctx_set]
    mid_words = [w for w in dict.fromkeys(BUILTIN_MID + lex["mid"]) if w not in ctx_set]

    for idx, b in enumerate(blocks):
        if is_pre(b):
            continue
        # 高危：无歧义的绝对化词
        for w in high_words:
            if not w or w not in b:
                continue
            # 「完美/全网/全球」等可能出现在正常叙述，仍报高危但标语境
            high.append((idx, w, "广告法绝对化用语", ctx(b, b.find(w), b.find(w) + len(w))))

        # 需要看语境的词：先看有没有身份/荣誉主张，再看安全搭配，最后才是程度承诺
        for w in CONTEXT_WORDS:
            for m in re.finditer(re.escape(w), b):
                seg = ctx(b, m.start(), m.end())
                if any(re.search(p, seg) for p in RISK_IDENTITY):
                    high.append((idx, seg, f"含「{w}」且落在身份/荣誉主张", seg))
                elif any(re.search(p, seg) for p in SAFE_PATTERNS):
                    continue  # 描述性/技术术语用法，不报
                elif any(re.search(p, seg) for p in RISK_CLAIM):
                    mid.append((idx, seg, f"含「{w}」的程度性绝对化（评价类，人工判断）", seg))
                else:
                    mid.append((idx, seg, f"含「{w}」，语境待人工确认", seg))

        for w in mid_words:
            if w and w in b:
                mid.append((idx, w, "夸大/营销词", ctx(b, b.find(w), b.find(w) + len(w))))
    return high, mid


def is_private_ip(s):
    """私有/保留网段不算隐私泄露 —— 教程里 192.168.x.x 是必须写的。
    只有公网 IP 才是真风险（暴露真实家庭/服务器地址）。"""
    try:
        parts = [int(x) for x in s.split(".")]
    except ValueError:
        return True
    if len(parts) != 4 or any(p > 255 for p in parts):
        return True
    a, b = parts[0], parts[1]
    if a in (0, 10, 127, 255):
        return True
    if a == 172 and 16 <= b <= 31:
        return True
    if a == 192 and b == 168:
        return True
    if a == 169 and b == 254:
        return True
    if a == 100 and 64 <= b <= 127:   # CGNAT
        return True
    if a >= 224:                      # 组播 / 广播
        return True
    return False


def check_privacy(blocks):
    """返回 (高危命中, 中危命中)。"""
    hard, soft = [], []
    for idx, b in enumerate(blocks):
        if is_pre(b):
            continue
        for name, pat, level in PRIVACY_PATTERNS:
            for m in pat.finditer(b):
                val = m.group(0)
                if name == "IP 地址" and is_private_ip(val):
                    continue
                hit = (idx, val, name, ctx(b, m.start(), m.end(), 8))
                (hard if level == "high" else soft).append(hit)
    return hard, soft


def check_induce(blocks, lex):
    hits = []
    for idx, b in enumerate(blocks):
        if is_pre(b):
            continue
        for w in BUILTIN_INDUCE + lex["induce"]:
            if w and w in b:
                for m in re.finditer(re.escape(w), b):
                    hits.append((idx, w, "诱导分享/关注/互动", ctx(b, m.start(), m.end())))
                    break
    return hits


def check_academic(blocks, lex):
    hits = []
    for idx, b in enumerate(blocks):
        for w in BUILTIN_ACADEMIC + lex["academic"]:
            if w and w in b:
                hits.append((idx, w, "学术诚信风险", ctx(b, b.find(w), b.find(w) + len(w))))
    return hits


def check_vague(blocks):
    hits = []
    for idx, b in enumerate(blocks):
        if is_pre(b):
            continue
        for m in VAGUE_NUM.finditer(b):
            seg = ctx(b, m.start(), m.end(), 20)
            if any(re.search(p, seg) for p in SAFE_PATTERNS):
                continue
            hits.append((idx, m.group(0), "数字无出处（需人工确认）", seg))
        if VAGUE_SRC.search(b) and len(b) < 120:
            hits.append((idx, VAGUE_SRC.search(b).group(0), "模糊归因（说不出来源）", b))
    return hits


def check_placeholders(blocks):
    hits = []
    for idx, b in enumerate(blocks):
        if is_pre(b):
            continue
        for w in PLACEHOLDERS:
            if w in b:
                hits.append((idx, w, "占位符未替换（发布阻断）", ctx(b, b.find(w), b.find(w) + len(w))))
    return hits


# ── 第 50 条：对偶拆分 / 否定绕弯（2026-10-22 用户点名最讨厌的句式）─────────
# 用户原话：「特别讨厌那种什么什么分两摊，各管一边，这种类型的，绕来绕去说一通」
# 判中危不判高危：句式是写作质量问题，不该阻断已发布旧稿的重复推送；
# 但写新稿时必须看得见 —— 报告里逐处列出来（含上下文），一处都别漏。
DUI_PATTERNS = [
    (r"各管一摊|各管一边|各管一头|各管各的|各干各的|各干一摊|各配各的|各走各的",
     "对偶拆分：把事劈两半各给一句"),
    (r"分两头|分两摊|两摊", "对偶拆分：分两摊"),
    (r"前者|后者", "前者/后者：读者得回头数，换成就近名词"),
    (r"一半[^。！？\n]{0,40}另一半", "对偶拆分：一半…另一半"),
    (r"一头[^。！？\n]{1,20}一头", "对偶拆分：一头 X 一头发"),
    (r"一(?:个|套|头|边|路)管[^。！？\n]{0,20}[，,；]\s*一(?:个|套|头|边|路)管",
     "对偶拆分：一个管 X，一个管 Y"),
    (r"一边是[^。！？\n]{0,25}一边是", "对偶拆分：一边是 X，一边是 Y"),
    # 第 23 条 ② 原文是「不是 A，是 B」/「不仅仅是…而是…」，两种都要抓：
    # 「不仅仅是」不含连续的「不是」，只认「而是」会把这两个句式全漏掉（2026-10-22 审计补）
    (r"(?:不(?:仅仅|仅|只)?|仅|只)是[^。！？\n]{1,25}?而是",
     "否定绕弯「不是 A 而是 B」：全禁，改回系动词"),
    (r"(?<!是)不是[^。！？\n]{1,25}?[，,]\s*是",
     "否定绕弯「不是 A，是 B」：全禁，改回系动词"),
]
# 只提醒不判违规的：可能是真清点（「你要做两件事，A、B」是允许的写法）
DUI_SOFT_HINTS = [
    (r"是两件事|是两回事|两件事是分开", "疑似劈两半（第 50 条边界）：确认是清点还是对偶"),
]

# 第 45 条病二：含糊的口语指代（2026-10-22 审计新增）。
# 这类词读者得自己猜指的是什么，正解是换成具体名词。全库实测频率都不高
# （这块 20、一回事 8、这一趟 5、还是那个 5、那条路 3），加进脚本不会被淹没。
VAGUE_REF_PATTERNS = [
    (r"这块儿|这块", "含糊指代「这块」：换成具体名词（第 45 条）"),
    (r"那条路|那一套|那一头", "含糊指代：读者得自己猜指的是什么（第 45 条）"),
    (r"一回事", "含糊指代「一回事」：说清是哪件事（第 45 条）"),
    (r"人还是|还是那个", "含糊指代／抖机灵（第 45 条）"),
    (r"这一趟", "含糊指代「这一趟」：换成具体名词（第 45 条）"),
    (r"那类|另一种", "含糊指代（第 45 条）：说清是哪一类／哪一种"),
]


def check_duiou(blocks, legacy=False):
    """返回 5 元组，第 5 位是级别。

    级别必须分开，不能用同一档：第 23 条②「不是 A 而是 B」和第 50 条对偶拆分
    是「一处都不许留」的硬规则（hard）；第 45 条含糊指代（这块／那类／另一种）
    用户定的是「判中危」（soft），混进 hard 会把「另一种做法是先备份」这种
    正常句子也拦成 ❌，等于逼人改好句子。2026-10-22 审计修。

    legacy=True 时全部降为 soft：只给旧稿重推用（2026-10-22 用户拍板）。
    新写的稿不许加 --legacy，否则这个开关就成了绕过闸门的后门。
    """
    hits = []
    for idx, b in enumerate(blocks):
        if is_pre(b):
            continue
        for table, level in ((DUI_PATTERNS, "hard"),
                             (DUI_SOFT_HINTS, "soft"),
                             (VAGUE_REF_PATTERNS, "soft")):
            for pat, why in table:
                for m in re.finditer(pat, b):
                    lv = "soft" if legacy else level
                    hits.append((idx, m.group(0), why,
                                 ctx(b, m.start(), m.end(), 18), lv))
    return hits


def check_html(raw):
    hits = []
    low = raw.lower()
    for tag, why in BAD_TAGS.items():
        if tag not in low:
            continue
        # 整页 HTML 的外壳 <div class="wrap"> 是唯一例外：它配 <style>.wrap{max-width:720px}</style>
        # 存在，粘进公众号编辑器时被剥掉，不构成排版问题（2026-10-21 实测真实产物：正文 0 个 div，
        # body 后紧跟 1 个 wrap）。除此之外任何 div 都报 —— 片段 HTML 里连 wrap 也不该有。
        if tag == "<div":
            shell = re.search(r"<body[^>]*>\s*<div\s+class=[\"']wrap[\"']", low)
            if shell and "<div" not in low[shell.end():]:
                continue
        hits.append((0, tag + ">", why, ""))
    if re.search(r"\bhref\s*=", low):
        hits.append((0, "a href", "禁用超链接标签，链接写纯文本", ""))
    for m in re.finditer(r"<img[^>]+src=[\"']([^\"']+)[\"']", raw, re.I):
        src = m.group(1)
        if not src.startswith("https://"):
            hits.append((0, src[:60], "图片非 HTTPS，微信会拦截或丢失", ""))
    return hits


# ── 输出 ────────────────────────────────────────────────────────────────

def _emit_grouped(out, items, limit=3):
    """同类问题超过 limit 条就折叠成一行 —— 13 张 http 图不该占 13 行。"""
    groups = {}
    order = []
    for it in items:
        key = it[2]
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(it)
    for key in order:
        g = groups[key]
        if len(g) <= limit:
            for it in g:
                # 元组长度不一：check_vague 是 4 元，check_duiou 第 5 位带级别。
                # 按位置取，不整包解包，加字段时不会再炸一次。
                idx, w, why, c = it[0], it[1], it[2], it[3] if len(it) > 3 else ""
                loc = f"第{idx}块" if idx else "全文"
                out.append(f"   · [{loc}] 「{w}」 —— {why}")
                if c and c != w:
                    out.append(f"     语境：…{c.strip()}…")
        else:
            samples = "、".join(f"「{x[1][:32]}」" for x in g[:limit])
            out.append(f"   · {len(g)} 处 —— {key}")
            out.append(f"     举例：{samples} …")


def render(path, blocks, high, mid, vague, privacy_hard, privacy_soft,
           induce, academic, place, htmlhits):
    name = os.path.basename(path)
    total_chars = sum(len(b) for b in blocks if not is_pre(b))
    out = []
    out.append("🛡️ 内容安检报告（脚本闸门）")
    out.append("━" * 46)
    out.append(f"文件：{name}")
    out.append(f"正文字数：{total_chars} · 段落块：{len(blocks)}")
    out.append("")

    hard = list(high) + list(privacy_hard) + list(induce) + list(place) + list(htmlhits)
    out.append(f"🔴 高危（发布前必须处理）：{len(hard)} 处")
    _emit_grouped(out, hard)
    if not hard:
        out.append("   （无）")

    out.append("")
    soft = list(mid) + list(privacy_soft) + list(vague) + list(academic)
    out.append(f"🟡 中危（建议人工看一眼）：{len(soft)} 处")
    seen = set()
    dedup = []
    for it in soft:
        k = (it[0], it[1], it[2])
        if k in seen:
            continue
        seen.add(k)
        dedup.append(it)
    _emit_grouped(out, dedup)
    if not dedup:
        out.append("   （无）")

    out.append("")
    out.append("━ 结论 ━")
    # 句式命中单独定性：不是发布阻断项（退出码仍 0，不卡旧稿重推），
    # 但也不许当「建议看一眼」放过。2026-10-22 用户定「必须改」。
    # 只算 hard（第 23 条② + 第 50 条）：第 45 条含糊指代用户定的是中危，
    # 混进来会把正常句子也判成 ❌。第 5 位缺省按 soft 处理，兼容旧调用。
    style_n = len([v for v in vague if (v[4] if len(v) > 4 else "soft") == "hard"])
    if hard:
        out.append(f"❌ 未通过：{len(hard)} 处高危，先改再推。")
    elif style_n:
        out.append(f"❌ 句式命中 {style_n} 处，必须改（第 23 条②／第 50 条）。退出码仍是 0——")
        out.append("   它不属于发布阻断项，但也不许当「建议看一眼」放过。")
    elif soft:
        out.append(f"⚠️ 基本通过：无高危，{len(soft)} 处中危请人工确认。")
    else:
        out.append("✅ 通过：脚本侧无命中，可以交付。")
    out.append("")
    out.append("注：脚本只管有确定性答案的部分。事实是否真、数据有没有出处，")
    out.append("    还得人看——别把「脚本通过」当成「内容没问题」。")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html_file")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--legacy", action="store_true",
                    help="旧稿重推：句式降为提示，只查排版与结构（新写的稿别加这个）")
    args = ap.parse_args()

    if not os.path.isfile(args.html_file):
        print(f"文件不存在：{args.html_file}", file=sys.stderr)
        return 2
    try:
        with open(args.html_file, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read()
    except OSError as e:
        print(f"读不了：{e}", file=sys.stderr)
        return 2

    lex = load_lexicon()
    blocks = extract_blocks(raw)
    high, mid = check_lexicon(blocks, lex)
    privacy_high, privacy_mid = check_privacy(blocks)
    induce = check_induce(blocks, lex)
    academic = check_academic(blocks, lex)
    vague = check_vague(blocks) + check_duiou(blocks, legacy=args.legacy)
    place = check_placeholders(blocks)
    htmlhits = check_html(raw)

    hard_n = len(high) + len(privacy_high) + len(induce) + len(place) + len(htmlhits)

    if args.json:
        print(json.dumps({
            "file": args.html_file,
            "hard_count": hard_n,
            "high": high, "privacy": privacy_high, "induce": induce,
            "placeholders": place, "html": htmlhits,
            "mid": mid, "privacy_mid": privacy_mid, "vague": vague, "academic": academic,
        }, ensure_ascii=False, indent=2))
        return 1 if hard_n else 0

    text = render(args.html_file, blocks, high, mid, vague,
                  privacy_high, privacy_mid, induce, academic, place, htmlhits)
    if args.legacy:
        # 必须让报告自己说清「这次没按新规查」，否则下次没人记得加过参数
        text = text.replace(
            "🛡️ 内容安检报告（脚本闸门）",
            "🛡️ 内容安检报告（脚本闸门）\n⚠️ 旧稿模式 --legacy：句式降为提示，不判必须改"
            "（新写的稿别加这个参数）", 1)
    if args.quiet:
        print("\n".join(l for l in text.split("\n") if l.startswith(("🔴", "🟡", "❌", "⚠️", "✅"))))
    else:
        print(text)
    return 1 if hard_n else 0


if __name__ == "__main__":
    sys.exit(main())
