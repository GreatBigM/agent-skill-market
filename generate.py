#!/usr/bin/env python3
"""hermes-skill-market 生成器 — 自动发现 + 自动同步

单一真相源 = 各 skill 发布仓库本身（~/<name>-skill/SKILL.md），网页只是渲染层。
卡片规格真相源 = SPEC.md（本文件与 SPEC.md 冲突时以 SPEC.md 为准，需同步修正）。
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


def _github_token():
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        return token
    try:
        with open(os.path.join(HOME, ".hermes", ".env"), encoding="utf-8") as f:
            for line in f:
                if line.startswith("GITHUB_TOKEN="):
                    return line.strip().split("=", 1)[1]
    except Exception:
        pass
    return ""


def fetch_github_stars(names):
    """GitHub API 拉取各仓库 star 数（失败静默置 None，不阻塞生成）"""
    token = _github_token()
    result = {}
    for n in names:
        req = urllib.request.Request(f"https://api.github.com/repos/{GITHUB_USER}/{n}",
                                     headers={"Accept": "application/vnd.github+json"})
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                result[n] = json.load(r).get("stargazers_count")
        except Exception:
            result[n] = None
    return result


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
    stars = fetch_github_stars(names)

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
            "stars": stars.get(name),
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
    cards = []
    for idx, it in enumerate(items):
        trig = " ".join(f'<span class="chip">{t}</span>' for t in it["triggers"][:5])
        ver = f'<span class="ver">v{it["version"]}</span>' if it["version"] else ""
        cat = f'<span class="cat">{it["category"]}</span>' if it["category"] else ""
        stars = f'<span class="stars">★ {it["stars"]}</span>' if it.get("stars") else ""
        github = it["github"]
        cards.append(f"""
    <div class="card" data-idx="{idx}">
      <div class="card-head">
        <h2>{it["name"]}</h2>
        {stars}
      </div>
      <div class="badges">{ver}{cat}</div>
      <div class="body">
        <div class="triggers">{trig}</div>
        <p class="desc">{it["description"]}</p>
      </div>
      <div class="card-foot">
        <div class="social">
          <a class="btn" href="{github}/stargazers" target="_blank" rel="noopener">★ Star</a>
          <a class="btn" href="{github}/fork" target="_blank" rel="noopener">⑂ Fork</a>
        </div>
        <button class="copy" onclick="copyCmd({idx})">⧉ Copy</button>
      </div>
    </div>""")
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GreatBM'Zoo — Hermes Skill Market</title>
<style>
  :root {{
    --bg: #0d1117; --card: #161b26; --border: #232a3a;
    --text: #e6edf3; --dim: #8b949e; --accent: #58a6ff; --accent2: #3fb950;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ color: var(--text); font: 15px/1.6 -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; padding: 40px 20px 80px; background:
    radial-gradient(1100px 520px at 15% -5%, rgba(88,166,255,.10), transparent 60%),
    radial-gradient(900px 480px at 105% 5%, rgba(63,185,80,.07), transparent 55%),
    var(--bg); }}
  .wrap {{ max-width: 1100px; margin: 0 auto; }}
  header {{ text-align: center; margin-bottom: 40px; }}
  h1 {{ font-size: 32px; letter-spacing: 1px; }}
  h1 .hl {{ color: var(--accent); }}
  .sub {{ color: var(--dim); margin-top: 8px; }}
  .stats {{ display: inline-flex; gap: 24px; margin-top: 14px; color: var(--accent2); font-size: 14px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; grid-auto-rows: 1fr; }}
  .card {{ background: linear-gradient(180deg, rgba(255,255,255,.03), transparent 40%), var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 22px 20px 16px; position: relative; overflow: hidden; transition: transform .18s, border-color .18s, box-shadow .18s; height: 100%; min-height: 340px; display: flex; flex-direction: column; }}
  .card::before {{ content: ""; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, var(--accent), transparent 65%); opacity: 0; transition: opacity .18s; }}
  .card:hover {{ transform: translateY(-3px); border-color: rgba(88,166,255,.5); box-shadow: 0 10px 26px rgba(0,0,0,.45); }}
  .card:hover::before {{ opacity: 1; }}
  .card-head {{ display: flex; align-items: center; justify-content: space-between; gap: 8px; }}
  .card-head h2 {{ font-size: 18px; font-family: ui-monospace, "Cascadia Code", Consolas, monospace; color: var(--text); letter-spacing: .3px; }}
  .stars {{ color: #e3b341; font-size: 13px; font-weight: 600; background: rgba(227,179,65,.12); border: 1px solid rgba(227,179,65,.35); padding: 2px 10px; border-radius: 20px; }}
  .badges {{ display: flex; gap: 6px; margin-top: 5px; }}
  .ver {{ color: var(--accent2); font-family: ui-monospace, monospace; font-size: 12.5px; background: rgba(63,185,80,.12); border: 1px solid rgba(63,185,80,.25); padding: 1px 9px; border-radius: 20px; }}
  .cat {{ color: #c9a0ff; font-size: 11.5px; background: rgba(201,160,255,.12); border: 1px solid rgba(201,160,255,.25); padding: 1px 9px; border-radius: 20px; }}
  .triggers {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 10px; }}
  .chip {{ font-size: 11.5px; color: #a5b3c2; background: #1e2534; border: 1px solid #2a3346; border-radius: 6px; padding: 1px 8px; white-space: nowrap; }}
  .body {{ border-top: 1px solid var(--border); margin-top: 12px; padding-top: 12px; flex: 1; display: flex; flex-direction: column; }}
  .desc {{ color: var(--dim); font-size: 13.5px; line-height: 1.7; margin: 0 0 16px; flex: 1; }}
  .card-foot {{ display: flex; align-items: center; justify-content: space-between; gap: 8px; border-top: 1px solid var(--border); padding-top: 13px; }}
  .social {{ display: flex; gap: 6px; }}
  .btn {{ display: inline-flex; align-items: center; gap: 4px; font-size: 12.5px; color: var(--text); background: #1c2333; border: 1px solid #2b3346; border-radius: 6px; padding: 5px 11px; text-decoration: none; transition: border-color .15s, color .15s, background .15s; }}
  .btn:hover, .copy:hover {{ border-color: var(--accent); color: var(--accent); background: rgba(88,166,255,.08); }}
  .copy {{ display: inline-flex; align-items: center; gap: 4px; font-size: 12.5px; color: var(--text); background: #1c2333; border: 1px solid #2b3346; border-radius: 6px; padding: 5px 11px; cursor: pointer; transition: border-color .15s, color .15s, background .15s, transform .1s; }}
  .copy:active {{ transform: scale(.97); }}
  footer {{ text-align: center; color: var(--dim); font-size: 13px; margin-top: 50px; }}
  footer code {{ background: #1a1d27; padding: 1px 6px; border-radius: 4px; }}
  .legal {{ margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--border); font-size: 12px; color: #6b7480; }}
  .legal div + div {{ margin-top: 6px; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>GreatBM'<span class="hl">Zoo</span></h1>
    <p class="sub">甜妞维护 · Agent Skill 集 · 即装即用</p>
    <div class="stats">
      <span>饲养员：GreatBigM、甜妞</span>
      <span>多 agent 支持：Hermes / Claude Code / Codex</span>
      <span>感谢各位游客老爷的投喂</span>
    </div>
  </header>
  <div class="grid">
{''.join(cards)}
  </div>
  <footer>
    页面由 <code>generate.py</code> 自动扫描本地发布仓生成，发新 skill 建仓即自动入市场。
    <div class="legal">
      <div>© 2026 GreatBigM 版权所有 ｜ 本站 skill 均基于 MIT 协议开源</div>
      <div>免责声明：所有 skill 按「现状」提供，不附任何担保；烧录/调试等操作风险自负，作者不承担由此产生的任何损失</div>
      <div>安全提示：安装命令源自各 skill 官方仓库，执行前可查看 install.sh；请仅从本站及官方仓库安装，谨防仿冒</div>
      <div>隐私保护：本站为纯静态页面，不收集任何用户信息，不设 Cookie，无第三方跟踪 ｜ Hermes、Claude Code、Codex 等商标归各自所有者所有</div>
    </div>
  </footer>
</div>
<script>
const CMDS = {{
  "github": {json.dumps([it["install_github"] for it in items])},
  "gitee": {json.dumps([it["install_gitee"] for it in items])}
}};
function copyCmd(idx) {{
  const src = location.hostname.includes("gitee.io") ? "gitee" : "github";
  navigator.clipboard.writeText(CMDS[src][idx]).then(() => {{
    const b = document.querySelector(`.card[data-idx="${{idx}}"] .copy`);
    const old = b.textContent;
    b.textContent = "✅ Copied";
    setTimeout(() => b.textContent = "⧉ Copy", 2000);
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
