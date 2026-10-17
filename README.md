# Oceanic Fisheries Ecosystem Laboratory
海洋渔业生态系统实验室

English-language website for the Oceanic Fisheries Ecosystem Laboratory (OFEL), Shanghai Ocean University.

Website: [https://fanzhang-lab-shou.github.io/OFEL/](https://fanzhang-lab-shou.github.io/OFEL/)

The landing page contains a research carousel and three large navigation cards. Full content is on separate static pages: `research.html`, `fan-zhang.html`, `members.html`, `alumni.html`, `publications.html`, `contact.html`, and `blog.html`. Existing homepage fragment links redirect to the corresponding pages.

Run `python3 scripts/build-site.py` after edits. It renders shared navigation/footer and page templates from `templates/`, then builds member cards and publications. GitHub Pages runs the same build before deployment. Generated HTML is included alongside the sources so local previews need no framework or build server.

- Research directions and artwork references: `assets/research.json`. Three primary directions appear in the homepage carousel; all five appear on the research page.
- Members: `assets/people.json`. Role-group order sets the row order. Missing photos reserve rectangular 3:4 portrait slots, and missing email/GitHub details render non-clickable icon placeholders. `scripts/build-people.py` can rebuild just the member page.
- Publications: `assets/publications.json`. Confirmed `attribution.lab_publication: true` determines the lab collection; Fan Zhang’s collection is derived from authorship and can overlap. Exactly one primary `topics` value is required per paper. Confirmed relationship labels and their sources are stored in `attribution`. `scripts/build-publications.py` rebuilds the publication page and both BibTeX downloads.
- Lab Blog: `assets/blog.json`. Initially empty. Add posts with `title`, `url`, and optional `date`/`summary`; create the destination article or supply its link before rebuilding.

论文归属以实验室确认的信息为准；每篇仅归入一个主要研究主题。成员的身份、照片与联系方式在 `people.json` 中维护。首页滚动展示支持左右切换、暂停、触屏滑动和键盘操作，并尊重减少动画的系统偏好。
