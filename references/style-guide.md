# 公众号文章设计风格指南

## 整体风格
- 浅色主题
- **每篇文章选定一个主题色，全篇统一使用**（跨文章可不同，单篇内不换色）
- 整体轻松、灵动
- 正文行距 1.9，阅读松弛

## 文章主题色方案（v2：全篇一色）

**每篇文章开始时选定 1 个主题色**，整篇文章的章节标题、行内代码、分隔线、卡片边框全部使用这个颜色（及它的浅色背景变体）。**单篇文章内禁止换色**——章节之间用背景卡片 + emoji 区分，不靠颜色跳变。

### 可选主题色池（文章开头任选其一）

| 主题色 | 色值（主色） | 浅色背景 | emoji 示例 |
|--------|-------------|---------|-----------|
| 靛蓝 | `#6366F1` | `#EEF2FF` | 🤖 |
| 紫色 | `#8B5CF6` | `#F5F3FF` | 🚀 |
| 蓝色 | `#3B82F6` | `#EFF6FF` | 📦 |
| 青色 | `#14B8A6` | `#F0FDFA` | ✅ |
| 绿色 | `#10B981` | `#ECFDF5` | 🔑 |
| 琥珀 | `#F59E0B` | `#FFFBEB` | ⚙️ |
| 珊瑚 | `#FB7185` | `#FFF1F2` | 🌐 |

**选择原则**：根据文章主题情绪选色（教程→蓝/青，前沿→紫，工具→琥珀，安全→绿），一篇文章固定一个，不中途换。

### 全篇统一用色规则

选定主题色后，全篇所有元素都从下面这个"一色体系"取色：

| 元素 | 颜色 | 说明 |
|------|------|------|
| 章节标题文字 | 主题色 | `<h2>` 用主题色 |
| 章节标题背景 | 主题色浅色变体 | 圆角卡片背景 |
| 行内代码背景 | 主题色浅色变体 | 命令/路径高亮 |
| 行内代码文字 | 主题色深色变体 | 比主色更深的同色系 |
| 分隔线 | 主题色 | 4px 圆角线 |
| 卡片边框/投影 | 主题色 rgba | 半透明投影 |
| 正文 | 深灰 `#3d3d3d` | **全篇唯一正文灰**——禁 `#475569`／`#4b5563`／`#666`／`#888` 混用（肉眼几乎看不出差别，但会让整页灰度不匀） |
| 副标题/次要文字 | 灰 `#999` | 与图注统一，不再使用 `#666`／`#888` |
| 图注 | 灰 `#999` | 不变 |

### 提示卡：语义靠竖条，不靠底色（2026-09-16 改）

三种提示（⚠️警告／💡提示／✅要点）**统一用主题色最浅底**，语义只靠左侧 3px 竖条的**颜色**区分：

| 语义 | 竖条色 | 文字色 | 底色 |
|------|--------|--------|------|
| ⚠️ 警告/踩坑 | 琥珀 `#B45309` | 正文灰 `#3d3d3d` | 主题最浅底 |
| 💡 提示 | 主题色 | 正文灰 `#3d3d3d` | 主题最浅底 |
| ✅ 要点 | 主题色 | 正文灰 `#3d3d3d` | 主题最浅底 |

```html
<!-- 提示卡统一模板（只换竖条色 = 换语义） -->
<section style="background:#F0FDFA;border-left:3px solid #B45309;border-radius:0 8px 8px 0;padding:11px 14px;margin:0 0 16px;">
<p style="margin:0;color:#3d3d3d;font-size:14.5px;line-height:1.85;">⚠️ 提示内容</p>
</section>
```

**唯一例外**：警示卡允许保留琥珀底 `#FFFBEB`（警告要跳出来），但**全篇 ≤2 处**。

**为什么改**（2026-09-16 实测）：底色是最重的视觉信号。一篇里同时出现青/蓝/绿三种浅底，明度接近、色相乱跳，整页就是"花"的——WB13 一篇 4 种浅底并存是典型。爆款实测只用 1 种浅底走完全篇（Pi 04 的 `#F0FDFA` 出现 17 次、隧道篇的 `#EFF6FF` 出现 44 次），语义靠形态和竖条区分，不靠换色。

> 一篇文章的用色总账：**主题色 1 + 主题最浅底 1 + 警示琥珀（≤2 处）+ 灰阶 3** ≈ 6 种色值封顶。

