# GreatM's Zoo — 卡片规格（定稿）

> 规格版本：v1.0（2026-08-12 定稿）
> 真相源：本文件 + `generate.py`（渲染代码即执行态，两者冲突以本文件为准，需同步修正 generate.py）
> 变更流程：任何样式/内容结构调整 = 规格变更，先改本文件 bump 版本，再改 generate.py

## 1. 网格

| 项 | 值 |
|---|---|
| 列 | `repeat(auto-fill, minmax(340px, 1fr))`（宽屏 3 列 / 中屏 2 列 / 窄屏 1 列） |
| 行 | `grid-auto-rows: 1fr`（全部等高，以最高卡为准） |
| 间距 | 16px |
| 卡片规格 | 等宽等高，统一规格 |

## 2. 卡片样式

| 项 | 值 |
|---|---|
| 圆角 | 14px |
| 内边距 | 18px 20px 14px（上 / 左右 / 下） |
| 背景 | 线性渐变高光 + #161b26；hover 上移 3px + 顶部渐变高光线 + 蓝色描边 + 阴影 |

## 3. 卡片内容（从上到下 5 行区）

| 区 | 内容 | 规格 |
|---|---|---|
| 1 标题行 | skill 名称 | 等宽字体 18px，独占一行 |
| 2 徽章行 | 版本 + 领域 | 版本绿胶囊 12.5px；领域紫胶囊 11.5px；一行左对齐 |
| 3 关键词行 | top 5 触发词 | 灰胶囊 11.5px，单行，超出隐藏 |
| 4 介绍 | description 全文 | 13.5px，行高 1.6，完整展开不省略；flex:1 弹性撑开 |
| 5 底部栏 | 左下 ★ Star / ⑂ Fork；右下 ⧉ Copy | 上边框分隔；按钮暗色 12.5px，padding 5px 11px，圆角 6px，hover 蓝边 |

## 4. 数据规格

| 字段 | 约束 |
|---|---|
| name | skill 名（= SKILL.md frontmatter name） |
| version | v1.x.x（= SKILL.md frontmatter version） |
| category | 领域（英文分类） |
| triggers | top 5 关键词 |
| description | **≤ 100 字符**（市场卡片规格；hermes-skill-gen 文件间约束 #10 已入稿） |

## 5. 交互与隐私

- 复制命令：域名路由 —— `gitee.io` 域名复制 gitee 源命令，其余（github.io/本地）复制 GitHub 源命令
- 页面零命令明码、零仓库路径、零源字样（Star/Fork 按钮链接仓库操作页但不显示 URL）
- Copy 反馈：✅ Copied，2 秒恢复

## 6. 页面骨架

- 标题：GreatM's Zoo（Zoo 高亮蓝）
- 副标题：甜妞维护 · Agent Skill 集 · 即装即用
- 统计行：饲养员：GreatBigM、甜妞 ｜ 多 agent 支持：Hermes / Claude Code / Codex ｜ 感谢各位游客老爷的投喂
- 页脚：安装说明 + generate.py 生成说明
- 背景：深色 #0d1117 + 蓝/绿双色 radial 渐变光晕
