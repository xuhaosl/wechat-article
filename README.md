# wechat-article

把一份素材写成公众号长文，一路做到能直接粘进编辑器的 HTML。

支持 Hermes Agent（原生安装或 Docker Compose 部署）。除 `Pillow` 与 `openpyxl` 之外全是标准库。

## 能做什么

| 阶段 | 做什么 |
| --- | --- |
| 写稿 | 从素材出发，先定这篇的知识点再动笔；50 条禁区按「什么时候翻」分七组，写完过一遍 |
| 排版 | 排成公众号认的 HTML：导读卡、关键词药丸、堆叠卡片、图注、代码块 |
| 安检 | 脚本查九类，人眼查五项，分工写在 `references/content-check.md` |
| 封面 | 21:9 底图裁成 900×383；文字由生图模型直接画进图里 |
| 跟踪 | 扫产物目录生成跟踪表，只记录产出了什么 |

## 快速开始

本仓库的根目录**就是这个 skill 本体**。先克隆，再拷进宿主应用的 skill 目录：

```bash
git clone https://github.com/xuhaosl/wechat-article.git

# Hermes Agent
cp -r wechat-article ~/.hermes/skills/wechat/
```

分类层可省，直接放 `~/.hermes/skills/wechat-article/` 也认。

两个第三方包都要装，`selftest.py` 会把缺的算作失败：

```bash
pip install Pillow openpyxl
```

产出根目录默认 `/opt/data/wechat`（容器里的持久卷）。不在容器里跑就先设一下：

```bash
export WECHAT_HOME=/你的目录
```

装完先跑自检，它会验依赖、8 个脚本、18 份 references 齐不齐、产出目录写不写得进去：

```bash
python3 scripts/selftest.py --smoke
```

`--smoke` 会拿一份内置假稿真跑一遍三个闸门，再造一张纯色图跑裁封面。全程在临时目录里，不调 API、不耗额度，跑完自动删。**它只证明脚本是活的，不证明任何真实稿子合格。**

然后直接用：

```bash
hermes chat -s wechat-article --oneshot -q "按这份素材写一篇"
```

## 包结构

```
wechat-article/
├── README.md                       ← 你在看的东西
├── LICENSE                         ← MIT
├── SKILL.md                        ← 主文件：13 步流程、禁区索引、闸门用法、交付清单
├── references/
│   ├── bans-1-opening.md           # 禁区 8 9 12 24 33 36 43 46 48：开场与导语
│   ├── bans-2-title.md             # 禁区 19 34 42 44：标题
│   ├── bans-3-source.md            # 禁区 5 6 7 21 22 25 26 29 49：信源与素材
│   ├── bans-4-sentence.md          # 禁区 1 3 4 15 23 31 38 40 45 50：句式与用词
│   ├── bans-5-structure.md         # 禁区 2 10 11 13 14 16 17 27 28 30 39：结构与节奏
│   ├── bans-6-voice.md             # 禁区 20 32 35 37 41：人称与定位
│   ├── bans-7-process.md           # 禁区 18 47：流程与自检
│   ├── techniques.md               # 18 条技法 + 6 条进池导向
│   ├── title-playbook.md           # 五套路、六维、17 条硬规律
│   ├── vocab.md                    # 说明书词汇换画面词
│   ├── ai-patterns.md              # 24 种 AI 腔逐条对
│   ├── ai-smell.md                 # 总纲与六病灶，正反例
│   ├── checklist.md                # 24 项排版清单、标题区与章节衔接写法
│   ├── compatibility-rules.md      # 公众号兼容性规则、组件写法
│   ├── style-guide.md              # 配色、卡片、代码块、页面干净度
│   ├── forbidden-words.md          # 违禁词表
│   ├── content-check.md            # 安检全流程：脚本九类 + 人眼五项
│   └── cover.md                    # 封面规范与七步流程
└── scripts/
    ├── preflight.py                # 交付前统一预检：四项串成一条结论
    ├── layout-check.py             # 排版硬闸门（字号、间距、并排、串行、表格）
    ├── content-check.py            # 内容安检九类，逐处给位置和上下文
    ├── fact-diff.py                # 改稿前后事实对账：命令、版本号、数字有没有掉
    ├── crop_cover.py               # 裁封面：任意比例 → 2.35:1，900×383
    ├── add_brand_icons.py          # 叠品牌图标（可选）
    ├── build-tracking.py           # 扫产物目录，重建产出跟踪表
    └── selftest.py                 # 装完自检，--smoke 真跑一遍
```

