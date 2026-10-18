# 网站维护指南

[← 返回 README](../README.md)

本仓库维护上海海洋大学**大洋渔业生态系统实验室**（Oceanic Fisheries Ecosystem Laboratory, OFEL）的英文网站。日常内容在 JSON 数据文件和 `templates/` 中编辑，构建脚本生成可直接访问的静态 HTML。

## 构建、检查与预览

在仓库根目录运行：

```sh
python3 scripts/build-site.py
python3 scripts/check-site.py
python3 -m http.server 8765 --bind 127.0.0.1
```

打开 <http://127.0.0.1:8765/>。构建和链接检查使用 Python 3 标准库；只有重新制作首页壁纸的可选脚本 `scripts/make-hero-wallpaper.py` 需要 Pillow 和 numpy。

生成的 HTML 随源文件一起提交。修改 JSON 或模板后重新构建，避免后续构建覆盖只改在生成页面中的内容。

## 内容在哪里

### 站点地图与链接分享预览

每次构建自动生成 `/OFEL/sitemap.xml`，列出 45 个现有正式页面的 HTTPS 规范目录地址，新增成员和新闻后自动扩充；旧 HTML 跳转页、404、查询参数和锚点不进入地图。未确认的更新时间不写入 `lastmod`。页面 head 也包含地图地址，可将完整站点地图 URL 提交到搜索引擎站长工具。`robots.txt` 需要由域名根目录的站点统一维护。

`scripts/page_metadata.py` 统一生成 Open Graph 和 Twitter 标题、摘要、图片及图片说明。新闻使用各自的 `image`；成员主页使用 `photo`，无照片时使用实验室横幅；Fan Zhang 的个人页使用 `assets/people/fan-zhang.jpg`；首页保留 `assets/social-card.png`。新闻以 `article` 标记，成员以 `profile` 标记。预览信息直接写入 HTML，抓取时无需执行 JavaScript。

新增或更换照片与封面后，可运行 `node scripts/prepare-share-images.cjs`（需要 `sharp`，可用 `NODE_PATH` 指定包目录）生成保留完整构图的较小 JPEG，并提交 `assets/share/`。文件名包含源图片哈希；源图片变化而预览图尚未生成时，构建器暂时使用新原图，避免继续展示旧照片。生成后按常规重新构建，再运行 `python3 scripts/check-sharing.py`。各分享平台独立控制抓取、裁切和缓存。

### 首页宣传片

首页底部的 Explore 按钮跳转到页脚上方的内嵌播放器并请求播放。源模板在 `templates/index.html`，视频为 `assets/video/ofel-film-1080p.mp4`，封面为 `assets/video/ofel-film-poster.webp`。保持 `controls`、`playsinline` 和 `preload="none"`，不添加自动播放，避免访客打开首页就下载整段视频。替换 MP4 时使用 H.264 / AAC 和 fast-start（`moov` 在文件开头），并重新检查文件大小及播放。

### 网页图片与手机导航

`assets/people/`、`assets/news/`、`assets/research/`、`assets/software/` 和 `assets/contact/` 中的原图保持不变。大于 100 KiB 的静态图片可通过 `node scripts/optimize-images.cjs` 生成 WebP 展示图（运行环境需安装 `sharp`；也可用 `NODE_PATH` 指定已有的包目录）。生成的 `assets/optimized/` 文件与 `manifest.json` 一起提交，再运行常规 Python 构建。GitHub Pages 构建无需安装图片工具。

构建器依据图片用途输出 `srcset` 和 `sizes`，由浏览器选择尺寸；原图更新导致哈希不匹配时回退原图，避免展示旧内容。不要直接修改生成页面中的图片地址，也不要把展示图路径写回新闻或人员 JSON。首页 News 仍按源记录日期选择最新一条。人物和海报均保持原始构图，较窄的卡片继续使用现有 CSS 裁切位置。

手机端首页四张导航卡片支持滑动、左右按钮、四个分页圆点，以及聚焦卡片区域后的方向键和 Home/End 键。桌面端保持网格，控制按钮仅在手机横向溢出时显示；减少动态效果的系统设置会禁用平滑切换。

### Fan Zhang 个人页

