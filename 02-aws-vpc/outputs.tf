output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_cidr" {
  value = aws_subnet.public.cidr_block
}

output "private_subnet_cidr" {
  value = aws_subnet.private.cidr_block
}

output "security_group_id" {
  value = aws_security_group.web.id
}