## 页面干净度六条（2026-09-16 新增 · 用户定）

底色比字号、emoji 都更重。下面六条是硬规则，出稿前用 `scripts/layout-check.py` 自动跑。

**1. 浅色底收敛到 1 种**（脚本红线：>3 种报警）。全篇卡片、色块、章节条统一用主题色最浅底；唯一例外是警示卡琥珀底（全篇 ≤2 处）。
> 依据：爆款 Pi 04 只有 2 种浅底（`#F0FDFA` 用了 17 次 + 警示 `#FFFBEB` 2 次），隧道篇 3 种；WB13 和 Hermes 04 各 4 种（青/蓝/绿/琥珀并存）——明度接近、色相乱跳，"花"就是这么来的。脚本红线定在 3 种是为了不对爆款误报。

**2. 功能语义走竖条，不走底色。** 见上节「提示卡」。

**3. 正文灰只许一种。** `#3d3d3d` 是唯一正文灰；次要文字只用 `#999`。
> 依据：Hermes 04 同时用了 `#3d3d3d`（42 次）和 `#475569`（14 次）两种正文灰，肉眼几乎分不出，但整页灰度不匀。

**4. 分隔线一律居中短线。** 满宽 4px 粗线全部淘汰，见「标题区视觉结构」。

**5. 禁卡片套卡片。** 带背景的容器里不再套第二个带背景的容器（代码块的深底 + 标题栏除外）；内层改裸文字，或拆成并列卡。
> 这条我原本写的是"限色块容器数量（≤1 个 / 200 字）"，**数据不支持**——爆款 Pi 04 每 144 字就一个色块、隧道篇每 108 字一个，比现状 WB13（每 169 字一个）还密。**块多不是问题，颜色杂才是。**

**6. 卡片／小节标题 ≤14px。** 不许 16px 以上、不许纯黑加粗，见「章节结构」三条硬规则。

> **emoji 不受这六条约束**：实测 emoji 密度与阅读量没有单调关系（隧道篇 22 个 emoji、Pi 04 只有 8 个，都是最高阅读），所以不设上限，只要求"别在连续两句里堆"。真正跟"花不花"强相关的是上面这几条底色/色值指标。

## 标题区视觉结构

文章开头要有强视觉冲击力，包含三层元素：大 emoji 图标 + h1 标题 + 副标题 + 彩色分隔线。

```html
<section style="text-align:center;padding:20px 0 8px;">
<p style="font-size:36px;margin:0 0 8px;">🤖</p>
<h1 style="font-size:22px;font-weight:bold;color:#3d3d3d;margin:0 0 6px;">文章主标题</h1>
<p style="font-size:13px;color:#999;margin:0;">副标题 / 一句话简介</p>
</section>
<!-- 居中短线，不做满宽；容器必须 font-size:0 + line-height:0，否则空行盒撑出 28px -->
<section style="text-align:center;margin:0 0 14px;font-size:0;line-height:0;">
<span style="display:inline-block;width:60px;height:3px;background:#6366F1;border-radius:2px;"></span>
</section>
```

要点：
- emoji 图标 36px，居中，紧贴标题上方
- h1 标题 22px，深灰色
- 副标题 13px，`#999`，**不超过 15 字**，`margin:0`（不要再留 16px）
- **分隔线必须是居中短细线**：`60 × 3px`，包在 `text-align:center` 的容器里，靠 `display:inline-block` 撑宽度。
  ⚠️ 2026-09-16 改：**禁满宽 4px 粗线**（`height:4px;background:...;margin:0 0 22px` 那种）。满宽粗线在手机上是一道横贯屏幕的杠，视觉重量跟章节标题条相当，等于两个锚点在抢读者注意力。爆款 Pi 04 用的就是居中 60×3 短线。
- **标题区 → 导读卡的留白合计 ≤30px**（2026-09-17 用户定，Hermes 06 从 54px 压到 22px）。
  手机上第一屏最金贵，标题和导语之间空一大块，等于把读者往外推。三处一起调：
  | 位置 | 旧 | 新 |
  | :-- | :-- | :-- |
  | 标题区 `padding` 下值 | 16px | 8px |
  | 副标题 `margin-bottom` | 16px | 0 |
  | 分隔线容器 `margin-bottom` | 22px | 14px |
  另外分隔线容器**必须写 `font-size:0;line-height:0`**——里面只有 3px 高的 `inline-block`，
  容器却按 15px×1.9 撑出 28.5px 的行盒，白占 25px。`layout-check.py` I4 项自动量。

