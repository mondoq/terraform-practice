variable "subnet_cidr" {
  description = "ラボ用ネットワークのCIDR（VPCのCIDRに相当）"
  type        = string
  default     = "172.30.0.0/24"
}

variable "host_port" {
  description = "ホスト側で公開するポート"
  type        = number
  default     = 8080
}

variable "bind_ip" {
  description = "待ち受けるホスト側IP。127.0.0.1=自分だけ / 0.0.0.0=LAN全体に公開"
  type        = string
  default     = "127.0.0.1"
}
