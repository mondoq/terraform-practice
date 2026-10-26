#!/usr/bin/env bash
# 変更を見張って、自動でコミット → push する（GitDoc の代わり）。
#   - 10 秒ごとに git status を見る
#   - 最後の変更から 5 秒たったら（保存が落ち着いたら）コミットする
#   - 秘密情報らしき文字列が含まれていたらコミットしない（公開リポジトリのため）
#
# 起動・停止は systemd のユーザーサービス（scripts/autosync.service を登録）で行う:
#   systemctl --user status autosync    # 状態
#   journalctl --user -u autosync -f    # ログ
#   systemctl --user stop autosync      # 一時停止
set -u

REPO=${1:-$HOME/terraform-practice}
INTERVAL=10
QUIET=5
SECRET_PATTERN='AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|aws_secret_access_key[[:space:]]*=|-----BEGIN [A-Z ]*PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{36}'

cd "$REPO" || exit 1
echo "watching $REPO"

push_if_ahead() {
  [ -z "$(git rev-list '@{u}..HEAD' 2>/dev/null)" ] && return
  if git push -q 2>/dev/null; then
    echo "push"
  # GitHub 側が先に進んでいたら（Dependabot のマージなど）取り込んでから再送
  elif git pull -q --rebase --autostash && git push -q; then
    echo "push (pull してから)"
  else
    echo "push 失敗。次の周期で再試行"
  fi
}

while sleep "$INTERVAL"; do
  # rebase やマージの途中なら手を出さない
  [ -d .git/rebase-merge ] || [ -d .git/rebase-apply ] || [ -f .git/MERGE_HEAD ] && continue

  if [ -n "$(git status --porcelain)" ]; then
    # 保存中・連続編集中はまだコミットしない
    newest=$(git ls-files -mo --exclude-standard -z | xargs -0 -r stat -c %Y 2>/dev/null | sort -n | tail -1)
    [ -n "$newest" ] && [ $(($(date +%s) - newest)) -lt "$QUIET" ] && continue

    git add -A
    if git diff --cached -U0 | grep '^+' | grep -qE "$SECRET_PATTERN"; then
      echo "秘密情報らしき文字列があるためコミットしません。該当ファイル:"
      git diff --cached -U0 -G "$SECRET_PATTERN" --name-only
      git reset -q
      sleep 50 # 同じ警告でログが埋まらないように
      continue
    fi

    files=$(git diff --cached --name-only)
    count=$(echo "$files" | wc -l)
    msg="$(date '+%Y-%m-%d %H:%M') $(echo "$files" | head -1)"
    [ "$count" -gt 1 ] && msg="$msg ほか $((count - 1)) 件"
    git commit -q -m "$msg" && echo "commit: $msg"
  fi

  push_if_ahead
done
