# GreatBM'Zoo — 卡片规格（定稿）

> 规格版本：v1.1（2026-08-12 定稿）
> 真相源：本文件 + `generate.py`（渲染代码即执行态，两者冲突以本文件为准，需同步修正 generate.py）
> 变更流程：任何样式/内容结构调整 = 规格变更，先改本文件 bump 版本，再改 generate.py

## 1. 网格

| 项 | 值 |
|---|---|
| 列 | `repeat(auto-fill, minmax(340px, 1fr))`（宽屏 3 列 / 中屏 2 列 / 窄屏 1 列） |
| 行 | `grid-auto-rows: 1fr`（全部等高，以最高卡为准） |
| 间距 | 16px |
| 卡片尺寸 | 等宽等高；min-height 340px（1:1 正方形基准，内容多自然更高） |

## 2. 卡片样式

| 项 | 值 |
|---|---|
| 圆角 | 14px |
| 内边距 | 22px 20px 16px（上 / 左右 / 下） |
| 背景 | 线性渐变高光 + #161b26；hover 上移 3px + 顶部渐变高光线 + 蓝色描边 + 阴影 |

## 3. 卡片内容（三部分，横线分隔）

```
┌─────────────────────────┐
│ 标题 + ★星数（右上角）    │  ← 上部：标题行 + 右上星数徽章
│ v1.x 领域                │     徽章行（版本+领域）
├─────────────────────────┤  ← 横线
│ 关键词 chips（可换行）    │  ← 中部：关键词 + 简介
│ 简介全文                  │     （简介永远在关键词下方）
├─────────────────────────┤  ← 横线
│ ★ Star ⑂ Fork    ⧉ Copy │  ← 下部：按钮行
└─────────────────────────┘
```

| 区 | 内容 | 规格 |
|---|---|---|
| 标题行 | skill 名称 + 右上 ★ 星数 | 等宽 18px；星数金色徽章（0 星隐藏，遮羞）；GitHub API 生成时静态嵌入 |
| 徽章行 | 版本 + 领域 | 版本绿胶囊 12.5px；领域紫胶囊 11.5px；一行左对齐 |
| 关键词行 | top 5 触发词 | 灰胶囊 11.5px，flex-wrap 可换行，完整显示不截断 |
| 简介 | description 全文 | 13.5px，行高 1.7，完整展开；flex 弹性撑开 |
| 按钮行 | 左下 ★ Star；右下 ⧉ Copy | Star 跳转仓库主页（详情跳转引导点赞）；Copy 复制安装命令 |

## 4. 数据规格

| 字段 | 来源 | 约束 |
|---|---|---|
| name | SKILL.md frontmatter name | — |
| version | SKILL.md frontmatter version | v1.x.x |
| category | SKILL.md frontmatter category | 英文分类 |
| triggers | SKILL.md frontmatter metadata.hermes.triggers | 卡片取 top 5 |
| description | SKILL.md frontmatter description | **≤ 100 字符**（hermes-skill-gen 文件间约束 #10） |
| stars | GitHub API（生成时拉取） | 0 星隐藏；失败静默降级 |

## 5. 交互与隐私

- 复制命令：域名路由 —— `gitee.io` 域名复制 gitee 源命令，其余（github.io/本地）复制 GitHub 源命令
- 页面零命令明码、零仓库路径、零源字样（Star/Fork 按钮链接仓库操作页但不显示 URL）
- Copy 反馈：✅ Copied，2 秒恢复
- 星数为生成时静态嵌入，页面运行时零外部请求（符合隐私声明）

## 6. 页面骨架

- 标题：GreatBM'Zoo（Zoo 高亮蓝）
- 副标题：Agent Skill 集 · 即装即用
- 统计行：饲养员：GreatBigM、甜妞 ｜ 多 agent 支持：Hermes / Claude Code / Codex ｜ 感谢各位游客老爷的投喂
- 背景：深色 #0d1117 + 蓝/绿双色 radial 渐变光晕

## 7. 页脚声明（权益与安全）

1. © 2026 大山子科技有限公司 出品 · 版权所有 ｜ 本站 skill 均基于 MIT 协议开源
2. 免责声明：skill 按「现状」提供，不附任何担保；烧录/调试等操作风险自负
3. 安全提示：安装命令源自官方仓库，执行前可查看 install.sh；谨防仿冒
4. 隐私保护：纯静态页面，不收集信息、无 Cookie、无第三方跟踪；第三方商标归各自所有者