全站共用 `assets/styles/site-ui.css` 中的系统字体、圆角与海蓝色彩变量，由 `templates/head.html` 和 `scripts/page_metadata.py` 在所有正式内容页统一加载，并按内容哈希更新缓存。`styles.css` 保留页面结构和基础响应式布局；UI 样式在后加载的共享文件中维护。原先只用于 Fan Zhang 页的 `faculty-ui.css` 已合并到共享文件，个人页特有布局仍使用 `body[data-page="fan-zhang"]` 限定。

系统无衬线字体直接使用访客设备字体，标题主要使用 650–750 字重；照片和面板采用 20–28px 圆角，输入框采用 14px，按钮和分类切换采用胶囊形状。内页用低饱和海蓝渐变衬托白色卡片；首页保留深海色背景与原有壁纸。浅色联系页的文字、网页邮箱入口与状态提示使用深色，校园图上的文字仍使用浅色。渐变为静态 CSS，不增加背景图片下载或动画。

调整共享 UI 后运行完整构建、链接和交互检查。保持 `hidden` 筛选规则、手机导航、键盘焦点、减少动态效果设置以及原有图片比例／取景位置；不要用全局圆角规则裁切官方 logo 或改变照片为圆形。

导师页顶部使用一张连续的无人背景 `assets/faculty/fan-zhang-library-background-v3.webp`，叠放既有修复人物 `assets/faculty/fan-zhang-hero-cutout-restored-v2.webp`；背景采用单一 `cover`，避免不同缩放照片叠放产生接缝。`facultyPortraitGeometry`（`script.js`）把桌面端人物限制在屏幕左半边；右侧 `.fz-workspace` 以正常网格排版姓名、搜索、五个入口与展开卡片，卡片内容从下方原章节读取，卡片内滚动，不覆盖人物。窄屏或竖屏把操作区放到人物下方。气泡保持在头部附近，窗口和气泡尺寸变化时重算位置。首屏导航透明，离开后恢复浅色；下方章节渐显，唯一 `h1` 在首屏。原图与旧抠图仍保留，背景处理提示词保存在 `assets/people/heroes/generation-notes.json`。调整布局后运行 `node scripts/test-profile-layout.cjs`，检查人物与右侧信息区分离、紧凑屏幕稳定性和渐显行为。

源文件为 `templates/members/fan-zhang.html`，样式使用 `faculty-` 前缀，避免影响其他成员页。保留 `#people` 和 `#principal-investigator` 原锚点。姓名仅出现一个主标题，职称加粗，联系按钮跳转联系页选择邮箱。ICCAT 的链接放在组织全称上。代表论文在 `scripts/build-site.py` 的 `faculty_dois` 中指定，标题、年份和期刊由现有论文库读取；只选择实验室成员／校友一作且 Fan Zhang 参与，或 Fan Zhang 本人一作的论文，排除外部合作者一作的论文，构建时校验这一条件。不在模板中手工复制论文信息。更换照片时保持完整人物可见，并检查桌面及手机的 `object-position`。

### 联系与到访

联系页内容在 `templates/contact.html`：校园插画与 Fan Zhang 联系方式、研究生咨询／研究访问／科研合作三个邮件入口，以及中英文地址和地图导航。邮件入口只打开访客的邮件应用，通过不同的主题区分咨询类型；邮箱下方另有 Gmail、Outlook 网页写信入口和复制邮箱按钮。复制受限时显示可选中的邮箱文本，网页邮箱入口在禁用 JavaScript 时仍可使用。不提供站内发送表单，也不表示已发布招生名额。保留 `#contact`、`#join-us` 和 `#visit` 页内锚点。校园插画复用首页图片，来源及生成记录位于 `assets/contact/shou-campus-collaboration-prompt.md`。

### 访问统计（Info → More）

