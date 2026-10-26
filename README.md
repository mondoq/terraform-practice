# Terraform 構築練習

[![Terraform CI](https://github.com/mondoq/terraform-practice/actions/workflows/terraform-ci.yml/badge.svg)](https://github.com/mondoq/terraform-practice/actions/workflows/terraform-ci.yml)
[![Portfolio](https://github.com/mondoq/terraform-practice/actions/workflows/portfolio.yml/badge.svg)](https://mondoq.github.io/terraform-practice/)

📊 **ポートフォリオ（自動採点の結果）: https://mondoq.github.io/terraform-practice/**
VS Code で保存 → GitDoc が自動コミット・push → GitHub Actions が演習を採点 → GitHub Pages を更新

| # | ディレクトリ | 必要なもの | 料金 |
|---|---|---|---|
| 01 | `01-docker-basics/` | Docker のみ | 無料 |
| 02 | `02-aws-vpc/` | AWS 認証情報 | 無料（VPC/サブネット/IGW/RT/SG のみ） |

基本サイクル: `init` → `plan` → `apply` → （確認）→ `destroy`

---

## 01: Docker で基本サイクル

```bash
cd ~/terraform-practice/01-docker-basics
terraform init        # プロバイダ（プラグイン）を .terraform/ にダウンロード
terraform plan        # 「何が作られるか」の差分を表示。+ は作成
terraform apply       # yes で実行
curl -I http://127.0.0.1:8080
terraform output
terraform state list  # Terraform が「自分が管理している」と記録しているもの
```

### 課題
1. **差分の読み方** — `terraform plan -var bind_ip=0.0.0.0` を実行。
   `~`（変更）ではなく `-/+`（作り直し）になる。どの属性が `forces replacement` か確認する。
   → AWS でも EC2 の一部属性は変更不可で作り直しになる。本番で plan を必ず読む理由。
2. **ドリフト** — Terraform の外で `docker rm -f tf-web` してから `terraform plan`。
   Terraform は state と現実の差分をどう扱うか？ → `apply` で元に戻る。
3. **依存関係** — `terraform graph` の出力を眺める。network → container の順序は
   誰も書いていないのに、参照（`docker_network.lab.name`）から自動で決まっている。
4. **2台目を作る** — `docker_container` を `count = 2` にして、IP を
   `cidrhost(var.subnet_cidr, 10 + count.index)` に。outputs も直す必要が出る。
5. 最後に `terraform destroy`。

---

## 02: AWS VPC（自宅ネットワークのクラウド版）

```
            Internet
               │
        [Internet Gateway]          ← J:COM 回線の出入口
               │
   ┌───────── VPC 10.0.0.0/16 ──────────────┐
   │  public  10.0.1.0/24   → 0.0.0.0/0 IGW │
   │  private 10.0.11.0/24  → local のみ     │
   └────────────────────────────────────────┘
```

### 事前準備（1回だけ）
1. AWS コンソールで IAM ユーザー（またはIAM Identity Center）を作り、認証情報を発行
2. `aws configure`（または `aws login`）→ `aws sts get-caller-identity` で確認
3. 念のため **AWS Budgets で月 1 USD のアラート** を設定

```bash
cd ~/terraform-practice/02-aws-vpc
terraform init
terraform plan  -var "my_ip_cidr=$(curl -s https://checkip.amazonaws.com)/32"
terraform apply -var "my_ip_cidr=$(curl -s https://checkip.amazonaws.com)/32"
```

### 課題
1. コンソールの VPC → ルートテーブルで、public と private の違いを目で確認
2. AZ を2つにする（`names[1]` 用のサブネットを追加）→ 後で `count`/`for_each` で書き直す
3. **NAT Gateway を足す設計だけ書いて `plan` まで**（apply すると時間課金・約 $0.06/h）
4. `terraform destroy` で片付け

---

## exercises/: 白紙からコードを書く練習（Docker・無料）

各ディレクトリの `TASK.md` を読んで `.tf` を自分で書き、`./check.sh` で採点。

| # | テーマ | 新しく覚える文法 |
|---|---|---|
| ex01-network | ネットワーク1つ（≒VPC） | terraform / provider / resource / output、属性の参照 |
| ex02-variables | nginx＋ポート公開 | variable、validation、文字列補間、ファイル分割 |
| ex03-public-private | Web=public / DB=private の2層 | 複数リソースの参照、`cidrhost()`、internal ネットワーク |
| ex04-for-each | マップから台数を増減 | `for_each`、`each.*`、for 式 |
