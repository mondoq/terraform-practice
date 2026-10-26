# 採点スクリプト共通関数（各 check.sh から source される）

PASS=0
FAIL=0

ok()   { printf '  \e[32m✔\e[0m %s\n' "$1"; PASS=$((PASS + 1)); }
ng()   { printf '  \e[31m✘\e[0m %s\n' "$1"; [ -n "$2" ] && printf '      ヒント: %s\n' "$2"; FAIL=$((FAIL + 1)); }
step() { printf '\n\e[1m[%s]\e[0m\n' "$1"; }

# expect "説明" "期待値" "実際の値" ["ヒント"]
expect() {
  if [ "$2" = "$3" ]; then ok "$1"; else ng "$1（期待: '$2' / 実際: '$3'）" "$4"; fi
}

# コードの基本チェック: fmt / validate / state と現実の一致
check_basics() {
  step "コード"
  if ! ls ./*.tf >/dev/null 2>&1; then
    ng ".tf ファイルがない" "main.tf を作って書き始める"
    summary
  fi
  if terraform fmt -check >/dev/null 2>&1; then ok "terraform fmt 済み"; else ng "整形されていない" "terraform fmt を実行"; fi
  if terraform validate -no-color >/dev/null 2>&1; then
    ok "terraform validate が通る"
  else
    ng "terraform validate でエラー" "terraform validate を実行してエラーを読む"
    summary
  fi
  if [ -z "$(terraform state list 2>/dev/null)" ]; then
    ng "まだ何も apply されていない" "terraform apply を実行してから再チェック"
    summary
  fi
  terraform plan -detailed-exitcode -input=false -no-color >/dev/null 2>&1
  case $? in
    0) ok "コードと実環境が一致（plan の差分なし）" ;;
    2) ng "plan に差分がある" "コードを直したあと terraform apply したか？" ;;
    *) ng "plan がエラー" "terraform plan を実行して確認" ;;
  esac
}

summary() {
  printf '\n結果: \e[32m%d 合格\e[0m / \e[31m%d 不合格\e[0m\n' "$PASS" "$FAIL"
  if [ "$FAIL" -eq 0 ]; then printf '\e[32m🎉 クリア！\e[0m 終わったら terraform destroy\n'; fi
  exit "$FAIL"
}

# docker inspect の Go テンプレートで値を取り出す（存在しなければ空文字）
dget() { docker inspect -f "$2" "$1" 2>/dev/null; }
