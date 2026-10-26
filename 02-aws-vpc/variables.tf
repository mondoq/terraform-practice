variable "region" {
  type    = string
  default = "ap-northeast-1"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "my_ip_cidr" {
  description = "SSHを許可する自宅のグローバルIP（例: 203.0.113.5/32）。curl -s https://checkip.amazonaws.com で確認"
  type        = string
}
