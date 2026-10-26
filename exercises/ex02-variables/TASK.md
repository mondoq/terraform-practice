# ex02: 変数・バリデーション・output（≒ EC2 ＋ ポート公開）

ネットワーク内に nginx コンテナを1台立て、公開設定を**変数で切り替えられる**ようにします。
今回は `main.tf` / `variables.tf` / `outputs.tf` に分けて書いてください（1ファイルでも動きますが、分けるのが慣習）。

## 要件
| 項目 | 値 |
|---|---|
| ネットワーク | 名前 `ex02-net`、サブネット `10.20.0.0/24` |
| イメージ | `nginx:1.27-alpine`（`docker_image` リソース） |
| コンテナ | 名前 `ex02-web`、`ex02-net` 上の IP `10.20.0.10` |
| ポート | コンテナの 80 → ホストの `var.host_port` に、`var.bind_ip` で待ち受け |
| 変数 `host_port` | number、デフォルト `8081` |
| 変数 `bind_ip` | string、デフォルト `"127.0.0.1"`。**`127.0.0.1` か `0.0.0.0` 以外はエラーにする** |
| output `url` | `http://127.0.0.1:8081` の形の文字列（変数から組み立てる） |

## 新しく使うもの
- `variable` ブロックの `type` / `default` / `validation { condition = ... error_message = ... }`
- `contains(["a", "b"], var.x)` 関数
- 文字列補間 `"http://${var.bind_ip}:${var.host_port}"`
- `docker_container` の `networks_advanced { }` と `ports { }` ブロック

<details><summary>詰まったら（ドキュメント）</summary>

- https://registry.terraform.io/providers/kreuzwerker/docker/latest/docs/resources/container
- https://developer.hashicorp.com/terraform/language/values/variables#custom-validation-rules
</details>

## 確認してみること
- `terraform plan -var bind_ip=192.168.0.1` → 自分で書いた error_message が出るか
- `terraform apply -var host_port=8082` → plan で `-/+`（作り直し）になるのはなぜか
