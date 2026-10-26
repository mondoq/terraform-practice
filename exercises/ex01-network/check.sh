#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
. ../lib/common.sh

check_basics

step "ネットワーク ex01-net"
expect "存在する"     "ex01-net"     "$(dget ex01-net '{{.Name}}')" "name の値を確認"
expect "サブネット"   "10.10.0.0/24" "$(dget ex01-net '{{range .IPAM.Config}}{{.Subnet}}{{end}}')" "ipam_config の subnet"
expect "ゲートウェイ" "10.10.0.1"    "$(dget ex01-net '{{range .IPAM.Config}}{{.Gateway}}{{end}}')" "ipam_config の gateway"

step "output"
expect "network_id が実際の ID と一致" "$(dget ex01-net '{{.Id}}')" "$(terraform output -raw network_id 2>/dev/null)" \
  "output \"network_id\" { value = docker_network.<名前>.id }"

summary
