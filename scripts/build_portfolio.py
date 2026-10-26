#!/usr/bin/env python3
"""ポートフォリオページ _site/index.html を生成する。

入力: build/results/（scripts/grade.sh の採点結果）、各ディレクトリの .tf、git の履歴
"""
import collections
import datetime
import html
import os
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "build" / "results"
OUT = ROOT / "_site"
REPO = os.environ.get("GITHUB_REPOSITORY", "mondoq/terraform-practice")
REPO_URL = f"https://github.com/{REPO}"
JST = datetime.timezone(datetime.timedelta(hours=9))

STATUS_LABEL = {
    "pass": ("クリア", "pass"),
    "fail": ("挑戦中", "fail"),
    "todo": ("未着手", "todo"),
}
PROJECT_LABEL = {"pass": ("validate OK", "pass"), "fail": ("validate NG", "fail")}

e = html.escape


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def read(path):
    return path.read_text(encoding="utf-8") if path.exists() else ""


def status_of(name):
    return read(RESULTS / f"{name}.status").strip() or "todo"


def last_updated(path):
    ts = git("log", "-1", "--format=%cI", "--", str(path.relative_to(ROOT)))
    return ts[:10] if ts else "-"


def score(log):
    m = re.search(r"結果: (\d+) 合格 / (\d+) 不合格", log)
    return (int(m[1]), int(m[2])) if m else None


def code_blocks(dir_):
    parts = []
    for tf in sorted(dir_.glob("*.tf")):
        parts.append(
            f'<div class="file"><div class="fname">{e(tf.name)}</div>'
            f"<pre><code>{e(read(tf))}</code></pre></div>"
        )
    return "".join(parts)


def leading_comment(tf):
    lines = []
    for line in read(tf).splitlines():
        if not line.startswith("#"):
            break
        lines.append(re.sub(r"^# ?", "", line).rstrip())
    return lines


def exercise_cards():
    cards, cleared = [], 0
    dirs = sorted(p for p in (ROOT / "exercises").glob("ex*") if p.is_dir())
    for d in dirs:
        st = status_of(d.name)
        cleared += st == "pass"
        label, cls = STATUS_LABEL.get(st, STATUS_LABEL["todo"])
        title = read(d / "TASK.md").splitlines()[0].lstrip("# ") if (d / "TASK.md").exists() else d.name
        log = read(RESULTS / f"{d.name}.log")
        sc = score(log)
        meta = f"{sc[0]} / {sc[0] + sc[1]} チェック合格" if sc else ""
        body = ""
        if st != "todo":
            body = (
                f"<details><summary>コード</summary>{code_blocks(d)}</details>"
                f"<details><summary>採点結果</summary><pre class=\"log\">{e(log)}</pre></details>"
            )
        cards.append(
            f'<article class="card"><div class="row"><h3>{e(title)}</h3>'
            f'<span class="badge {cls}">{label}</span></div>'
            f'<p class="meta">{e(meta)}{" · " if meta else ""}最終更新 {last_updated(d)}</p>{body}</article>'
        )
    return "".join(cards), cleared, len(dirs)


def project_cards():
    cards = []
    for d in sorted(p for p in ROOT.glob("[0-9][0-9]-*") if p.is_dir()):
        label, cls = PROJECT_LABEL.get(status_of(d.name), PROJECT_LABEL["fail"])
        desc = leading_comment(d / "main.tf")
        headline = desc[0] if desc else d.name
        rest = "\n".join(desc[1:]).strip("\n")
        cards.append(
            f'<article class="card"><div class="row"><h3>{e(headline)}</h3>'
            f'<span class="badge {cls}">{label}</span></div>'
            f'<p class="meta"><code>{e(d.name)}/</code> · 最終更新 {last_updated(d)}</p>'
            f'{f"<pre class=desc>{e(rest)}</pre>" if rest else ""}'
            f"<details><summary>コード</summary>{code_blocks(d)}</details></article>"
        )
    return "".join(cards)


def activity():
    raw = git("log", "--format=%H%x09%cI%x09%s", "-n", "500")
    commits = [line.split("\t", 2) for line in raw.splitlines() if line]

    per_day = collections.Counter(c[1][:10] for c in commits)
    today = datetime.datetime.now(JST).date()
    start = today - datetime.timedelta(days=7 * 16 - 1 + (today.weekday() + 1) % 7)
    cells = []
    d = start
    while d <= today:
        n = per_day.get(d.isoformat(), 0)
        lv = 0 if n == 0 else 1 if n < 3 else 2 if n < 8 else 3
        cells.append(f'<i class="l{lv}" title="{d.isoformat()}: {n} commits"></i>')
        d += datetime.timedelta(days=1)

    rows = "".join(
        f'<li><time>{c[1][:16].replace("T", " ")}</time>'
        f'<a href="{REPO_URL}/commit/{c[0]}">{e(c[2].splitlines()[0])}</a></li>'
        for c in commits[:30]
    )
    return "".join(cells), rows, len(commits), len(per_day)


def main():
    ex_html, cleared, total = exercise_cards()
    heat, rows, n_commits, n_days = activity()
    now = datetime.datetime.now(JST).strftime("%Y-%m-%d %H:%M JST")

    page = TEMPLATE.format(
        repo=e(REPO),
        repo_url=REPO_URL,
        now=now,
        cleared=cleared,
        total=total,
        n_commits=n_commits,
        n_days=n_days,
        exercises=ex_html,
        projects=project_cards(),
        heat=heat,
        commits=rows,
    )
    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(page, encoding="utf-8")
    print(f"wrote {OUT / 'index.html'}")


