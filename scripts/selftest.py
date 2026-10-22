#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wechat-article 自检 — 装完之后先跑这一条。

只查四件事：两个第三方依赖、8 个业务脚本、18 份 references 齐不齐、产出根目录写不写得进去。
另外两项（中文字体、agnes-multimodal 在不在）只提示，不算失败。

加 --smoke 会再真跑一遍：拿一份内置假稿过三个闸门，再造一张纯色图跑裁封面。
全程在系统临时目录里，不调 API、不耗积分，跑完自动删。**它只证明脚本是活的，
不证明任何真实稿子合格。**

技能不需要预建任何工作区目录。写文件时脚本自己 makedirs。

用法：
  python3 scripts/selftest.py
  python3 scripts/selftest.py --home /opt/data/wechat
  python3 scripts/selftest.py --smoke
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_ROOT = os.path.dirname(os.path.dirname(SKILL))
HOME = os.environ.get("WECHAT_HOME", "/opt/data/wechat")

for i, a in enumerate(sys.argv[1:]):
    if a == "--home" and i + 1 < len(sys.argv[1:]):
        HOME = sys.argv[1:][i + 1]
    elif a.startswith("--home="):
        HOME = a.split("=", 1)[1]

rows = []


def ck(name, ok, detail="", soft=False):
    """soft=True 的项失败只提示，不影响退出码。"""
    rows.append((name, ok, detail, soft))


# ① 两个第三方依赖，其余全标准库
for mod, pkg in [("PIL", "Pillow"), ("openpyxl", "openpyxl")]:
    try:
        __import__(mod)
        ck("依赖 " + pkg, True)
    except ImportError:
        ck("依赖 " + pkg, False, "pip install --target %s/pylibs %s" % (HOME, pkg))

# ② 本技能的脚本，七个业务脚本一个不能少（本文件是自检自己，不列）
SCRIPTS = [
    ("fact-diff.py", "改稿前后比对事实"),
    ("layout-check.py", "排版闸门"),
    ("content-check.py", "内容安检"),
    ("preflight.py", "四项一条跑完"),
    ("crop_cover.py", "封面裁 2.35:1"),
    ("add_brand_icons.py", "叠品牌图标"),
    ("build-tracking.py", "重建跟踪表"),
]
sdir = os.path.join(SKILL, "scripts")
for fn, what in SCRIPTS:
    p = os.path.join(sdir, fn)
    ck("脚本 " + fn, os.path.isfile(p), what if os.path.isfile(p) else "缺：" + p)

# ③ references 齐全：七组禁区 + 十二份细则，少一份就是装漏了
REF = [
    # 七组禁区（49 条）
    ("禁区 1-opening", "bans-1-opening.md"),
    ("禁区 2-title", "bans-2-title.md"),
    ("禁区 3-source", "bans-3-source.md"),
    ("禁区 4-sentence", "bans-4-sentence.md"),
    ("禁区 5-structure", "bans-5-structure.md"),
    ("禁区 6-voice", "bans-6-voice.md"),
    ("禁区 7-process", "bans-7-process.md"),
    # 十一份细则
    ("细则 techniques", "techniques.md"),
    ("细则 title-playbook", "title-playbook.md"),
    ("细则 vocab", "vocab.md"),
    ("细则 ai-patterns", "ai-patterns.md"),
    ("细则 ai-smell", "ai-smell.md"),
    ("细则 checklist", "checklist.md"),
    ("细则 compatibility-rules", "compatibility-rules.md"),
    ("细则 style-guide", "style-guide.md"),
    ("细则 forbidden-words", "forbidden-words.md"),
    ("细则 content-check", "content-check.md"),
    ("细则 cover", "cover.md"),
]
for label, rel in REF:
    p = os.path.join(SKILL, "references", rel)
    ck(label, os.path.isfile(p), "" if os.path.isfile(p) else "缺：" + p)

# ④ 产出根目录写不写得进去（容器里最常见的坑是挂载卷只读）
probe_dir = os.path.join(HOME, "output")
try:
    os.makedirs(probe_dir, exist_ok=True)
    probe = os.path.join(probe_dir, ".write-probe")
    with open(probe, "w", encoding="utf-8") as f:
        f.write("ok")
    os.remove(probe)
    ck("产出目录可写", True, probe_dir)
except OSError as e:
    ck("产出目录可写", False, "%s（挂载卷只读或没权限）" % e)

# ⑤ 软项：中文字体。只有要 Pillow 叠中文才需要，平时用不上
fdir = os.path.join(HOME, "assets", "fonts")
fonts = []
if os.path.isdir(fdir):
    fonts = sorted(f for f in os.listdir(fdir) if f.lower().endswith((".ttf", ".otf", ".ttc")))
ck("中文字体", bool(fonts),
   ", ".join(fonts[:3]) if fonts else "没放。不叠中文就不用管；要叠就放 NotoSansSC-*.otf 到 " + fdir,
   soft=True)

