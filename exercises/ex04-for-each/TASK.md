# ex04: for_each で台数を変数から増減させる

同じ設定のサーバーを「変数のマップ」から何台でも作れるようにします。
`docker_container` ブロックは **1つだけ** 書くこと。

## 要件
| 項目 | 値 |
|---|---|
| ネットワーク | `ex04-net`、`10.40.0.0/24` |
| 変数 `servers` | 下の型とデフォルト値 |
| コンテナ | キーごとに1台。名前 `ex04-<キー>`、IP は `cidrhost(サブネット, ip_suffix)`、80 → `127.0.0.1:<port>` |
| output `urls` | `{ web1 = "http://127.0.0.1:8091", ... }` のマップ |

```hcl
variable "servers" {
  type = map(object({
    ip_suffix = number
    port      = number
  }))
  default = {
    web1 = { ip_suffix = 11, port = 8091 }
    web2 = { ip_suffix = 12, port = 8092 }
    web3 = { ip_suffix = 13, port = 8093 }
  }
}
```

## 新しく使うもの
- `for_each = var.servers` と、その中で使える `each.key` / `each.value.port`
- for 式: `{ for k, c in docker_container.web : k => "..." }`
- 参照の形が変わる: `docker_container.web["web1"]`

<details><summary>詰まったら（ドキュメント）</summary>

- https://developer.hashicorp.com/terraform/language/meta-arguments/for_each
- https://developer.hashicorp.com/terraform/language/expressions/for
</details>

## クリア後にやること
1. `web2` を消して `terraform plan` → **web2 だけ**が destroy されるのを確認
2. 同じことを `count` で書いていたら、真ん中を消したときに何が起きるか考える（for_each が好まれる理由）
3. `terraform state list` で `docker_container.web["web1"]` という名前を確認
