# GreatBM'Zoo ★

甜妞维护的 Agent skill 市场 — 嵌入式 & 工作流技能集，一键安装。

**在线市场**: https://greatbigm.github.io/agent-skill-market/

## 已收录 skills

| skill | 版本 | 分类 | 说明 |
|-------|------|------|------|
| qwiki | v2.1.0 | knowledge | 个人知识库建设（知识卡片/检索/沉淀） |
| workbench-workflow | v3.1.0 | knowledge | 项目任务管理体系（change 四要素生命周期） |
| serial-tftp | v1.6.0 | devops | 嵌入式串口交互与 TFTP 刷机 |
| adb-tftp | v1.1.0 | devops | Ingenic T32 家族 ADB 通道 TFTP 烧录 |
| iperf-standard-test | v1.0.0 | devops | iperf3 标准吞吐测试方法论 |
| agent-skill-gen | v1.6.0 | autonomous-ai-agents | skill 生成构成规范 |
| agent-skill-review | v1.5.0 | autonomous-ai-agents | skill 审查（构成+发布前双清单） |
## 安装方法

任意 skill 一键安装（以 qwiki 为例）：

```bash
# 国内源（gitee）
curl -fsSL https://gitee.com/GreatBigM/qwiki-skill/raw/main/install.sh | bash
# 海外源（GitHub 镜像）
curl -fsSL https://raw.githubusercontent.com/GreatBigM/qwiki-skill/main/install.sh | bash
```

安装脚本自动探测本机 agent（Hermes / Claude Code / Codex / ZCode），支持：
- `--target hermes,claude,zcode` 指定目标
- `--all` 安装到全部
- 重复执行 = 升级（自动备份旧版 + 版本对比）

## 生成机制

- 页面由 `generate.py` 自动生成，**单一真相源 = 各 skill 发布仓库本身的 SKILL.md**
- 自动扫描 `$HOME` 下所有「含 SKILL.md + install.sh + .git」的发布仓
- 发新 skill：本地建仓发布 → 重跑 `python3 generate.py` → 自动入市场
- 生成产物：`index.html`（页面）+ `data.json`（机器可读，供 registry 消费）

```bash
python3 generate.py            # 本地扫描生成
python3 generate.py --remote   # 本地扫描 + gitee API 校验
```

## 仓库布局

```
agent-skill-market/
├── generate.py     # 生成器（自动发现）
├── index.html      # 生成产物：市场页面
├── data.json       # 生成产物：skill 元数据
└── README.md
```

## 对外发布约定

- 仓库作者身份：`GreatBigM <GreatBigM@users.noreply.github.com>`（公司邮箱不进公开历史）
- 双远端：gitee 主推 + GitHub 镜像
