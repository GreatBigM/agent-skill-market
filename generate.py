#!/usr/bin/env python3
"""hermes-skill-market 生成器 — 自动发现 + 自动同步

单一真相源 = 各 skill 发布仓库本身（~/<name>-skill/SKILL.md），网页只是渲染层。
自动发现：扫描 $HOME 下所有「含 SKILL.md + install.sh 的 git 目录」= 发布仓。
发新 skill：本地建仓发布 → 重跑本脚本 → 自动纳入市场，无需改任何配置。
用法:
  python3 generate.py            # 本地扫描生成
  python3 generate.py --remote   # 本地扫描 + gitee API 校验仓库存在/拿描述
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime

import yaml

HOME = os.path.expanduser("~")
GITEE_USER = "GreatBigM"
GITHUB_USER = "GreatBigM"


def is_publish_repo(d):
    """发布仓判据：目录下同时有 SKILL.md + install.sh + .git"""
    return (
        os.path.isdir(d)
        and os.path.isfile(os.path.join(d, "SKILL.md"))
        and os.path.isfile(os.path.join(d, "install.sh"))
        and os.path.isdir(os.path.join(d, ".git"))
    )


def discover_local():
    """扫描 $HOME 下所有发布仓目录名"""
    out = []
    for name in sorted(os.listdir(HOME)):
        d = os.path.join(HOME, name)
        if is_publish_repo(d):
            out.append(name)
    return out


def fetch_gitee_repos():
    """gitee API 拉取全部仓库（用于远端校验）"""
    repos = {}
    page = 1
    while True:
        url = (f"https://gitee.com/api/v5/users/{GITEE_USER}/repos"
               f"?per_page=100&page={page}&type=all&sort=updated")
        with urllib.request.urlopen(url, timeout=15) as r:
            batch = json.load(r)
        if not batch:
            break
        for b in batch:
            repos[b["name"]] = b.get("description") or ""
        if len(batch) < 100:
            break
        page += 1
    return repos


def parse_frontmatter(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def git_last_commit(repo_dir):
    try:
        return subprocess.run(
            ["git", "-C", repo_dir, "log", "-1", "--format=%ad", "--date=short"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
    except Exception:
        return ""


def collect(use_remote):
    names = discover_local()
    remote = fetch_gitee_repos() if use_remote else {}

    items = []
    for name in names:
        repo_dir = os.path.join(HOME, name)
        fm = parse_frontmatter(os.path.join(repo_dir, "SKILL.md"))
        hermes = fm.get("metadata", {}).get("hermes", {}) if isinstance(fm.get("metadata"), dict) else {}
        items.append({
            "name": fm.get("name", name),
            "description": fm.get("description", ""),
            "version": fm.get("version", ""),
            "category": fm.get("category", ""),
            "tags": hermes.get("tags", []),
            "triggers": hermes.get("triggers", []),
            "updated": git_last_commit(repo_dir),
            "gitee": f"https://gitee.com/{GITEE_USER}/{name}",
            "github": f"https://github.com/{GITHUB_USER}/{name}",
            "install_gitee": f"curl -fsSL https://gitee.com/{GITEE_USER}/{name}/raw/main/install.sh | bash",
            "install_github": f"curl -fsSL https://raw.githubusercontent.com/{GITHUB_USER}/{name}/main/install.sh | bash",
        })
        if use_remote:
            it = items[-1]
            it["remote_missing"] = name not in remote
            if name in remote and remote[name] and not it["description"]:
                it["description"] = remote[name]

    missing = [i["name"] for i in items if i.get("remote_missing")]
    if missing:
        print(f"⚠ 远端未找到（本地有但 gitee 无）: {', '.join(missing)}")
    return items


def render_html(items):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    cards = []
    for idx, it in enumerate(items):
        trig = " ".join(f'<span class="chip">{t}</span>' for t in it["triggers"][:6])
        ver = f'<span class="ver">v{it["version"]}</span>' if it["version"] else ""
        cat = f'<span class="cat">{it["category"]}</span>' if it["category"] else ""
        upd = f'<span class="upd">🔄 {it["updated"]}</span>' if it["updated"] else ""
        cards.append(f"""
    <div class="card" data-idx="{idx}">
      <div class="card-head">
        <h2>{it["name"]}</h2>
        <div class="badges">{ver}{cat}{upd}</div>
      </div>
      <p class="desc">{it["description"]}</p>
      <div class="triggers">{trig}</div>
      <div class="install">
        <div class="src-tabs">
          <button class="src-tab active" data-src="gitee" onclick="switchSrc(this, {idx})">gitee（国内）</button>
          <button class="src-tab" data-src="github" onclick="switchSrc(this, {idx})">GitHub（海外）</button>
        </div>
        <div class="cmd-row">
          <code class="cmd" id="cmd-{idx}">{it["install_gitee"]}</code>
          <button class="copy" onclick="copyCmd({idx})">复制</button>
        </div>
      </div>
      <div class="links">
        <a href="{it["gitee"]}" target="_blank">gitee 仓库 ↗</a>
        <a href="{it["github"]}" target="_blank">GitHub 镜像 ↗</a>
      </div>
    </div>""")
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hermes Skill Market — 甜妞的 Skill 市场</title>
<style>
  :root {{
    --bg: #0f1117; --card: #1a1d27; --card-hover: #20242f; --border: #2a2e3d;
    --text: #e8eaf0; --dim: #9aa0b0; --accent: #7c9cff; --accent2: #5fd0a0;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font: 15px/1.6 -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; padding: 40px 20px 80px; }}
  .wrap {{ max-width: 1100px; margin: 0 auto; }}
  header {{ text-align: center; margin-bottom: 40px; }}
  h1 {{ font-size: 32px; letter-spacing: 1px; }}
  h1 .hl {{ color: var(--accent); }}
  .sub {{ color: var(--dim); margin-top: 8px; }}
  .stats {{ display: inline-flex; gap: 24px; margin-top: 14px; color: var(--accent2); font-size: 14px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(480px, 1fr)); gap: 18px; }}
  .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px 22px; transition: transform .15s, border-color .15s; }}
  .card:hover {{ transform: translateY(-2px); border-color: var(--accent); background: var(--card-hover); }}
  .card-head {{ display: flex; align-items: baseline; justify-content: space-between; gap: 10px; flex-wrap: wrap; }}
  .card-head h2 {{ font-size: 19px; font-family: ui-monospace, "Cascadia Code", Consolas, monospace; }}
  .badges {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  .ver {{ color: var(--accent2); font-family: ui-monospace, monospace; font-size: 13px; background: rgba(95,208,160,.1); padding: 2px 8px; border-radius: 20px; }}
  .cat {{ color: #c9a0ff; font-size: 12px; background: rgba(201,160,255,.12); padding: 2px 8px; border-radius: 20px; }}
  .upd {{ color: var(--dim); font-size: 12px; }}
  .desc {{ color: #c6cad6; margin: 12px 0 10px; font-size: 14px; }}
  .triggers {{ display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; min-height: 26px; }}
  .chip {{ font-size: 12px; color: var(--dim); background: #242837; border: 1px solid var(--border); border-radius: 4px; padding: 1px 7px; }}
  .install {{ border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }}
  .src-tabs {{ display: flex; background: #14161f; }}
  .src-tab {{ flex: 1; background: none; border: none; color: var(--dim); padding: 7px 0; cursor: pointer; font-size: 13px; border-bottom: 2px solid transparent; }}
  .src-tab.active {{ color: var(--accent); border-bottom-color: var(--accent); background: rgba(124,156,255,.08); }}
  .cmd-row {{ display: flex; align-items: center; background: #10131b; }}
  .cmd {{ flex: 1; font-family: ui-monospace, Consolas, monospace; font-size: 12.5px; color: #a8e6cf; padding: 10px 12px; overflow-x: auto; white-space: nowrap; }}
  .copy {{ background: var(--accent); color: #0b0e14; border: none; border-radius: 6px; margin: 6px 8px; padding: 6px 14px; cursor: pointer; font-size: 13px; font-weight: 600; }}
  .copy:hover {{ filter: brightness(1.15); }}
  .links {{ margin-top: 10px; display: flex; gap: 16px; font-size: 13px; }}
  .links a {{ color: var(--accent); text-decoration: none; }}
  .links a:hover {{ text-decoration: underline; }}
  footer {{ text-align: center; color: var(--dim); font-size: 13px; margin-top: 50px; }}
  footer code {{ background: #1a1d27; padding: 1px 6px; border-radius: 4px; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Hermes <span class="hl">Skill Market</span> ★</h1>
    <p class="sub">甜妞维护 · 嵌入式 & 工作流 skill 集 · 安装命令即装即用</p>
    <div class="stats">
      <span>{len(items)} skills</span>
      <span>多 agent 支持：Hermes / Claude Code / Codex</span>
      <span>更新于 {now}</span>
    </div>
  </header>
  <div class="grid">
{''.join(cards)}
  </div>
  <footer>
    安装 = 复制命令到终端执行（<code>--all</code> 装到全部检测到的 agent，重跑即升级）。
    页面由 <code>generate.py</code> 自动扫描本地发布仓生成，发新 skill 建仓即自动入市场。
  </footer>
</div>
<script>
function switchSrc(btn, idx) {{
  const tabs = btn.parentElement.children;
  for (const t of tabs) t.classList.remove("active");
  btn.classList.add("active");
  const cmds = {json.dumps([it["install_gitee"] for it in items])};
  const giteeCmds = {json.dumps([it["install_gitee"] for it in items])};
  const githubCmds = {json.dumps([it["install_github"] for it in items])};
  const code = btn.dataset.src === "gitee" ? giteeCmds[idx] : githubCmds[idx];
  document.querySelector(`#cmd-${{idx}}`).textContent = code;
}}
function copyCmd(idx) {{
  const cmd = document.querySelector(`#cmd-${{idx}}`).textContent;
  navigator.clipboard.writeText(cmd).then(() => {{
    const b = document.querySelector(`.card[data-idx="${{idx}}"] .copy`);
    const old = b.textContent;
    b.textContent = "✅ 已复制";
    setTimeout(() => b.textContent = old, 1500);
  }});
}}
</script>
</body>
</html>"""


def main():
    use_remote = "--remote" in sys.argv
    items = collect(use_remote)
    out_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_html(items))
    with open(os.path.join(out_dir, "data.json"), "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"✅ 自动发现 {len(items)} 个 skill 发布仓 → index.html + data.json")
    for it in items:
        mark = " ⚠" if it.get("remote_missing") else ""
        print(f"   {it['name']:<24} v{it['version']:<8} {it['category']}{mark}")


if __name__ == "__main__":
    main()
