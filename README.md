# RustChinaConf2026

RustChinaConf 2026 大会议程网页（中英双语）· Bilingual schedule for RustChinaConf 2026.

- 日期 / Dates：2026 年 10 月 15–17 日 / Oct 15–17, 2026
- 地点 / Venue：深圳南山伊敦酒店 / ADEN Hotel Shenzhen Nanshan · 与 GOSIM Shenzhen 2026 同期举办
- 在线访问 / Live page：https://rustnexuscon.github.io/RustChinaConf2026/

## 目录结构

| 路径 | 内容 |
|---|---|
| `data/talks-zh.md`、`data/talks-en.md` | 讲师与议题表（中 / 英），两表行数与顺序必须一致 |
| `assets/speakers/` | 讲师头像，文件名与表格「头像」列中的文件名一致（扩展名统一为 `.jpg`） |
| `assets/kv.jpg` | 大会主视觉（1920px 网页版） |
| `src/template.html` | 页面模板：样式、交互，以及 Day 0、开场、茶歇、午餐、闭幕等固定环节 |
| `scripts/build.py` | 构建脚本：解析两张表，把头像和主视觉内嵌为 data URI，生成 `index.html` |
| `index.html` | 构建产物，自包含单页，可直接用浏览器打开 |

## 更新议程

1. 修改 `data/` 下的两张表；新增讲师时把头像放进 `assets/speakers/`。
   固定环节（时间、茶歇、Day 0 等）在 `src/template.html` 的 `PLENARY`、`DAY0` 中修改。
2. 本地构建并预览：`python3 scripts/build.py`，然后打开 `index.html`。
   macOS 用自带的 `sips` 压缩头像，其他系统需要 `pip install pillow`。
3. 提交并推送到 `main`。GitHub Actions（`.github/workflows/pages.yml`）会重新构建并发布到 Pages。

`build.py` 中的特殊处理：闪电演讲拆成 3 个 10 分钟时段（`LIGHTNING`）、姓名更正（`NAME_FIXES`），
以及议题前缀（K1、特别演示、⚡、炉边对话、圆桌）转为标签显示（`TAGS`）。
