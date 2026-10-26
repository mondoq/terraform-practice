# ex03: パブリック／プライベートの2層構成

AWS の定番「Web は public、DB は private」を Docker で再現します。

```
            ホスト（インターネット側）
                  │ 127.0.0.1:8083
   ┌── ex03-public 10.30.1.0/24 ──┐
   │      web 10.30.1.10          │
   └──────────┬───────────────────┘
              │ web は両方に足を出す
   ┌── ex03-private 10.30.11.0/24 (internal) ──┐
   │      web 10.30.11.10    db 10.30.11.20    │
   └────────────────────────────────────────────┘
```

## 要件
| 項目 | 値 |
|---|---|
| ネットワーク1 | `ex03-public`、`10.30.1.0/24` |
| ネットワーク2 | `ex03-private`、`10.30.11.0/24`、**`internal = true`**（外への経路なし ≒ NAT GW のないプライベートサブネット） |
| コンテナ `ex03-web` | nginx。public `10.30.1.10` と private `10.30.11.10` の**両方**に接続。80 → `127.0.0.1:8083` |
| コンテナ `ex03-db` | nginx（DB の代役）。private `10.30.11.20` **のみ**。ポート公開なし |
| サブネットの値 | 変数 `public_cidr` / `private_cidr` にし、IP は `cidrhost()` で求める（直書き禁止） |

## 新しく使うもの
- 同じ種類のブロックを2回書く（`networks_advanced` を2つ）
- 1つの `docker_image` を2つのコンテナから参照する

## 確認してみること（check.sh も見ます）
```bash
docker exec ex03-web wget -qO- -T 3 http://10.30.11.20 | head -3   # web → db：届く
docker exec ex03-db  wget -qO- -T 3 http://example.com              # db → 外：届かない
```
→ db が外に出られないのはなぜか？ AWS ではどうやって private から外に出させるか？（NAT Gateway / VPC エンドポイント）