## 标题长度（2026-09-17 新增 · 硬约束）

| 口径 | 上限 | 说明 |
| :-- | :-- | :-- |
| 字符数（主口径） | **17 字符** | 中文字、中文标点、英文字母、数字各计 1 |
| 显示宽度（辅口径） | **15 宽** | 中文/全角 1，英文字母·数字·半角 0.5 |

基准样本（用户亲手改定）：**《又从头讲一遍？Hermes替你记住》= 17 字符 / 14 宽**——手机上标题刚好一行放得下。

为什么还要辅口径：22px 字号在手机上约 340px 宽，一行只放得下约 15 个中文字。中文字宽是英文的两倍，
所以「纯中文 17 字」（17 宽）会折行，而「11 汉字 + 6 字母」（14 宽）不会。**字符数没超但宽度超了，照样折行。**

超出即折行，第一屏标题变成两行参差的字块，观感立刻变乱。`layout-check.py` I1 项自动量，
字符数超 = 硬错误，宽度超 = 警告。

## 导读卡（标题区唯一的前置模块 · 2026-09-16 结构变更）

**「导读段 + 目录框」两段式废止**：标题区下方**只放一个导读卡**（色块），然后**直接进入正文第 1 章**——不许再有目录框、系列介绍段、"上一篇我们聊了…"钩子卡、任何中间模块。

理由（用户实测纠正）：读者点进来是为了拿东西，第一屏却先给他看目录和引子，人还没拿到东西就走了。爆款对照——Pi 04 / 隧道篇 / Pi 02 的第 1 章就是正题；Hermes 组把正题推到第 2 章（第 1 章在讲「NAS 一直开着」「模型才烧钱」这类读者早就知道的道理），5 篇推荐全部 <194。

```html
<!-- 导读卡（必须色块，不许裸 p） -->
<section style="background:#F0FDFA;border-radius:12px;padding:15px 17px;margin:0 0 18px;">
<p style="margin:0;font-size:15px;color:#374151;line-height:1.85;">导读内容：这篇要解决读者的什么问题（痛点）。</p>
</section>
```

导读卡要点：
- **必须色块卡片，不许裸 `<p>`**。无背景的裸段在手机上看起来跟正文一模一样，读者分不清「这是铺垫还是内容」，190 字裸段就是一堵墙（Hermes 01 踩过；Pi 04 当年是卡片，09-12 后退化成裸段）
- **目标 40-150 字**，2-4 句（爆款实测：Pi 04 = 140 字、Pi 02 = 110 字、WB13 = 88 字、Hermes 08 = 96 字；**红线 200 字**，Hermes 01 的 280 字是反例）。`layout-check.py` H 项自动量
- **必须「场景开场」，禁泛论定性开场**（2026-09-16 Hermes 06 定稿新增）：第一句要给读者一个他亲历过的画面，第二句落到具体损失，末句说明这篇给什么。对比——被否版「AI 助手最大的毛病是没记性。聊了半个月，它还是不认识你…」＝先讲道理，读者没有代入感；改后「你上周跟它说过，回复别写那么长。今天开个新对话，它照样给你三大段。每个新窗口都像初次见面，背景得从头交代。」＝画面先行，读者自己就认领了。**自检：第一句里有没有一个「我经历过」的具体动作？**
- **必须带读者痛点 + 结尾一句「这篇给什么」**。参考爆款：Pi 04 导读「你让 AI 重构一个模块…等它跑完这一轮得重来。按 Ctrl+C 打断，前面的活白干。Pi 给了第三种选择…这篇把 steering 和 follow-up 两条路一次讲清」
- **末句「这篇给什么」不许写成「先讲 X，再讲 Y」的目录式枚举**（2026-09-18 用户定，Hermes 08 实例）：我在重排章序后把末句写成「这篇先讲她的能力该按什么顺序往上加，再讲项目规则放在哪、四个文件谁优先、里面该写什么」，用户回「导语也要调整」——这跟被废止的目录框是同一个毛病，只是没画框。**改法：把「给什么」压成一句正常的话收口**，如「她的能力该按什么顺序往上加，这份规矩又该放在哪、写什么，这篇一次说清」。自检：末句念出来像不像在报章节目录？
- **一个场景就够，别堆同类画面；痛点要落到根因**（2026-09-18 用户定，Hermes 08 二次退回）：前三句都在说同一件事的不同表现，那不叫丰富，叫啰嗦——读者读完第一句就已经认领了，第二例只是拖长。
  - **被否版（128 字）**：「你在一个新项目文件夹里让她改配置，她先把目录结构猜错，还顺手动了你没让她动的文件。回头问你想要什么风格，你已经把要求说过三遍。换个项目就要重讲一遍规矩，这事不怪她，你从没把规矩写成文件。…」——前两句都是「她不听话」的同类画面。
  - **正向形态 = 一个画面 + 一句损失 + 一句根因 + 一句给什么**（96 字，已采用）：
    ```html
    <p style="margin:0;font-size:15px;color:#3d3d3d;line-height:1.85;text-align:justify;">新起一个项目让她改配置，她上来就把目录猜错，还动了你没让她动的文件。你解释一遍，换个项目又得重来。她手里只有一份全局设定，没有一条规矩是写给这个项目的。这篇讲那份规矩到底该放在哪、里面写什么。</p>
    ```
  - 关键在**第三句**：痛点从「她不听话」推进到「**为什么她做不到**」（她手里只有全局设定），这才是痛点；停在抱怨层就只是举例子。
  - **自检两句**：①三句里有没有两句在说同一件事？②有没有一句回答了「她为什么会这样」？
