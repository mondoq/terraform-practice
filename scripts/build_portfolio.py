#!/usr/bin/env python3
"""ポートフォリオ（記事形式）を _site/ に生成する。

  _site/index.html        … 記事一覧
  _site/posts/<名前>.html  … 演習・プロジェクトごとの記事

記事の材料:
  TASK.md   … 課題（「手順」の節は手元の作業メモなので除く）
  *.tf      … 書いたコード
  NOTE.md   … 自分の一言（任意。空なら節ごと出さない）
  build/results/ … scripts/grade.sh の採点結果
  git log   … 公開日・更新日・変更履歴
プロフィールはリポジトリ直下の PROFILE.md（1行目の見出しが名前、残りが自己紹介）。
"""
import datetime
import html
import os
import pathlib
import re
import shutil
import subprocess
import zlib

import markdown

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "build" / "results"
OUT = ROOT / "_site"
REPO = os.environ.get("GITHUB_REPOSITORY", "mondoq/terraform-practice")
REPO_URL = f"https://github.com/{REPO}"
JST = datetime.timezone(datetime.timedelta(hours=9))

e = html.escape


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def read(path):
    return path.read_text(encoding="utf-8") if path.exists() else ""


def md(text, demote=0):
    """demote: 記事の節（h2）の下に入れるため、見出しを何段下げるか"""
    if demote:
        text = re.sub(r"^(#{1,5}) ", lambda m: "#" * (len(m[1]) + demote) + " ", text, flags=re.M)
    return markdown.markdown(text, extensions=["tables", "fenced_code"])


def jp_date(iso):
    return f"{int(iso[:4])}年{int(iso[5:7])}月{int(iso[8:10])}日" if iso else ""


def dir_dates(d):
    """(公開日, 更新日) = そのディレクトリの最初と最後のコミット日"""
    log = git("log", "--format=%cI", "--", str(d.relative_to(ROOT))).splitlines()
    return (log[-1][:10], log[0][:10]) if log else ("", "")


def history(d):
    raw = git("log", "--format=%H%x09%cI%x09%s", "--", str(d.relative_to(ROOT)))
    items = []
    for line in raw.splitlines()[:20]:
        sha, ts, subject = line.split("\t", 2)
        items.append(
            f'<li><time>{ts[:16].replace("T", " ")}</time>'
            f'<a href="{REPO_URL}/commit/{sha}">{e(subject)}</a></li>'
        )
    return f'<ul class="history">{"".join(items)}</ul>' if items else ""


def note_html(d):
    text = re.sub(r"<!--.*?-->", "", read(d / "NOTE.md"), flags=re.S).strip()
    return md(text, demote=1) if text else ""


def task_html(d):
    text = read(d / "TASK.md")
    text = re.sub(r"\A# .*\n", "", text)  # タイトルは記事見出しに使う
    text = re.sub(r"^## 手順\n.*?(?=^## |\Z)", "", text, flags=re.S | re.M)
    return md(text, demote=1)


def code_html(d):
    return "".join(
        f'<figure class="code"><figcaption>{e(tf.name)}</figcaption>'
        f"<pre><code>{e(read(tf))}</code></pre></figure>"
        for tf in sorted(d.glob("*.tf"))
    )


def leading_comment(tf):
    lines = []
    for line in read(tf).splitlines():
        if not line.startswith("#"):
            break
        lines.append(re.sub(r"^# ?", "", line).rstrip())
    return lines


def section(title, body):
    return f"<h2>{title}</h2>{body}" if body else ""


def exercise_articles():
    for d in sorted(p for p in (ROOT / "exercises").glob("ex*") if p.is_dir()):
        status = read(RESULTS / f"{d.name}.status").strip()
        if status not in ("pass", "fail"):
            continue  # 未着手は記事にしない
        log = read(RESULTS / f"{d.name}.log")
        m = re.search(r"結果: (\d+) 合格 / (\d+) 不合格", log)
        score = f" {m[1]}/{int(m[1]) + int(m[2])}" if m else ""
        title = read(d / "TASK.md").splitlines()[0].lstrip("# ") if (d / "TASK.md").exists() else d.name
        published, updated = dir_dates(d)
        yield {
            "slug": d.name,
            "kind": "演習",
            "title": title,
            "chip": ("クリア" if status == "pass" else "挑戦中") + score,
            "chip_cls": status,
            "published": published,
            "updated": updated,
            "body": "".join([
                section("課題", task_html(d)),
                section("書いたコード", code_html(d)),
                section("学んだこと", note_html(d)),
                section("自動採点の結果", f'<pre class="log">{e(log)}</pre>'),
                section("変更履歴", history(d)),
            ]),
        }


