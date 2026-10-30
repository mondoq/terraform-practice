<!--
ここに書いた内容が、ポートフォリオの記事の「学んだこと」に載ります（Markdown で書けます）。
このコメントだけなら、記事には何も出ません。

書くことの例:
- 何を作ったか、自宅ネットワークや AWS でいうと何にあたるか
- 詰まったところと、どう解決したか
- 次に試したいこと
-->
terraform {
  required_version = ">=1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
　
AMIの設定:
　

### 構成図


