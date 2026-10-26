#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
. ../lib/common.sh

ip_on() { dget "$1" "{{with index .NetworkSettings.Networks \"$2\"}}{{.IPAddress}}{{end}}"; }

check_basics

step "ネットワーク"
expect "public のサブネット"  "10.30.1.0/24"  "$(dget ex03-public '{{range .IPAM.Config}}{{.Subnet}}{{end}}')"
expect "private のサブネット" "10.30.11.0/24" "$(dget ex03-private '{{range .IPAM.Config}}{{.Subnet}}{{end}}')"
expect "private は internal"  "true"          "$(dget ex03-private '{{.Internal}}')" "docker_network の internal = true"

step "コード"
if grep -qE 'ipv4_address *= *"' ./*.tf; then
  ng "ipv4_address が直書きされている" "cidrhost(var.public_cidr, 10) のように書く"
else
  ok "IP は cidrhost() で求めている"
fi

step "web"
expect "public 側 IP"  "10.30.1.10"  "$(ip_on ex03-web ex03-public)"
expect "private 側 IP" "10.30.11.10" "$(ip_on ex03-web ex03-private)" "networks_advanced ブロックを2つ書く"
expect "HTTP で応答"   "200" "$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 http://127.0.0.1:8083)"

step "db"
expect "private 側 IP"       "10.30.11.20" "$(ip_on ex03-db ex03-private)"
expect "public には繋がない" ""            "$(ip_on ex03-db ex03-public)" "db の networks_advanced は private だけ"
expect "ポート公開なし"      ""            "$(dget ex03-db '{{range $k, $v := .HostConfig.PortBindings}}{{$k}}{{end}}')" "db に ports ブロックは不要"

step "通信"
if docker exec ex03-web wget -qO- -T 3 http://10.30.11.20 >/dev/null 2>&1; then ok "web → db 届く"; else ng "web → db が届かない"; fi
if docker exec ex03-db wget -qO- -T 3 http://example.com >/dev/null 2>&1; then
  ng "db から外に出られてしまう" "private の internal = true"
else
  ok "db → インターネット 届かない"
fi

summary