# ⑥ 软项：封面要调 agnes-multimodal，但那是另一个技能，可能没装
agnes = os.path.join(SKILLS_ROOT, "media", "agnes-multimodal", "scripts", "agnes_image.py")
ck("agnes-multimodal", os.path.isfile(agnes),
   agnes if os.path.isfile(agnes) else "没找到，封面这一步跑不了。放技能到 skills/media/ 下",
   soft=True)

# ⑦ 可选：--smoke 真跑一遍。全程本地临时目录，不调 API、不耗积分。
# 它只证明「闸门能跑出结论、裁图能出 900×383」，不证明这篇假稿写得合格。
SMOKE_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>smoke</title></head>
<body>
<!-- 标题区块 -->
<section style="text-align:center;padding:24px 0 8px;">
<p style="font-size:40px;margin:0 0 8px;">&#129514;</p>
<h1 style="font-size:22px;margin:0 0 8px;color:#1a1a1a;">冒烟测试</h1>
<p style="font-size:13px;color:#999;margin:0;">验证闸门能不能出结论</p>
<section style="text-align:center;margin:0 0 14px;font-size:0;line-height:0;"><span style="display:inline-block;width:60px;height:3px;background:#E8590C;border-radius:2px;"></span></section>
</section>
<section style="background:#FFF4ED;border-radius:10px;padding:14px 16px;margin:0 0 24px;">
<p style="margin:0;color:#3d3d3d;font-size:15px;line-height:1.8;">冒烟样本用一份假稿让三个闸门各跑一遍，确认它们能算出结论、不会崩。它不代表任何真实文章的写法，只用来验证装好的脚本是活的。</p>
</section>
<p style="margin:0 0 24px;color:#E8590C;font-size:13px;">#冒烟 #自检</p>
<section style="margin:0 0 30px">
<p style="font-size:16px;font-weight:bold;color:#E8590C;margin:0 0 10px;">第 1 章 冒烟</p>
<p style="color:#3d3d3d;font-size:15px;line-height:1.9;margin:0;">这一段是正文，用来让闸门算一遍行文密度。</p>
</section>
</body></html>
"""

if "--smoke" in sys.argv:
    import shutil
    import subprocess
    import tempfile

    tmp = tempfile.mkdtemp(prefix="wechat-smoke-")
    try:
        s_home = os.path.join(tmp, "wechat")
        s_art = os.path.join(s_home, "output", "冒烟")
        s_cov = os.path.join(s_home, "output", "covers")
        os.makedirs(s_art, exist_ok=True)
        os.makedirs(s_cov, exist_ok=True)
        s_html = os.path.join(s_art, "01_2026-01-01_冒烟测试.html")
        with open(s_html, "w", encoding="utf-8") as f:
            f.write(SMOKE_HTML)
        senv = dict(os.environ, WECHAT_HOME=s_home)

        def smoke_run(script, args, marker, expect):
            r = subprocess.run([sys.executable, script] + args, cwd=sdir, env=senv,
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace")
            out = (r.stdout or "") + (r.stderr or "")
            ok = marker in out and expect in out and "Traceback" not in out
            tail = out.strip().splitlines()[-1][:48] if out.strip() else "无输出"
            return ok, "退出码 %d｜%s" % (r.returncode, tail)

        for script, args, marker, expect, label in [
            ("layout-check.py", [s_html], "结论", "硬错误 0", "冒烟 排版闸门"),
            ("content-check.py", [s_html], "结论", "✅ 通过", "冒烟 内容安检"),
            ("preflight.py", [s_html, "--no-cover"], "预检", "全通过", "冒烟 交付预检"),
        ]:
            ok, detail = smoke_run(script, args, marker, expect)
            ck(label, ok, detail)

        # 第 50 条回归：塞两句典型坏句，闸门必须抓出来。
        # 只拍「能跑出结论」不够，还得拍「该抓的抓得到」——否则规则被改回去也没人知道。
        s_bad = os.path.join(s_art, "02_2026-01-01_冒烟坏句.html")
        with open(s_bad, "w", encoding="utf-8") as f:
            f.write(SMOKE_HTML.replace(
                "这一段是正文，用来让闸门算一遍行文密度。",
                "两套知识库各管一摊。这不是配置问题，而是思路问题。"))
        ok, detail = smoke_run("content-check.py", [s_bad], "对偶拆分", "否定绕弯")
        ck("冒烟 第50条句式", ok, detail)

        # --legacy：旧稿重推开关。失效了等于新规把旧稿全卡死，
        # 而失效往往不报错——只是「结论行还是 ❌」。所以两个都要验：
        # 报告头得写明旧稿模式，结论行得是中危而不是必须改。
        ok, detail = smoke_run("content-check.py", [s_bad, "--legacy"],
                               "旧稿模式", "⚠️ 基本通过")
        ck("冒烟 legacy 开关", ok and "必须改" not in detail, detail)

        # 第 50 条逐条回归：只验「报告里有这一类」不够，某一条正则写坏照样过。
        # 这里把 12 个该报的、2 个不该报的直接喂给检测函数，逐条对。
        try:
            import importlib.util as _iu
            _spec = _iu.spec_from_file_location("_cc_dui", os.path.join(sdir, "content-check.py"))
            _cc = _iu.module_from_spec(_spec)
            _spec.loader.exec_module(_cc)
            hard_cases = [
                "两套知识库各管一摊。", "两条方向，各配各的。", "这件事分两头走。",
                "前者靠这里管理。", "后者是上一篇讲的东西。", "一半人疯了，另一半人在解释。",
                "一头收，一头发。", "一个管脑子，一个管手。", "一边是加法，一边是前提。",
                "这不是配置问题，而是思路问题。", "不仅仅是功能，而是定位。",
                "工具集不是一个名字，是一组打包好的工具。",
            ]
            # 第 45 条指代 / 第 50 条边界：用户定的是「中危」，不许升格成必须改。
            # 单独分组，是防以后把两档合并回去（合并会把正常句子判成 ❌）。
            soft_cases = [
                "把这块配置管住了。", "其实是一回事。", "会话和记忆是两回事。",
            ]
            miss = [s for s in hard_cases + soft_cases if not _cc.check_duiou([s])]
            ok_cases = [
                "标签页能自由拖动，一边看资料一边写特别爽。",
                "你要做两件事，给她定个身份，再发一句话。",
            ]
            false_pos = [s for s in ok_cases if _cc.check_duiou([s])]
            # 分档断言：hard 必须 hard，soft 必须 soft
            wrong_level = []
            for s in hard_cases:
                h = _cc.check_duiou([s])
                if not any((x[4] if len(x) > 4 else "soft") == "hard" for x in h):
                    wrong_level.append("该 hard 却 soft：" + s[:14])
            for s in soft_cases:
                h = _cc.check_duiou([s])
                if any((x[4] if len(x) > 4 else "soft") == "hard" for x in h):
                    wrong_level.append("该 soft 却 hard：" + s[:14])
            ck("冒烟 句式分档", not miss and not false_pos and not wrong_level,
               "漏 %d 条 / 误报 %d 条 / 分档错 %d 条%s" % (
                   len(miss), len(false_pos), len(wrong_level),
                   ("｜" + (miss + false_pos + wrong_level)[0][:30]) if (miss or false_pos or wrong_level) else ""))
        except Exception as _e:
            ck("冒烟 第50条逐条", False, "导入失败：%s" % _e)

        # 裁封面：造一张纯色宽图，看能不能出 900×383
        try:
            from PIL import Image
            src = os.path.join(tmp, "flat.png")
            Image.new("RGB", (1280, 640), (30, 30, 30)).save(src)
            dst = os.path.join(s_cov, "01_冒烟.png")
            r = subprocess.run([sys.executable, "crop_cover.py", src, dst], cwd=sdir,
                               capture_output=True, text=True, encoding="utf-8")
            size = Image.open(dst).size if os.path.isfile(dst) else None
            ck("冒烟 裁封面", size == (900, 383),
               "输出 %s×%s" % size if size else "没生成文件｜" + (r.stderr or "")[-50:])
        except ImportError:
            ck("冒烟 裁封面", False, "Pillow 没装，跳过", soft=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

# 输出
bad = [r for r in rows if not r[1] and not r[3]]
warn = [r for r in rows if not r[1] and r[3]]


def _width(s):
    """按终端显示宽度算，中文占两格。"""
    import unicodedata
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def _pad(s, n):
    return s + " " * max(0, n - _width(s))


w = max(_width(r[0]) for r in rows)

print("=" * 70)
print("wechat-article 自检")
print("  技能目录   %s" % SKILL)
print("  WECHAT_HOME %s" % HOME)
print("=" * 70)
for name, ok, detail, soft in rows:
    mark = "✅" if ok else ("⚠️ " if soft else "❌")
    print("  %s %s %s" % (mark, _pad(name, w), detail))
print("-" * 70)

if bad:
    print("❌ %d 项必须修" % len(bad))
    print()
    print("补齐依赖（装在挂载卷里，容器重启不丢）：")
    print("  pip install --target %s/pylibs Pillow openpyxl" % HOME)
    print("  # 然后在 compose 的 environment 里加 PYTHONPATH=%s/pylibs" % HOME)
else:
    print("✅ 必须项全过，可以用了")
    if warn:
        print("⚠️  上面 %d 项是提示，不影响写稿排版" % len(warn))
    print()
    print("Key 不在本检查范围。封面生成不了时先查 agnes 的密钥来源：")
    print("  python3 %s --history 3" % os.path.join(os.path.dirname(agnes), "agnes_common.py"))

sys.exit(2 if bad else 0)