全站通过 [GoatCounter](https://fanzlabshou.goatcounter.com/) 统计访问，脚本写在 `templates/head.html`，所有正式页面都会计入；不使用 Cookie，从 2026-10-17 开始计数。登录 GoatCounter 可查看来源、国家、设备等完整后台。

顶部 Info 菜单的 More 页面（`/more/`，模板 `templates/more.html`）用站内自己的样式展示数据，交互代码为 `script.js` 中的 `initSiteStats`：总浏览量、独立访客、最近 7 天浏览量、最近 14 天每日浏览量（按 UTC 日期）和最受欢迎页面。数据来自 GoatCounter 的公开计数接口 `/counter/<路径>.json`，需在 GoatCounter 设置中保持勾选 “Allow adding visitor counts on your website”；仪表盘本身可以只对登录用户可见。页面排行只统计主要页面与新闻文章，列表由构建脚本的 `stats_pages` 自动生成。结果在浏览器会话中缓存 10 分钟，计数服务不可用时显示短横线。

### 研究方向

编辑 [`assets/research.json`](../assets/research.json)。`primary` 为 `true` 的三个方向是核心方向，其余两个为延伸研究。五个方向都会出现在首页研究轮播和研究页面中。

每个方向的 `publications` 填写 2–3 个已收录论文的 DOI，由论文元数据自动显示标题、年份、期刊和作者归属。一个 DOI 只能选入一个研究方向，构建时会拒绝重复或未知 DOI。合作论文明确标注 Fan Zhang & collaborators。资源评估方向的 `software` 提供 ALSCL 的站内入口。代表论文和软件入口只在 Research Themes 内页展示，首页轮播保持简洁。

顶部 Research 菜单分为 Research Themes 和 Collaborators。研究方向位于 `/research/themes/`，模板为 `templates/research/themes.html`；合作人员页面为 `/research/collaborators/`，待提供名单后在对应模板中补充。旧 `research.html` 链接由 GitHub Pages 的 404 回退跳转至 Themes，并保留研究方向的锚点。

### 成员与校友

编辑 [`assets/people.json`](../assets/people.json)，照片放在 [`assets/people/`](../assets/people/)。

- `groups` 的顺序决定教师、博士后、博士生、硕士生的显示顺序。同组按年级从高到低排列，再按姓名排序。
- `alumni` 按毕业年份分组，年份从新到旧排列。
- 毕业后仍在实验室工作的成员，可在 `alumni` 条目中设置 `profile_ref` 为现有成员姓名；校友照片与链接复用该成员主页，保留其当前岗位。相同年份可分别设置 PhD、Master’s 等学位分组。
- `photo`、`photo_alt` 和 `bio` 分别维护照片、替代文字和英文简介；简介中的空行划分段落。
- 可选的 `bio_zh` 保存中文原文，个人主页中以可展开的中英对照区域呈现。
- `profile_photo_aspect_ratio` 可设置个人主页照片比例，`photo_position` 调整取景位置。`profile_photo` 可为下方资料区单独指定高清修复图，默认仍使用 `photo`；目前 Qinqin Lin、Zhechuan Xu 和 Xianglong Yan 使用 `assets/people/portraits/` 中保留原背景的高清修复、轻度自然美颜版本；下方资料照使用完整照片，顶部仍使用独立透明抠图；Qinqin Lin 使用修复会议现场的独立环境背景，另两页使用柔和色彩背景。处理提示词保存在该目录的 `generation-notes.json`。
- `email`、`github`、`website`、`researchgate` 维护联系方式。未提供的值留为 `null` 或省略，不填猜测的地址。
- 成员目录仅显示姓名、身份／年级和照片，不显示邮箱、外部个人页或联系图标；这些联系方式只在个人主页展示已提供的项目。
- `website_label` 设置网站链接名称；`website_icon` 可选 `globe` 或 `researchgate`。独立的 `researchgate` 字段可与 GitHub、学校主页同时使用。

成员目录采用深海蓝底的错落照片网格，顶部导航与页脚同色；标题占用网格左上方的大块留白。卡片显示姓名、身份／年级和照片，整张卡片链接个人页。优先使用 `profile_photo` 高清资料照，缺少照片时使用既有占位图。保持原组别顺序及年级从高到低的排序，组别旧锚点保留在该组第一位成员的姓名上。桌面端为五列，中屏四列，手机两列；悬停和键盘聚焦时卡片轻微放大，减少动态效果设置下保留焦点提示并取消缩放。样式使用 `.directory-` 前缀，深色导航及页脚通过 `body[data-page="members"]` 限定，避免影响其他页面。

构建后自动生成 `members/<given-name>-<family-name>/index.html`，访问地址为 `/members/<given-name>-<family-name>/`，包括简介、按作者姓名匹配的论文、前后成员导航。缺失照片保留矩形照片位。

现有成员中同时设置 `photo` 与 `hero.cutout` 的个人页，顶部为全屏深色介绍：模糊原照作背景、透明主体居中偏右，左上 “Hi, I’m” 和姓名，左侧简介与联系入口，右下研究方向。证件照或正面半身照可设置 `hero.background_color`（六位十六进制色值），只用扩散色彩作背景，避免背景里再次出现放大人脸；目前用于 Zhechuan Xu 和 Xianglong Yan。Qinqin Lin 通过 `hero.background_image` 指定从修复会议照片制作的无人环境背景，`hero.background_dimensions` 记录其尺寸；背景柔化、人物抠图保持清晰，两层独立显示，避免背景中重复出现人脸。`hero.summary` 保存首屏短简介，`hero.research` 保存已有资料确认的研究方向；缺少依据时显示 “To be updated”。手机端改为图片上方、文字下方的连续布局。下方仍保留完整简介、中文原文、论文及前后成员导航，照片、简介、每篇论文和成员导航通过现有 `data-reveal` 逐段渐显；系统要求减少动态效果时直接显示。样式在 `.member-intro`，生成器为 `scripts/build-people.py`，仅作用于当前成员；没有照片或尚未制作抠图的成员保持原版式。首屏姓名为唯一 `h1`，下方姓名为 `h2#member-details`。首屏导航透明，滚到详细资料后恢复浅色。原始照片保留不变，透明前景文件在 `assets/people/heroes/`，内置 image_gen 的生成方式与提示词记录在同目录 `generation-notes.json`。

Fan Zhang 主页的主体信息在 [`templates/members/fan-zhang.html`](../templates/members/fan-zhang.html) 中维护。

### 论文

编辑 [`assets/publications.json`](../assets/publications.json) 与 [`assets/member-publications.json`](../assets/member-publications.json)。同一个 DOI 只保留一条记录。

- Fan Zhang 为作者，且第一作者为实验室成员或校友的论文，归入实验室论文集合。
- Fan Zhang 论文集合按共同作者信息生成，两个集合可包含同一篇论文。
- 每篇论文只设一个主要 `topics` 值，避免在多个研究主题中重复。
- 已确认的合作关系及其依据记录在 `attribution`；论文归属以实验室确认的信息为准。
- `member-publications.json` 中的其他成员论文显示在匹配的个人主页；Fan Zhang 共同署名的记录也进入主论文页面。

`scripts/build-publications.py` 生成论文页面和两份 BibTeX 文件。学名在 [`scripts/species.py`](../scripts/species.py) 中维护，在论文、新闻与 BibTeX 中自动使用斜体。

论文页支持按标题或作者搜索，可与年份、主题及论文集合组合筛选；搜索忽略大小写和拉丁字母的重音符号。年份选项只列出当前集合的年份。使用任一筛选时展示全部匹配结果，不再限制为最近六篇；Clear filters 清空搜索、年份和主题，保留当前集合。

每篇论文及成员主页的论文条目提供 Copy citation 与 View citation。可读引用由同一份元数据生成，包含全部作者、年份、题名、期刊、已知的卷期页码或文章编号和 DOI。剪贴板不可用时展开并选中引用文本，便于手动复制；不需要新的引用服务或 API。原有集合 BibTeX 下载保持可用。

### 新闻

编辑 [`assets/blog.json`](../assets/blog.json)，图片放在 [`assets/news/`](../assets/news/)。

每条新闻包含 `slug`、`date`、`title`、`summary` 和 `body`，可选 `image`、`image_alt`、`image_caption`、`image_position`、`image_aspect_ratio`、`people`、`paper` 与 `source`。使用真实发布日期；活动公告按活动日期归档。`people` 姓名与成员记录一致时，会链接到其主页。`body` 支持普通段落、`heading`、`figure`，以及 `details`（由 `label` / `value` 条目组成的活动信息表）。

每条新闻还须填写一个 `category`，取值来自 `blog.json` 顶层的 `categories`。当前为研究成果（research）、学术交流（exchange）、课程活动（courses）、荣誉与任职（honors）。只有已有新闻的类别才显示筛选按钮。News 内页支持分类筛选及 `?category=research` 等直达链接，列表和文章均显示类别；分类不会进入首页，筛选前后新闻始终保持日期倒序。新增新闻时无需调整首页精选逻辑。

News 列表的图片框为横向 3:2。需要单独构图时可填写 `thumbnail` 和 `thumbnail_position`，仅替换列表缩略图；文章中的 `image` 仍展示原海报，首页也继续按最新日期选择新闻。

构建生成 `news/<slug>/index.html`，访问地址为 `/news/<slug>/`，列表始终按日期从新到旧排列。**首页 News 入口始终使用日期最新的新闻封面与标题，不设置手动精选。补录、修改旧新闻或更换旧新闻封面，均不得覆盖日期较新的首页新闻。**

首页 Publications 入口按当前展示论文的 DOI 匹配新闻中 `paper.cover` 的期刊封面，保留期刊标识的展示空间。没有对应封面时使用研究插图作为背景。
当前固定展示 Runze Wang 等发表于 *Fish and Fisheries* 的论文（`10.1111/faf.70077`）；如需更换精选论文，在 `scripts/build-site.py` 的首页论文选择处修改 DOI。

### Resources

顶部 Resources 菜单包含 Reference Materials 和 Software，源模板在 `templates/resources/`，生成页面在 `resources/`。

- Reference Materials 的卡片信息在 `assets/reference-materials.json`：`professional_links` 放专业资料入口，`international_organizations` 放国际组织。每项包含机构名称、全名、简介、官方链接、显示域名、覆盖范围和本地 Logo 路径。白色 Logo 可设置 `dark_logo: true` 使用深色底板。Logo 存放在 `assets/resources/`，来源记录见该目录的 `README.md`。
- Software 展示 ALSCL 简介、在线文档与仓库链接。ALSCL logo 取自其官方仓库，存放在 `assets/software/alscl-logo.png`。

## 目录结构

```text
OFEL/
├── README.md                  实验室展示与仓库入口
├── index.html                 首页
├── research/                  Research Themes 与 Collaborators
├── publications/index.html    论文与筛选
├── contact/index.html         联系与加入
├── members/                   成员、校友与个人主页
├── news/                      新闻列表与文章
├── resources/                 参考资料与软件
├── assets/                    JSON 数据、照片、插图、BibTeX
│   ├── people/                成员照片
│   └── news/                  新闻封面、图表与期刊封面
├── templates/                 页面源模板、共享导航与页脚
├── scripts/                   构建、链接检查及图像辅助脚本
├── docs/                      维护说明与 README 图形素材
├── styles.css                 样式
├── script.js                  导航、筛选与轮播交互
└── .github/workflows/pages.yml 自动构建与部署
```

公开网址统一使用目录形式（如 `/news/`、`/members/fan-zhang/`、`/publications/`），不显示 `.html` 或 `index.html`。每个目录实际包含一个 `index.html`。模板文件名保留原样，避免把内容源文件与公开网址混淆。

模板采用相对站点根目录的路径；[`scripts/site_paths.py`](../scripts/site_paths.py) 根据输出目录调整链接、图片、`srcset`、CSS 与 JavaScript 路径。新增成员和新闻自动写入相应文件夹。

此前公开的 `.html` 文件保留为小型跳转页，直接转到新的目录网址，保留查询参数和 `#` 片段。直接访问目录内的 `index.html` 时，前端会把地址栏规范为目录网址。旧首页片段链接仍跳转到对应页面。`404.html` 兼容更早位于根目录的成员与新闻地址。不要在旧跳转页中编辑内容。

网址相关改动后运行 `python3 scripts/test-site-paths.py`、构建及全站检查。检查脚本会验证目录式导航、canonical 地址、新闻时间顺序与深层页面资源路径。

## 提交与部署

1. 修改数据、模板或静态资源。
2. 运行 `python3 scripts/build-site.py`。
3. 运行 `python3 scripts/check-site.py`，再预览受影响的页面。
4. 提交源文件、图片及对应生成的 HTML。
5. 推送到 `main`；GitHub Actions 将再次构建、检查并部署。

部署状态见 [Deploy laboratory website](https://github.com/FanZhang-LAB-SHOU/OFEL/actions/workflows/pages.yml)。

README 的定制横幅和导航图标在 [`docs/assets/`](assets/) 中，网站预览为截图。README 视觉排版参考 [awesome-readme](https://github.com/matiassingers/awesome-readme) 和 [GitSkins](https://www.gitskins.com/)，图形与布局为本仓库定制。

当前横幅为 [`ofel-banner.png`](assets/ofel-banner.png)，展示船队、金枪鱼群及 DNA 双螺旋，实验室名称下方标注 Fanzhang Lab，底部研究标签为 Population Dynamics；由内置 imagegen 工具基于原横幅编辑生成，保留深海蓝与青绿色调。[完整生成提示词](assets/ofel-banner-prompt.md) 随图保存。