- **痛点的排列顺序必须与正文章序一致**（2026-09-18 用户定，Hermes 08 第三次调整）：导语是正文的缩影，读者是**顺着导语的顺序**往下读的；章序一改，导语必须跟着改。
  - 实例：「顺序别搞反」由压轴前移为第 1 章后，导语还停在旧顺序（先说项目里乱来、后讲顺序）→ 用户指出应「**先写装完 Agent 第一步不知道干什么（对应 01），再简写结果与自己想要的大相径庭（对应规则文件）**」
  - 结构 = **第 1 章的痛（一句）→ 后续章节的痛（一句，含根因）→ 给什么（一句）**（89 字，已采用）：
    ```html
    <p style="margin:0;font-size:15px;color:#3d3d3d;line-height:1.85;text-align:justify;">Agent 装好之后该先干什么，你不知道，她就在那儿闲着。真让她上手，结果又跟你想的差很远，因为她根本不认识你这个项目。这篇讲她的能力该按什么顺序往上加，和那条项目规矩该立在哪。</p>
    ```
  - ⚠️ 顺序对齐之后**还要回头查与第 1 章的重复**：本篇第 1 章开场是「逛一圈 Skill 市场一口气装十几个，再接一堆 MCP 回来」，所以导语第一句不能也写「跟着装技能、接 MCP」，只能从「装完不知道先干什么、她就那么闲着」这一侧切进去
- **⚠️ 例外：机制型主题不造痛点，钩子换成「信息缺口」**（2026-09-21 用户定，Hermes 10 实例）：
  - **适用**：素材通篇是「有哪些东西、怎么分类、在哪儿开关」这类**纯机制说明**，没有天然痛感画面。硬套痛点会写出**不成立的因果链**。
  - **被否版**：「你让她查个工具的用法，她打开浏览器、写了个脚本，顺手还改了配置。你只是想问一句话。她默认背着十几套工具，能读文件、能执行命令的那些，一直是开着的。」用户读后反问：「这有什么问题么？」——**工具开着只让她「能」做，本身不构成问题**，「默认全开」是合理的出厂默认。
  - **正向形态 ＝ 信息缺口（点名「你」）＋ 现状 ＋ 给什么**（61 字，已采用）：
    ```html
    <p style="margin:0;font-size:15px;color:#3d3d3d;line-height:1.85;text-align:justify;">她自带的四十多种工具，你可能一次都没打开看过。分门别类打好了包，默认基本都开着。这份清单和管着它的四层开关，这篇一次说清。</p>
    ```
  - 区别只在**主语**：「她默认都开着」（危险暗示）vs「你可能没打开看过」（信息缺口）。
  - ⚠️ 首句**仍须出现「你」**——`layout-check.py` H 项会警告「导读卡首句里没有你」，机制型也不例外，只是把「危险」换成「你不知道」。
  - ⚠️ 改了导读卡，**开场第一句和结尾回扣必须一起改**（Hermes 10 结尾：「回头看这张表…现在你看过了。／以后要收窄哪一层，从粗到细四层，挑一层下手就行。」）
