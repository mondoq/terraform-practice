#!/usr/bin/env bash
# 練習成果を採点して build/results/ に書き出す（ポートフォリオ生成用）。
#   exercises/ex*/ … .tf があれば init → apply → check.sh → destroy
#   NN-*/          … init → validate（AWS 認証情報なしでできる範囲）
#
# apply / destroy を実行するので GitHub Actions 上でだけ動かす。
# 手元で動かすと、自分で apply 中の演習環境が destroy される。
set -u
cd "$(dirname "$0")/.." || exit 1

if [ -z "${CI:-}" ]; then
  echo "CI 専用のスクリプトです（手元の演習環境を destroy してしまうため）" >&2
  exit 1
fi

out=build/results
rm -rf "$out"
mkdir -p "$out"

strip_color() { sed -E 's/\x1b\[[0-9;]*m//g'; }

for dir in exercises/ex*/; do
  name=$(basename "$dir")
  echo "::group::$name"
  if ! ls "$dir"*.tf >/dev/null 2>&1; then
    echo todo >"$out/$name.status"
    echo "::endgroup::"
    continue
  fi

  if ! (cd "$dir" && terraform init -input=false -no-color && terraform apply -auto-approve -input=false -no-color) \
    >"$out/$name.apply.log" 2>&1; then
    echo "[apply でエラー]" >"$out/$name.log"
    tail -n 30 "$out/$name.apply.log" >>"$out/$name.log"
    echo >>"$out/$name.log"
  fi

  "$dir/check.sh" 2>&1 | strip_color | tee -a "$out/$name.log"
  if [ "${PIPESTATUS[0]}" -eq 0 ]; then echo pass; else echo fail; fi >"$out/$name.status"

  (cd "$dir" && terraform destroy -auto-approve -input=false -no-color) >/dev/null 2>&1
  echo "::endgroup::"
done

for dir in [0-9][0-9]-*/; do
  name=${dir%/}
  if (cd "$dir" && terraform init -backend=false -input=false -no-color && terraform validate -no-color) \
    >"$out/$name.log" 2>&1; then
    echo pass
  else
    echo fail
  fi >"$out/$name.status"
done

# 採点結果に関係なく成功で終わる（不合格もポートフォリオに載せるため）
exit 0
