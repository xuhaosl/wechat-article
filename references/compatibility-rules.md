# 公众号 HTML 兼容性规则（踩坑总结）

以下规则均经过实际公众号编辑器粘贴验证，**必须严格遵守**。

## 标签规则

### 禁用 `<div>` → 一律用 `<section>`
公众号编辑器粘贴时会**剥离 `<div>` 元素上所有 inline 样式**（background、color、padding、border-radius 全丢），但对 `<section>` 元素的样式保留率高得多。

```
禁用: <div style="background:#xxx;...">
正确: <section style="background:#xxx;...">
```

**唯一例外**：整页最外层那个 `<div class="wrap">` 外壳（配 `<style>.wrap{max-width:720px}</style>`）。它在 `<body>` 之后、第一个 `<section>` 之前，粘进编辑器时被剥掉，不影响正文；`content-check.py` 只放行这一种形态——**片段 HTML 里一个 div 都不许有**。

### 禁用 `<a href>` → 可见 URL 文本
公众号编辑器粘贴时会**剥离所有 `<a>` 标签的 `href` 属性**，外部链接一律变成纯文字，无法点击跳转。

```
禁用: <a href="https://xxx.com">链接文字</a>
正确: <span style="color:#xxx;font-weight:bold;">🔗 https://xxx.com</span>
```

注意：保留 `https://` 完整协议前缀，不要只留域名路径。

### 禁用 `<ul>/<ol>/<li>` → 改为 `<p>` 段落
公众号对列表结构的缩进和间距处理不稳定，手机端经常出现缩进丢失、列表项挤到一起的问题。

```
禁用: <ul><li>项目一</li><li>项目二</li></ul>
正确: <p style="margin:6px 0;">● 项目一</p>
      <p style="margin:6px 0;">● 项目二</p>
```

### 禁用 `<table>` → 改为 `<section>` 卡片式布局
窄屏溢出，手机端排版错乱。改为每行一个独立 `<section>` 卡片，标题 + 描述上下排列。

### 强调文字不用 `<b>` / `<strong>` → 用带样式的 `<span>`
语义标签的样式由编辑器默认样式表决定，保留率不如行内样式。需要加粗强调时一律写成显式样式的 `<span>`，颜色 + 粗细都写全，粘贴后不会丢。

```
禁用: <b style="color:#A63C06;">不是</b>聊天机器人
正确: <span style="color:#A63C06;font-weight:bold;">不是</span>聊天机器人
```

## 样式规则

### 禁用 `linear-gradient` → 用纯色 `background:`
公众号不认渐变，所有 `linear-gradient` 背景粘贴后变白底。

```
禁用: background:linear-gradient(to right,#F5F3FF,#FAFAFF)
正确: background:#F5F3FF
```

### 禁用 `background-color:` → 用简写 `background:`
长属性名兼容性差，简写 `background:` 在公众号中保留率更高。

```
禁用: background-color:#FEF3C7
正确: background:#FEF3C7
```

### 文字颜色不靠继承 → 每个元素显式设置
即使父容器设置了 `color`，公众号粘贴后中间层样式可能丢失，导致文字变黑色。每个 `<p>`/`<span>` 必须显式设置 `color`。

### 字号建议
- 正文：15px
- 一级标题：18px
- 二级标题：16px
- 代码：13px
- 标注/说明：12.5-13px

窄屏舒适，过大字号在手机端占屏过多。

## 布局规则

### 禁用 `display:flex` + `gap` → 用 `inline-block` + `margin`
微信内置浏览器不兼容 flex 布局，gap 属性会被忽略。

```
禁用: display:flex;gap:6px
正确: display:inline-block;margin-right:6px
```

### 禁用 `text-indent` 负缩进
手机端文字错位，直接去掉。

### 加 `word-break:break-word`
最外层容器加 `word-break:break-word`，长 URL/路径自动换行，不撑破布局。

### 代码块加 `overflow-x:auto`
超长代码行横向滚动，不撑破布局。

## 组件规则

### 代码块
深色背景 `<section>` + `<pre>`，加仿 macOS 终端窗口栏（红黄绿三圆点）。

- 圆点用 CSS 盒模型（自然美观），不用 Unicode `●` 字符（渲染怪异）
- **不加标签文字**（如 Terminal、PowerShell、cmd 等）
- 容器用 `<section>` + `background` + `font-size:0` 消除空白
- **加入注释**：关键命令上方加 `#` 注释，注释用浅灰色 `#6c7086`

```html
<section style="background:#1e1e2e;border-radius:10px;overflow:hidden;margin:10px 0;">
<section style="background:#313244;padding:7px 14px;font-size:0;">
<span style="display:inline-block;width:11px;height:11px;border-radius:50%;background:#f38ba8;margin-right:6px;vertical-align:middle;"></span>
<span style="display:inline-block;width:11px;height:11px;border-radius:50%;background:#f9e2af;margin-right:6px;vertical-align:middle;"></span>
<span style="display:inline-block;width:11px;height:11px;border-radius:50%;background:#a6e3a1;margin-right:8px;vertical-align:middle;"></span>
</section>
<pre style="margin:0;padding:12px 14px;font-family:'Cascadia Code','Fira Code',Consolas,'Courier New',monospace;font-size:13px;line-height:1.7;color:#cdd6f4;white-space:pre-wrap;word-break:break-all;overflow-x:auto;"><span style="color:#6c7086;"># 备份配置文件</span>
cp config.toml config.toml.bak</pre>
</section>
```

### 提示框 / Callout
全圆角纯色背景 `<section>`，内部 `<p>`/`<span>` 加显式 `color`。