- **内容 = 这篇文章要解决读者的什么问题（痛点）**。不写「本文介绍了…」，不写系列回顾，不写「我」的处境自述
- **不许与第 1 章重复**。反例：WB13 导读写「真正烧钱的从来不是工具本身，是模型」，第 1 章标题就叫「模型才是烧钱的地方」，首段又是「工具可以不花钱，模型不行」——同一个意思说了三遍
- 背景用文章主题色的最浅变体，文字深灰

关键词标签紧随导读卡之后（位置固定），组件样式见下节「关键词标签」。

### 目录模块（2026-09-16 起废止）

历史文章里的目录框（纯文字版 / 圆形数字徽标版）不再生成。已发布的不回改；新文章一律「标题区 → 导读卡 → 第 1 章」三段直落。

原徽标版模板的坑仍值得记着（万一将来恢复）：一项必须一个 `<section>`、文字 span 禁设百分比宽度、禁用 `flex`+`gap`。

## 关键词标签

每篇文章**导读卡**下方必须有 3-5 个关键词标签，帮助读者快速识别文章主题和平台推荐算法抓取。

```html
<!-- 关键词标签 -->
<section style="margin:0 0 16px;">
<p style="margin:0;font-size:0;line-height:1.6;">
<span style="display:inline-block;background:#EEF2FF;color:#6366F1;padding:2px 10px;border-radius:12px;font-size:12px;margin:0 6px 6px 0;line-height:1.6;">#WorkBuddy</span>
<span style="display:inline-block;background:#EEF2FF;color:#6366F1;padding:2px 10px;border-radius:12px;font-size:12px;margin:0 6px 6px 0;line-height:1.6;">#CodeX</span>
<span style="display:inline-block;background:#EEF2FF;color:#6366F1;padding:2px 10px;border-radius:12px;font-size:12px;margin:0 6px 6px 0;line-height:1.6;">#AI工具</span>
</p>
</section>
```

要点：
- 关键词由技能根据文章内容**自动总结**，无需用户手动指定
- 每次生成 **3-5 个**标签，中文或英文关键词均可，`#` 开头
- 标签主色使用文章**主题色的浅色变体背景 + 深色变体文字**
- 药丸形状（`border-radius:12px`），小字号（12px），轻量不抢眼
- 容器 `font-size:0` 消除空白间隙，子元素显式恢复 `font-size:12px`
- 位置固定在导读卡之后；**导读卡之后直接进第 1 章**，中间不许再有任何模块

## 章节结构（2026-09-16 重做 · 解决「目录撤掉后章节感消失」）

目录已于 2026-09-16 废止，读者失去了"全文有几节、现在在哪"的地图。**章节标题从此要独自承担导航职责**，所以必须做出明确的块级边界。

### 三条硬规则（与版式选择无关，一律执行）

1. **每章必须用一个 `<section>` 包住**，容器 `margin:0 0 30px`。章末留白 + 章首留白 + 容器外边距三层叠加，章与章之间才有"块"的边界。裸标题直接插在正文流里 = 章节感消失（Hermes 04 的坑：6 个 h2 平铺，只有一层 30px 空档）。
2. **全篇只允许一种章节标题形态**。禁止同一篇里混用「色块标题」和「纯文字加粗标题」——Hermes 04 混了三套（6 个 h2 色块 + 3 处 18px 加粗 `●` + 1 处 16px 纯黑标题），读者扫过去分不清哪个是章节。
3. **层级必须拉开**：章节标题 17-18px；**卡片／小节标题一律 ≤14px**，禁止 16px 以上、禁止纯黑 `#1a1a1a` 加粗出现在章节层。字号混淆是"看着乱"的第一来源。

### 章节标题形态（满宽标题条 + 左竖条 + 序号）

下面的橙色（`#FFF4ED` / `#E8590C` / `#8A2E00`）只是示例，**三处颜色一律换成本篇选定的主题色及其浅色、深色变体**（主题色池见上文）。这套形态对任何主题通用，不绑橙色。

