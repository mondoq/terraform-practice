# 演習03:EC2を一台立てる
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

# EC2インスタンスの定義
resource "aws_instance" "my_ec2" {
  ami           = data.aws_ami.amazon_linux_2023.id
  instance_type = "t3.micro"

  tags = {
    Name = "terraform-sample-ec2"
  }
}

