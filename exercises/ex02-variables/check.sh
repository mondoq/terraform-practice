#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
. ../lib/common.sh

check_basics

step "変数"
if terraform plan -input=false -no-color -var bind_ip=192.168.0.1 >/dev/null 2>&1; then
  ng "bind_ip=192.168.0.1 が通ってしまう" "variable \"bind_ip\" に validation ブロックを書く"
else
  ok "bind_ip=192.168.0.1 はエラーになる"
fi
if terraform plan -input=false -no-color -var bind_ip=0.0.0.0 >/dev/null 2>&1; then
  ok "bind_ip=0.0.0.0 は通る"
else
  ng "bind_ip=0.0.0.0 がエラーになる" "condition が厳しすぎないか"
fi

step "コンテナ ex02-web"
expect "起動している"     "true"       "$(dget ex02-web '{{.State.Running}}')" "docker_container の name"
expect "ex02-net 上の IP" "10.20.0.10" "$(dget ex02-web '{{with index .NetworkSettings.Networks "ex02-net"}}{{.IPAddress}}{{end}}')" \
  "networks_advanced { name = ...  ipv4_address = ... }"
expect "ポート公開" "127.0.0.1:8081" "$(dget ex02-web '{{range (index .HostConfig.PortBindings "80/tcp")}}{{.HostIp}}:{{.HostPort}}{{end}}')" \
  "ports { internal = 80  external = var.host_port  ip = var.bind_ip }"
expect "HTTP で応答" "200" "$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 http://127.0.0.1:8081)"

step "output"
expect "url" "http://127.0.0.1:8081" "$(terraform output -raw url 2>/dev/null)" "文字列補間 \"\${var.xxx}\""

summary
