# tflint の設定。terraform の文法チェック（validate）では拾えない
# 「動くけど良くない書き方」や AWS 固有の誤り（存在しないインスタンスタイプ等）を検出する。
plugin "terraform" {
  enabled = true
  preset  = "recommended"
}

plugin "aws" {
  enabled = true
  version = "0.40.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}