## 闸门与退出码

**`preflight.py` 是唯一要看的结论**，另外两个是明细。

| 脚本 | 做什么 | 0 | 1 | 2 |
| --- | --- | --- | --- | --- |
| `preflight.py` | 排版 + 命名 + 安检 + 封面，一次跑完 | 可发 | 看一眼 | 不能发 |
| `layout-check.py` | 只查排版 | 过 | 只有警告 | 有硬错误 |
| `content-check.py` | 只查内容 | 无高危 | 有高危 | 文件读不了 |

### 句式分两档

| 档 | 含什么 | 怎么办 |
| --- | --- | --- |
| 必须改 | 把一件事劈成两半再对仗（各管一摊、分两头、前者后者、一半另一半）、`不是 A 而是 B`、`不是 A，是 B` | 一处不留，预检结论行写「改完再发」 |
| 中危 | 含糊指代（这块、那类、另一种）、`是两回事` | 按语境判，可以不改 |

两档合并过一次，代价是正常句子被判错——`另一种做法是先备份` 这种写法会被判成必须改。`selftest.py` 里留了一条「该 soft 却 hard」的反向断言，合并回去会报分档错。

旧稿重推（正文不想动）加 `--legacy`，句式降为提示：

```bash
python3 scripts/preflight.py <文章.html> --legacy
```

新写的稿别加这个开关。

## 设计要点

**唯一真相源是 `.html`。** 写稿中间可以落 md 当草稿，但 html 一出来那份 md 就删掉，不留在产物目录里，也不拿它对账。留两份就要同步两份，漂移是自己造出来的。

**机器能判的和人判的分开写。** 脚本管有确定性答案的部分，人管语义。`content-check.py` 的九类都在文档里逐条对应，加检测项就同一步改脚本、改文档、改自检，三处一起。

**加检测项只认「造一个该被拦的样本，看它出不出得来」。** 读代码不算数——文档写着禁、函数也在，正则少写一半的情况真实发生过，全库曾积到几十处没被拦。所以每类检测在 `selftest.py` 里都有一条坏样本，跑 `--smoke` 会真喂进去。

**同一条判据只留一处。** 两套判据并存时，旧的先执行，新的等于没写。`--legacy` 第一版就是这么失效的。

**封面文字由生图模型画。** 容器里不需要装中文字体；只有自己叠品牌图标时才用得上 `add_brand_icons.py`。

**素材薄可以加，素材厚更不该加。** 具体到这篇要不要补内容、补什么，看素材本身，不看篇幅。

## 已验证

`python3 scripts/selftest.py --smoke` 七项全过，可以自己复现：

| 项 | 验什么 |
| --- | --- |
| 排版闸门 | 内置假稿过 `layout-check.py`，断言看到结论行 |
| 内容安检 | 过 `content-check.py`，断言看到结论行 |
| 交付预检 | 过 `preflight.py`，四项串起来不出错 |
| 第 50 条句式 | 喂坏句必须被抓到 |
| legacy 开关 | 同一份旧稿，降级后不许再判「必须改」 |
| 句式分档 | 12 条该报 + 2 条该过，漏报误报分档错各自计数 |
| 裁封面 | 造纯色图，输出 900×383 |

另外四条是硬失败项：两个第三方依赖、8 个脚本、18 份 references 齐不齐、产出目录写不写得进去。

## 做不到的

四条边界写在 `SKILL.md` 里，这里重申，免得误会：

- **发布不在这个 skill 里。** 个人订阅号只能手动扫码发，那一步在你自己的电脑上。
- **事实真假靠人。** 数据有没有出处、版本号对不对，脚本判不了。`fact-diff.py` 只能告诉你改稿前后哪些事实项消失了或多出来了。
- **标点靠人眼。** 冒号、破折号、双引号三个脚本都不查——URL、时间、代码块里的冒号例外太多，机械查必然误报。
- **封面底图要自己出。** 配合 [`agnes-multimodal`](https://github.com/xuhaosl/agnes-multimodal) 出 21:9 底图，或自备一张同比例的图再裁。

## License

MIT
