#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
. ../lib/common.sh

check_basics

step "コード"
n=$(grep -cE '^resource +"docker_container"' ./*.tf | awk -F: '{s += $NF} END {print s}')
expect "docker_container ブロックは1つ" "1" "$n" "for_each で1ブロックにまとめる"
if grep -q 'for_each' ./*.tf; then ok "for_each を使っている"; else ng "for_each が見当たらない"; fi

step "コンテナ"
for i in 1 2 3; do
  c="ex04-web$i"
  expect "$c の IP"       "10.40.0.1$i"         "$(dget "$c" '{{with index .NetworkSettings.Networks "ex04-net"}}{{.IPAddress}}{{end}}')" "name = \"ex04-\${each.key}\""
  expect "$c のポート"    "127.0.0.1:809$i"     "$(dget "$c" '{{range (index .HostConfig.PortBindings "80/tcp")}}{{.HostIp}}:{{.HostPort}}{{end}}')"
  expect "$c HTTP で応答" "200"                 "$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "http://127.0.0.1:809$i")"
done

step "output"
expect "urls" '{"web1":"http://127.0.0.1:8091","web2":"http://127.0.0.1:8092","web3":"http://127.0.0.1:8093"}' \
  "$(terraform output -json urls 2>/dev/null | tr -d ' \n')" "{ for k, c in docker_container.web : k => \"http://...\" }"

summary