```html
<section style="margin:0 0 30px;">
  <!-- 章节标题条 -->
  <section style="background:#FFF4ED;border-left:4px solid #E8590C;border-radius:0 10px 10px 0;padding:10px 14px;margin:0 0 15px;">
    <p style="margin:0;font-size:0;">
      <span style="display:inline-block;font-size:12px;font-weight:700;color:#E8590C;letter-spacing:1.5px;margin-right:9px;vertical-align:middle;">01</span>
      <span style="font-size:17px;font-weight:700;color:#8A2E00;vertical-align:middle;">章节标题</span>
    </p>
  </section>
  <!-- 本章正文 -->
  <p style="margin:0 0 14px;font-size:15px;color:#3d3d3d;line-height:1.9;">正文…</p>
</section>
```

要点：
- **满宽**：标题条禁止左右加 margin（写成 `margin:0 0 15px`），必须与正文左右边界严格对齐
- 左侧 4px 竖条 = "新一章从这里开始"的信号，比 22px 的徽标显眼
- 序号 `01` 用 12px + `letter-spacing:1.5px`，小字靠左，保留"第几节"的位置感，替代目录的导航作用
- 标题文字用**主题色的深色变体**（如橙 `#E8590C` → 深 `#8A2E00`；青 `#14B8A6` → 深 `#0F766E`），与卡片标题（直接用主题色）拉开
- 背景用主题色的最浅暖变体（橙系 `#FFF4ED`）
- 序号和标题在**同一个 `<p style="font-size:0">`** 里靠 `vertical-align:middle` 对齐；**禁 flex + gap**（微信不兼容）

### 二级标题（小节 / 卡片内标题）
纯文字 + 主题色，无背景，**最大 14px**（比正文 15px 还小一档，靠加粗和颜色区分，绝不靠字号）。

```html
<p style="font-size:14px;font-weight:700;color:#8B5CF6;margin:18px 0 8px;">安装要准备什么</p>
```

## 配图图注

每张配图下方加居中灰色说明文字，帮助读者理解图片内容。box-shadow 颜色用文章主题色的 rgba 形式。

```html
<img src="URL" alt="说明" style="width:100%;max-width:480px;border-radius:12px;margin:0 auto 6px;display:block;box-shadow:0 4px 16px rgba(99,102,241,0.12);" />
<p style="text-align:center;color:#999;font-size:12.5px;margin:0 0 16px;">图片说明文字 🔧</p>
```

要点：
- 图注 12.5px，灰色 `#999`，居中
- **图注 ≤15 字**（2026-09-17 用户定）。去掉 `▲` 和 emoji 后计数。
  图注长了在手机上会折成两三行小灰字，比图本身还抢眼。反例（Hermes 06 原版）：
  「▲ 终端里列出来的历史会话，每条带时间和来源，这就是第三层兜底 📜」29 字 → 三行；
  改后「▲ 历史会话带时间和来源」10 字 → 一行收住。`layout-check.py` I2 项自动量
- **图注末尾不再加 emoji**（emoji 占宽还打断短句节奏，图注只留一个 `▲` 前缀）
- box-shadow 用文章主题色的半透明 rgba（如靛蓝 `rgba(99,102,241,0.12)`），比纯黑投影更柔和

## 对比内容（禁并排双卡 · 2026-09-17 改）

**A vs B 这类对比，一律「上下堆叠的单栏卡」，禁左右并排。**

原先写的「对比型表格 → 并排两张卡片」作废。实测在手机上两栏各只有约 150px 宽，
中文一行放 6-7 个字就换行，卡片被拉成两根细柱，比单栏还难读。

