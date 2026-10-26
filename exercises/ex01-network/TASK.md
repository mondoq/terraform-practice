# ex01: ネットワークを1つ作る（≒ VPC）

`main.tf` を**白紙から**書いて、次の Docker ネットワークを作ってください。

## 要件
| 項目 | 値 |
|---|---|
| プロバイダ | `kreuzwerker/docker`（バージョン `~> 3.0`） |
| リソース | `docker_network`、Terraform 上の名前は自由 |
| ネットワーク名 | `ex01-net` |
| サブネット | `10.10.0.0/24` |
| ゲートウェイ | `10.10.0.1` |
| output | `network_id` という名前でネットワークの ID を出す |

## 手順
```bash
cd ~/terraform-practice/exercises/ex01-network
vim main.tf          # 書く
terraform init
terraform apply
./check.sh           # 採点
terraform destroy    # 片付け
```

## 書くもの（4ブロック）
1. `terraform { required_providers { ... } }`
2. `provider "docker" {}`
3. `resource "docker_network" "..." { ... }` — サブネット指定は中に `ipam_config { }` ブロック
4. `output "network_id" { value = ... }` — 参照は `<リソース種別>.<名前>.<属性>`

<details><summary>詰まったら（ドキュメント）</summary>

https://registry.terraform.io/providers/kreuzwerker/docker/latest/docs/resources/network
（ページ下部の "Argument Reference" と "Attributes Reference" を見る）
</details>

## 発展
- ゲートウェイを直書きせず `cidrhost()` 関数で求める（`terraform console` で `cidrhost("10.10.0.0/24", 1)` を試せる）
