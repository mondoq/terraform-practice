# 演習02: AWS に「自宅ネットワークのクラウド版」を作る
# 無料のリソースだけで構成（NAT Gateway / EC2 は作らない）。
#
#   自宅                        AWS
#   J:COM 回線                → Internet Gateway
#   家庭用ルーターの経路表    → Route Table
#   LAN 192.168.0.0/24        → VPC 10.0.0.0/16 内のサブネット
#   Windows ファイアウォール  → Security Group

terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project   = "terraform-practice"
      ManagedBy = "terraform"
    }
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "practice-vpc" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = { Name = "practice-igw" }
}

# 10.0.0.0/16 を /24 に切り出す: public = 10.0.1.0/24, private = 10.0.11.0/24
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, 1)
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = { Name = "practice-public-a" }
}

resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, 11)
  availability_zone = data.aws_availability_zones.available.names[0]

  tags = { Name = "practice-private-a" }
}

# public だけデフォルトルートを IGW に向ける。これが「パブリックサブネット」の正体。
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = { Name = "practice-public-rt" }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# private は明示的な関連付けをしない → VPC のメインルートテーブル（local のみ）が使われる

resource "aws_security_group" "web" {
  name        = "practice-web-sg"
  description = "HTTP from anywhere, SSH from my home IP only"
  vpc_id      = aws_vpc.main.id

  tags = { Name = "practice-web-sg" }
}

resource "aws_vpc_security_group_ingress_rule" "http" {
  security_group_id = aws_security_group.web.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}

resource "aws_vpc_security_group_ingress_rule" "ssh" {
  security_group_id = aws_security_group.web.id
  cidr_ipv4         = var.my_ip_cidr
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
}

resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.web.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}