```html
<!-- ✅ 单栏堆叠 + 逐项竖排：两项一组，卡内一项一个 <p>，行首 4px 主题色圆点 -->
<section style="background:#FFF4ED;border-radius:10px;padding:12px 14px;margin:0 0 8px;">
<p style="margin:0 0 8px;font-weight:bold;color:#E8590C;font-size:14px;">✅ 会主动存</p>
<p style="margin:0 0 4px;color:#3d3d3d;font-size:14px;line-height:1.55;"><span style="display:inline-block;width:4px;height:4px;background:#E8590C;border-radius:50%;margin-right:8px;vertical-align:2px;"></span>用户偏好</p>
<p style="margin:0 0 4px;color:#3d3d3d;font-size:14px;line-height:1.55;"><span style="display:inline-block;width:4px;height:4px;background:#E8590C;border-radius:50%;margin-right:8px;vertical-align:2px;"></span>环境事实</p>
<p style="margin:0;color:#3d3d3d;font-size:14px;line-height:1.55;"><span style="display:inline-block;width:4px;height:4px;background:#E8590C;border-radius:50%;margin-right:8px;vertical-align:2px;"></span>纠正与约定</p>
</section>
```

**两项铁律，缺一不可**：

① **不并排**（禁 `inline-block` ＋ 半宽 40~60% 的两栏，`<section>` 还是 `<span>` 都算）
② **不串行**（禁「用户偏好 · 环境事实 · 纠正与约定 · 已完成的工作 · 你明确要求记的」压在同一个 `<p>` 里）

第 ② 条是 2026-09-17 用户二次纠正的：**并列清单必须一项一行**。压成一行用 ` · ` 串联，
看起来像一句长话而不是清单，读者扫不出有几项、也记不住，清单的价值就没了。

- 卡内行距用 `line-height:1.55`（比正文 1.9 紧），配 `margin:0 0 4px` 让 5 项竖排也不松散
- 行首统一 4px 主题色圆点（`inline-block` + `border-radius:50%` + `vertical-align:2px`），比 `·` 更像清单
- `layout-check.py` I3 项抓并排双卡，I5 项抓「同一段里 ≥2 个 ` · ` 串联的伪清单」

## 行内代码（inline code）高亮

所有正文中的文件名、命令、路径、界面菜单路径等，统一用彩色背景圆角标签高亮，不要有的有样式有的没有。

```html
<span style="background:#EEF2FF;color:#6366F1;padding:1px 6px;border-radius:4px;font-size:14px;font-family:'Cascadia Code','Fira Code',Consolas,monospace;">npm -v</span>
```

要点：
- 背景用文章主题色的浅色变体，文字用主题色深色变体
- 字号 14px（比正文 15px 略小），等宽字体
- 圆角 4px，padding `1px 6px`
- **必须覆盖**：命令、文件名、路径、配置项名、界面菜单路径（如「设置 > 路由 > 安全」）

## 正文 emoji 穿插

emoji 不要只在标题和提示框里出现，正文中也要穿插使用，保持轻松灵动风格。

示例：
- 段落开头：「📥 接下来我们来安装……」
- 段落中间：「打开终端 📱 输入以下命令」
- 段落结尾：「详见下一节 👇」
- 列表项：「✅ 已完成」「❌ 不支持」

原则：
- 每隔 2-3 段穿插一个 emoji，不要密集
- emoji 与文字之间留一个空格
- 选择与内容相关的 emoji（安装用 📦/📥，配置用 ⚙️，安全用 🔑，网络用 🌐 等）

## 章节过渡语

每个章节末尾加 1-2 句过渡语，自然引出下一章，避免章节衔接生硬。

示例：
- 「接下来就带你从零配置终端环境 🛠️」
- 「模型配置完成后，就可以开始使用了。不过在此之前，还有一个常见问题需要解决 👇」
- 「安装完成后，下一步就是配置模型了 ⚙️」

过渡语用正文段落样式，放在章节最后一段，末尾带 emoji 引导。

## 代码块（完整模板）

代码块 = 深色容器 + macOS 三圆点标题栏 + `pre`。**三圆点必须用 `inline-block` + `margin-right` 排列，禁止 `display:flex` + `gap`**（微信内置浏览器不兼容）。父级加 `font-size:0` 消除 inline-block 之间的空白间隙。

```html
<section style="background:#1F2937;border-radius:10px;padding:0;margin:0 0 16px;overflow:hidden;">
  <section style="background:#374151;padding:8px 14px;font-size:0;">
    <span style="display:inline-block;width:10px;height:10px;background:#FF5F57;border-radius:50%;margin-right:6px;"></span>
    <span style="display:inline-block;width:10px;height:10px;background:#FEBC2E;border-radius:50%;margin-right:6px;"></span>
    <span style="display:inline-block;width:10px;height:10px;background:#28C840;border-radius:50%;"></span>
  </section>
  <pre style="margin:0;padding:14px 16px;font-family:Menlo,Consolas,monospace;font-size:13px;line-height:1.7;color:#E5E7EB;white-space:pre-wrap;word-break:break-all;">命令内容</pre>
</section>
```