```html
<!-- 警告框（黄色） -->
<section style="background:#FEF3C7;border-radius:10px;padding:12px 16px;margin:10px 0;font-size:14.5px;color:#92400E;line-height:1.75;">
<p style="margin:0;color:#92400E;font-size:14.5px;line-height:1.75;">
<span style="font-weight:bold;color:#92400E;">⚠️ 注意：</span>提示内容
</p>
</section>

<!-- 建议框（蓝色） -->
<section style="background:#DBEAFE;border-radius:10px;padding:12px 16px;margin:10px 0;font-size:14.5px;color:#1E40AF;line-height:1.75;">
<p style="margin:0;color:#1E40AF;font-size:14.5px;line-height:1.75;">
<span style="font-weight:bold;color:#1E40AF;">💡 建议：</span>建议内容
</p>
</section>
```

### 圆点列表项
用 Unicode `●` 字符 + `color` 着色，不用 CSS 盒模型（会被剥离）。

```html
<p style="margin:6px 0;"><span style="color:#3B82F6;font-size:18px;">●</span> 列表内容</p>
```

### 步骤编号
统一用 `📍 第 X 步：标题` 两行结构，标题行 + 描述行。不混用 `1.` `2.` 纯数字编号。

```html
<p style="margin:10px 0 4px;font-weight:bold;color:#F59E0B;font-size:14.5px;">📍 第 1 步：标题</p>
<p style="margin:0 0 8px;font-size:14.5px;">描述内容</p>
```

### 图片
`width:100%;max-width:480px`，圆角 12px + 柔和投影，居中。投影颜色用章节主色调的 rgba 半透明形式（比纯黑更柔和）。图片下方加居中灰色图注。

⚠️ **图片 src 必须用 HTTPS 远程 URL，不能用本地相对路径**（2026-08-14 教训）：公众号编辑器无法解析本地路径，推送脚本对本地路径报 `Invalid URL` 导致丢图。**地址一律按素材笔记原文里的 URL 取**；源图在本地、没有 URL 时停下来报清是哪一节第几张，等用户给地址，别自己编一个。

```html
<img src="URL" alt="说明" style="width:100%;max-width:480px;border-radius:12px;margin:0 auto 6px;display:block;box-shadow:0 4px 16px rgba(99,102,241,0.12);" />
<p style="text-align:center;color:#999;font-size:12.5px;margin:0 0 16px;">图片说明文字 🔧</p>
```

### 行内代码（inline code）
正文中出现的命令、文件名、路径、配置项、界面菜单路径等，统一用彩色背景圆角 `<span>` 高亮。**必须全量覆盖**，不能有的有样式有的没有。

```html
<span style="background:#EEF2FF;color:#6366F1;padding:1px 6px;border-radius:4px;font-size:14px;font-family:'Cascadia Code','Fira Code',Consolas,monospace;">npm -v</span>
```

- 背景用当前章节主题色的浅色变体，文字用主题色深色变体
- 覆盖范围：命令、文件名、路径、配置项名、界面菜单路径（如「设置 > 路由 > 安全」）

### 锚点跳转
`id` 属性会被公众号剥离，浏览器预览可用但公众号失效。目录项可加 `<a href="#sec1">` 供浏览器预览跳转，但需告知用户公众号内需手动用编辑器「文字跳转」功能。

### 文末不要加链接汇总
用户明确不要文末链接汇总区，所有链接在正文对应位置以可见 URL 文本呈现即可。

### 系列链接：正文写产品名，链接由用户在编辑器里挂（2026-09-12 修正，**废止「链接占位卡」**）
用户手改 Hermes 01 定稿时，把我放的两张「链接占位卡」**全部删掉**，改成在正文里直接写出产品名，发布时自己选中那几个字、用公众号编辑器的「合集」功能挂上**系列合集链接**（`appmsgalbum`）。

- **正确做法**：正文正常写出产品名／系列名并列（如「Claude Code、CodeX、WorkBuddy、DeepSeek Harness」），**不写链接、不放占位卡、不列具体篇目清单**
- **为什么**：①占位卡多一道"删卡换链接"的无用工序，等于给用户加活；②用户挂的是**系列合集**（一次覆盖整个系列），曝光拉动强于单篇；③我猜的单篇篇目（RAGFlow 03 等）他基本没挂——猜错了
- **我该做好的**：把产品名写全、写准（这是挂链接的锚点）；系列名尽量用公众号里的实际叫法，方便对上合集
- 同一个产品名可以在正文出现多次，每一处都是可挂链的位置，用户自己选
 
### 主题色与固定功能色的撞色检查
选定主题色后，要顺手比一下 3 个固定功能色（⚠️琥珀 #F59E0B / 💡蓝 #3B82F6 / ✅绿 #10B981）。**主题色是橙色系时，琥珀警示卡会和主题色卡糊在一起**——此时主题色取偏红橙的 `#E8590C`（浅底 `#FFF1E8`），与琥珀的偏黄调拉开距离；或反把警示卡边框改成 `#D97706`。撞色不是禁止，只要求"一眼能分清哪张是提示、哪张是内容"。

## 敏感词汇处理
扫描全文是否包含 VPN、翻墙、v2Ray、Clash、代理工具等敏感词汇，如有则替换为"科学上网"。

## 隐私信息检查（强制）
生成产物前必须检查全文：用户名、邮箱、手机号、个人本地路径、真实 IP 地址、API 密钥、密码等。如发现实际隐私数据，必须告知用户具体位置和内容，询问如何处理，不可自行删改。通用占位符（如"你的安装路径"）不算隐私信息。
