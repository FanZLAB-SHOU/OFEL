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

### 研究方向

编辑 [`assets/research.json`](../assets/research.json)。`primary` 为 `true` 的三个方向是核心方向，其余两个为延伸研究。五个方向都会出现在首页研究轮播和研究页面中。

### 成员与校友

编辑 [`assets/people.json`](../assets/people.json)，照片放在 [`assets/people/`](../assets/people/)。

- `groups` 的顺序决定教师、博士后、博士生、硕士生的显示顺序。同组按年级从高到低排列，再按姓名排序。
- `alumni` 按毕业年份分组，年份从新到旧排列。
- `photo`、`photo_alt` 和 `bio` 分别维护照片、替代文字和英文简介；简介中的空行划分段落。
- `profile_photo_aspect_ratio` 可设置个人主页照片比例，`photo_position` 调整取景位置。
- `email`、`github`、`website`、`researchgate` 维护联系方式。未提供的值留为 `null` 或省略，不填猜测的地址。
- 未提供 GitHub 链接时不显示 GitHub 图标。成员列表中缺失邮箱仍显示不可点击的邮箱占位图标；个人主页只显示已提供的联系方式。
- `website_label` 设置网站链接名称；`website_icon` 可选 `globe` 或 `researchgate`。独立的 `researchgate` 字段可与 GitHub、学校主页同时使用。

构建后自动生成 `members/<given-name>-<family-name>.html`，包括简介、按作者姓名匹配的论文、前后成员导航。缺失照片保留矩形照片位。

Fan Zhang 主页的主体信息在 [`templates/members/fan-zhang.html`](../templates/members/fan-zhang.html) 中维护。

### 论文

编辑 [`assets/publications.json`](../assets/publications.json) 与 [`assets/member-publications.json`](../assets/member-publications.json)。同一个 DOI 只保留一条记录。

- Fan Zhang 为作者，且第一作者为实验室成员或校友的论文，归入实验室论文集合。
- Fan Zhang 论文集合按共同作者信息生成，两个集合可包含同一篇论文。
- 每篇论文只设一个主要 `topics` 值，避免在多个研究主题中重复。
- 已确认的合作关系及其依据记录在 `attribution`；论文归属以实验室确认的信息为准。
- `member-publications.json` 中的其他成员论文显示在匹配的个人主页；Fan Zhang 共同署名的记录也进入主论文页面。

`scripts/build-publications.py` 生成论文页面和两份 BibTeX 文件。学名在 [`scripts/species.py`](../scripts/species.py) 中维护，在论文、新闻与 BibTeX 中自动使用斜体。

### 新闻

编辑 [`assets/blog.json`](../assets/blog.json)，图片放在 [`assets/news/`](../assets/news/)。

每条新闻包含 `slug`、`date`、`title`、`summary` 和 `body`，可选 `image`、`image_position`、`image_aspect_ratio`、`people`、`paper` 与 `source`。使用真实发布日期；`people` 姓名与成员记录一致时，会链接到其主页。

构建生成 `news/<slug>.html`，列表按日期从新到旧排列。首页 News 入口自动使用最新新闻的封面和标题。

首页 Publications 入口按当前展示论文的 DOI 匹配新闻中 `paper.cover` 的期刊封面，保留期刊标识的展示空间。没有对应封面时使用研究插图作为背景。
当前固定展示 Runze Wang 等发表于 *Fish and Fisheries* 的论文（`10.1111/faf.70077`）；如需更换精选论文，在 `scripts/build-site.py` 的首页论文选择处修改 DOI。

## 目录结构

```text
OFEL/
├── README.md                  实验室展示与仓库入口
├── index.html                 首页
├── research.html              研究方向
├── publications.html          论文与筛选
├── contact.html               联系与加入
├── members/                   成员、校友与个人主页
├── news/                      新闻列表与文章
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

模板采用相对站点根目录的路径；[`scripts/site_paths.py`](../scripts/site_paths.py) 根据输出目录调整链接、图片、`srcset`、CSS 与 JavaScript 路径。新增成员和新闻自动写入相应文件夹。

旧首页片段链接会跳转到对应页面。`404.html` 兼容历史上位于根目录的成员与新闻地址，在 GitHub Pages 上跳转到新路径并保留查询参数和片段。

## 提交与部署

1. 修改数据、模板或静态资源。
2. 运行 `python3 scripts/build-site.py`。
3. 运行 `python3 scripts/check-site.py`，再预览受影响的页面。
4. 提交源文件、图片及对应生成的 HTML。
5. 推送到 `main`；GitHub Actions 将再次构建、检查并部署。

部署状态见 [Deploy laboratory website](https://github.com/FanZhang-LAB-SHOU/OFEL/actions/workflows/pages.yml)。

README 的定制横幅和导航图标在 [`docs/assets/`](assets/) 中，网站预览为截图。README 视觉排版参考 [awesome-readme](https://github.com/matiassingers/awesome-readme) 和 [GitSkins](https://www.gitskins.com/)，图形与布局为本仓库定制。
