# 演習01: Docker で Terraform の基本サイクルを体験する
# AWS と同じ「ネットワークを作る → その中にサーバーを置く → ポートを公開する」構成。
#   docker_network   ≒ VPC / サブネット
#   docker_container ≒ EC2
#   ports.ip         ≒ セキュリティグループ（どこから受け付けるか）

terraform {
  required_version = ">= 1.6"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_network" "lab" {
  name = "tf-lab"

  ipam_config {
    subnet  = var.subnet_cidr
    gateway = cidrhost(var.subnet_cidr, 1)
  }
}

resource "docker_image" "nginx" {
  name         = "nginx:1.27-alpine"
  keep_locally = true
}

resource "docker_container" "web" {
  name  = "tf-web"
  image = docker_image.nginx.image_id

  networks_advanced {
    name         = docker_network.lab.name
    ipv4_address = cidrhost(var.subnet_cidr, 10)
  }

  ports {
    internal = 80
    external = var.host_port
    ip       = var.bind_ip
  }
}