TEMPLATE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Terraform Practice Portfolio</title>
<style>
:root {{
  --bg: #f7f7f5; --surface: #fff; --text: #1d1d1f; --muted: #6b6b70; --line: #e3e3e0;
  --accent: #5b3fd6; --pass: #1f8a4c; --fail: #b8640b; --todo: #8a8a8f;
  --code-bg: #f2f1ee; --h0: #e8e8e4; --h1: #c5b9f5; --h2: #8f76ea; --h3: #5b3fd6;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg: #141416; --surface: #1d1d20; --text: #ececee; --muted: #9c9ca3; --line: #2e2e33;
    --accent: #a593ff; --pass: #4cc98a; --fail: #f0a04b; --todo: #8a8a8f;
    --code-bg: #26262a; --h0: #26262a; --h1: #3d3470; --h2: #6450c4; --h3: #a593ff;
  }}
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--bg); color: var(--text);
  font: 15px/1.7 system-ui, -apple-system, "Hiragino Sans", "Noto Sans JP", sans-serif; }}
main {{ max-width: 960px; margin: 0 auto; padding: 48px 16px 64px; }}
header h1 {{ font-size: 28px; margin: 0 0 4px; letter-spacing: -0.01em; }}
header p {{ margin: 0; color: var(--muted); }}
a {{ color: var(--accent); }}
.stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin: 28px 0 8px; }}
.stat {{ background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 14px 16px; }}
.stat b {{ display: block; font-size: 26px; font-variant-numeric: tabular-nums; }}
.stat span {{ color: var(--muted); font-size: 13px; }}
h2 {{ font-size: 18px; margin: 44px 0 14px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 420px), 1fr)); gap: 14px; }}
.card {{ background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 16px 18px; min-width: 0; }}
.row {{ display: flex; gap: 12px; align-items: flex-start; justify-content: space-between; }}
.card h3 {{ font-size: 15px; margin: 0; }}
.meta {{ margin: 4px 0 0; color: var(--muted); font-size: 13px; }}
pre.desc {{ background: none; padding: 0; margin: 10px 0 0; color: var(--muted); white-space: pre-wrap; }}
.badge {{ flex: none; font-size: 12px; font-weight: 600; padding: 2px 10px; border-radius: 999px;
  border: 1px solid currentColor; }}
.badge.pass {{ color: var(--pass); }} .badge.fail {{ color: var(--fail); }} .badge.todo {{ color: var(--todo); }}
details {{ margin-top: 10px; }}
summary {{ cursor: pointer; font-size: 13px; color: var(--accent); }}
pre {{ background: var(--code-bg); border-radius: 8px; padding: 12px; overflow-x: auto;
  font: 12.5px/1.55 ui-monospace, SFMono-Regular, Menlo, monospace; margin: 6px 0 0; }}
.fname {{ font: 12px ui-monospace, monospace; color: var(--muted); margin-top: 10px; }}
.heat {{ display: grid; grid-auto-flow: column; grid-template-rows: repeat(7, 12px);
  grid-auto-columns: 12px; justify-content: start; gap: 3px;
  overflow-x: auto; padding-bottom: 4px; }}
.heat i {{ width: 12px; height: 12px; border-radius: 3px; background: var(--h0); }}
.heat .l1 {{ background: var(--h1); }} .heat .l2 {{ background: var(--h2); }} .heat .l3 {{ background: var(--h3); }}
.log-list {{ list-style: none; padding: 0; margin: 14px 0 0; }}
.log-list li {{ display: flex; gap: 14px; padding: 6px 0; border-bottom: 1px solid var(--line); font-size: 14px; }}
.log-list time {{ flex: none; color: var(--muted); font-variant-numeric: tabular-nums; font-size: 13px; }}
.log-list a {{ color: var(--text); text-decoration: none; overflow-wrap: anywhere; }}
.log-list a:hover {{ color: var(--accent); }}
footer {{ margin-top: 48px; color: var(--muted); font-size: 13px; }}
</style>
</head>
<body>
<main>
<header>
  <h1>Terraform Practice</h1>
  <p>クラウドネットワークエンジニアを目指して、IaC（Terraform）を自宅環境で練習した記録。
  コードを保存するたびに GitHub Actions が自動で採点し、このページを更新しています。</p>
</header>

<section class="stats">
  <div class="stat"><b>{cleared} / {total}</b><span>演習クリア</span></div>
  <div class="stat"><b>{n_commits}</b><span>コミット</span></div>
  <div class="stat"><b>{n_days}</b><span>活動日数</span></div>
</section>

<h2>演習（白紙からコードを書き、自動採点）</h2>
<div class="grid">{exercises}</div>

<h2>構築プロジェクト</h2>
<div class="grid">{projects}</div>

<h2>活動</h2>
<div class="card">
  <div class="heat" aria-label="直近16週間のコミット数">{heat}</div>
  <ul class="log-list">{commits}</ul>
</div>

<footer>最終更新 {now} · ソース <a href="{repo_url}">{repo}</a></footer>
</main>
</body>
</html>
"""

if __name__ == "__main__":
    main()