def project_articles():
    for d in sorted(p for p in ROOT.glob("[0-9][0-9]-*") if p.is_dir()):
        status = read(RESULTS / f"{d.name}.status").strip()
        desc = leading_comment(d / "main.tf")
        overview = "\n".join(desc[1:]).strip("\n")
        published, updated = dir_dates(d)
        yield {
            "slug": d.name,
            "kind": "構築",
            "title": re.sub(r"^演習\d+:\s*", "", desc[0]) if desc else d.name,
            "chip": "validate OK" if status == "pass" else "validate NG",
            "chip_cls": "pass" if status == "pass" else "fail",
            "published": published,
            "updated": updated,
            "body": "".join([
                section("構成", f'<pre class="plain">{e(overview)}</pre>' if overview else ""),
                section("学んだこと", note_html(d)),
                section("コード", code_html(d)),
                section("変更履歴", history(d)),
            ]),
        }


def eyecatch(a, cls="eyecatch"):
    hue = zlib.crc32(a["slug"].encode()) % 360
    return (
        f'<div class="{cls}" style="--h:{hue}" aria-hidden="true">'
        f'<span class="eye-kind">{a["kind"]} · Terraform</span>'
        f'<span class="eye-title">{e(a["title"])}</span></div>'
    )


def profile():
    text = read(ROOT / "PROFILE.md")
    m = re.match(r"# (.+)\n", text)
    name = m[1].strip() if m else REPO.split("/")[0]
    bio = md(text[m.end():].strip()) if m else ""
    return name, bio


def page(title, body, depth=0):
    base = "../" * depth
    return PAGE.format(title=e(title), body=body, base=base)


def main():
    articles = sorted(
        [*exercise_articles(), *project_articles()],
        key=lambda a: (a["updated"], a["slug"]),
        reverse=True,
    )
    name, bio = profile()
    avatar = e(name[:1].upper())
    now = datetime.datetime.now(JST).strftime("%Y-%m-%d %H:%M")

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "posts").mkdir(parents=True)
    (OUT / "style.css").write_text(CSS, encoding="utf-8")

    for a in articles:
        updated = (
            f" · {jp_date(a['updated'])} 更新" if a["updated"] and a["updated"] != a["published"] else ""
        )
        body = f"""
<nav class="top"><a href="../index.html">← {e(name)} の記事一覧</a></nav>
<article class="post">
  {eyecatch(a)}
  <h1>{e(a["title"])}</h1>
  <div class="byline">
    <span class="avatar">{avatar}</span>
    <div><b>{e(name)}</b><br><span class="muted">{jp_date(a["published"])}{updated}</span></div>
    <span class="chip {a["chip_cls"]}">{e(a["chip"])}</span>
  </div>
  <div class="content">{a["body"]}</div>
</article>
<footer>このページは push のたびに GitHub Actions が自動採点・生成しています（{now} JST）· <a href="{REPO_URL}">ソース</a></footer>
"""
        (OUT / "posts" / f"{a['slug']}.html").write_text(page(a["title"], body, depth=1), encoding="utf-8")

    cards = "".join(
        f"""<a class="card" href="posts/{a["slug"]}.html">
  {eyecatch(a, "thumb")}
  <div class="card-body">
    <h2>{e(a["title"])}</h2>
    <div class="card-meta"><span class="muted">{jp_date(a["updated"] or a["published"])}</span>
    <span class="chip {a["chip_cls"]}">{e(a["chip"])}</span></div>
  </div>
</a>"""
        for a in articles
    ) or '<p class="muted">まだ記事がありません。</p>'

    index = f"""
<header class="profile">
  <span class="avatar big">{avatar}</span>
  <h1>{e(name)}</h1>
  <div class="bio">{bio}</div>
  <p class="muted small">{len(articles)} 本の記事 · <a href="{REPO_URL}">GitHub</a></p>
</header>
<section class="cards">{cards}</section>
<footer>最終更新 {now} JST</footer>
"""
    (OUT / "index.html").write_text(page(f"{name} の Terraform 練習記録", index), encoding="utf-8")
    print(f"wrote {len(articles)} articles to {OUT}")


PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="{base}style.css">
</head>
<body><main>{body}</main></body>
</html>
"""

CSS = """
:root {
  --bg: #ffffff; --text: #08131a; --muted: #6b7680; --line: #e6e8ea;
  --accent: #1a7f6e; --code-bg: #f5f6f7; --pass: #1a7f4b; --fail: #b25c00;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #15181b; --text: #e8eaec; --muted: #98a2ab; --line: #2c3237;
    --accent: #5cc8b4; --code-bg: #1f2428; --pass: #57c98c; --fail: #f0a04b;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text);
  font: 16px/1.9 "Hiragino Sans", "Noto Sans JP", system-ui, sans-serif; }