要点：
- 容器 `#1F2937`，标题栏 `#374151`，圆角 10px + `overflow:hidden`
- 三圆点 10px，颜色 `#FF5F57` / `#FEBC2E` / `#28C840`，**圆点上不加任何文字标签**
- `pre` 字号 13px、行高 1.7、等宽字体，`white-space:pre-wrap` 保证窄屏不横向溢出
- ⚠️ 反复踩的坑：写成 `display:flex;align-items:center;gap:6px` 排三圆点，微信内不生效。生成后务必自检 `display:flex` 命中数为 0

## 代码块注释

代码块中适当加入 `#` 注释，帮助读者理解每条命令的作用。注释用绿色或灰色。

```html
<pre style="...color:#cdd6f4;">
<span style="color:#6c7086;"># 停止网络地址转换服务</span>
net stop winnat

<span style="color:#6c7086;"># 备份配置文件</span>
cp config.toml config.toml.bak
</pre>
```

要点：
- 注释用浅灰色 `#6c7086`（在深色代码块背景中可读）
- 关键命令上方加注释，简单命令可省略
- 备份、停止、启动等操作性命令都应加注释

## 正文样式

```html
<p style="margin:0 0 14px;font-size:15px;color:#3d3d3d;line-height:1.9;">正文内容</p>
```

**硬规则（2026-09-16 新增）**：
- **段落的左右 margin 必须是 0**，左右留白一律交给最外层容器的 `padding:20px 16px` 控制。写成 `margin:0 16px 14px` 会让整篇文字比别的系列多缩进 16px——一行少两个字，全页看着"飘"，且标题色块与正文边界对不齐（Hermes 01~05 就是这个问题）。
- 逐段自查：正则 `<p style="margin:0 [^0]` 命中数必须为 0。
- 每段 **≤3 句、≤80 字**。爆款实测平均段长 30 字左右；超过 90 字的段落全篇不许超过 2 个（且只能是清单型或卡片内容）。

## 卡片布局
用于核心特点、功能一览等并列内容，每项独立成块。**卡片内标题一律 14px**（严禁 16px 以上或纯黑加粗，否则会和章节标题抢层级）。

```html
<section style="background:#FAFAFF;border-radius:10px;padding:10px 14px;margin-bottom:6px;">
<p style="margin:0 0 3px;font-weight:bold;color:#8B5CF6;font-size:14px;">⚡ 特点名</p>
<p style="margin:0;color:#666;font-size:14px;">描述文字</p>
</section>
```

## 分隔线
纯色线条，不用渐变。**全篇统一用居中短细线**（`display:inline-block` 撑宽度），不用满宽横杠。

```html
<section style="text-align:center;margin:0 0 22px;">
<span style="display:inline-block;width:60px;height:3px;background:#6366F1;border-radius:2px;"></span>
</section>
```

- 用于：标题区下方
- **不用在章与章之间**——章节边界靠 `<section>` 容器的 margin + 标题条承担，再加分隔线是重复装饰
- ⚠️ 禁 `height:4px;background:...;margin:0 0 22px` 这种满宽写法

## 页面容器
最外层 `<section>` 设置全局样式。

```html
<section style="max-width:677px;margin:0 auto;padding:20px 16px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,'PingFang SC','Microsoft YaHei',sans-serif;font-size:15px;line-height:1.9;color:#3d3d3d;background:#fff;word-break:break-word;">
...
</section>
```

## 结尾样式
居中短细线 + 总结文字（与标题区同一种线，形态统一）。

```html
<section style="text-align:center;margin:30px 0 12px;">
<section style="text-align:center;margin:0 0 16px;">
<span style="display:inline-block;width:60px;height:3px;background:#6366F1;border-radius:2px;"></span>
</section>
<p style="color:#999;font-size:13.5px;margin:0 0 6px;">🎉 总结文字</p>
<p style="color:#999;font-size:12px;margin:0 0 16px;">互动引导</p>
</section>
```

- 次要文字色一律 `#999`，**不用 `#888`／`#bbb`**（同页两种灰就是"不匀"）