main { max-width: 1000px; margin: 0 auto; padding: 32px 16px 64px; }
a { color: var(--accent); }
.muted { color: var(--muted); }
.small { font-size: 13px; }

.avatar { display: inline-grid; place-items: center; flex: none; width: 40px; height: 40px;
  border-radius: 50%; background: var(--accent); color: var(--bg); font-weight: 700; }
.avatar.big { width: 72px; height: 72px; font-size: 30px; }
.chip { flex: none; font-size: 12px; font-weight: 600; padding: 0 10px; border-radius: 999px;
  border: 1px solid currentColor; line-height: 22px; white-space: nowrap; }
.chip.pass { color: var(--pass); } .chip.fail { color: var(--fail); }

/* 一覧 */
.profile { text-align: center; padding: 24px 0 36px; border-bottom: 1px solid var(--line); margin-bottom: 32px; }
.profile h1 { font-size: 22px; margin: 12px 0 4px; }
.bio { max-width: 560px; margin: 0 auto; color: var(--muted); font-size: 14px; }
.bio p { margin: 4px 0; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 280px), 1fr)); gap: 28px 24px; }
.card { color: inherit; text-decoration: none; display: block; min-width: 0; }
.card:hover h2 { color: var(--accent); }
.card-body { padding-top: 12px; }
.card h2 { font-size: 16px; line-height: 1.6; margin: 0 0 8px; }
.card-meta { display: flex; gap: 10px; align-items: center; justify-content: space-between; font-size: 13px; }

/* アイキャッチ（記事ごとに色が変わる） */
.thumb, .eyecatch { display: flex; flex-direction: column; justify-content: flex-end; gap: 4px;
  aspect-ratio: 1.91 / 1; border-radius: 10px; padding: 18px 20px; color: #fff; overflow: hidden;
  background: linear-gradient(135deg, hsl(var(--h) 55% 38%), hsl(calc(var(--h) + 40) 60% 52%)); }
.eye-kind { font-size: 12px; opacity: .85; letter-spacing: .04em; }
.eye-title { font-weight: 700; font-size: 17px; line-height: 1.5; }
.eyecatch .eye-title { font-size: clamp(20px, 4vw, 30px); }

/* 記事 */
nav.top { max-width: 680px; margin: 0 auto 20px; font-size: 14px; }
nav.top a { color: var(--muted); text-decoration: none; }
.post { max-width: 680px; margin: 0 auto; }
.post h1 { font-size: clamp(24px, 4.5vw, 32px); line-height: 1.5; margin: 28px 0 16px; }
.byline { display: flex; gap: 12px; align-items: center; font-size: 14px; line-height: 1.5;
  padding-bottom: 24px; border-bottom: 1px solid var(--line); }
.byline .chip { margin-left: auto; }
.content h2 { font-size: 22px; margin: 48px 0 12px; padding-bottom: 6px; border-bottom: 2px solid var(--text); }
.content h3 { font-size: 18px; margin: 28px 0 8px; }
.content table { border-collapse: collapse; width: 100%; font-size: 14px; display: block; overflow-x: auto; }
.content th, .content td { border: 1px solid var(--line); padding: 6px 10px; text-align: left; }
.content th { background: var(--code-bg); }
.content code { background: var(--code-bg); padding: 1px 5px; border-radius: 4px; font-size: .9em; }
.content pre { background: var(--code-bg); border-radius: 8px; padding: 14px 16px; overflow-x: auto;
  font: 13px/1.6 ui-monospace, SFMono-Regular, Menlo, monospace; }
.content pre code { background: none; padding: 0; font-size: inherit; }
.content pre.plain { background: none; padding: 0; white-space: pre-wrap; font-size: 14px; }
.content details { margin: 12px 0; }
.code { margin: 16px 0; }
.code figcaption { font: 12px ui-monospace, monospace; color: var(--muted); }
.code pre { margin: 4px 0 0; }
.history { list-style: none; padding: 0; font-size: 14px; }
.history li { display: flex; gap: 14px; padding: 6px 0; border-bottom: 1px solid var(--line); }
.history time { flex: none; color: var(--muted); font-variant-numeric: tabular-nums; }
.history a { color: inherit; text-decoration: none; overflow-wrap: anywhere; }
.history a:hover { color: var(--accent); }

footer { max-width: 680px; margin: 64px auto 0; color: var(--muted); font-size: 12px; text-align: center; }
"""

if __name__ == "__main__":
    main()
