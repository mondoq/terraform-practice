output "web_private_ip" {
  description = "ラボネットワーク内でのコンテナのIP（EC2のプライベートIPに相当）"
  value       = docker_container.web.network_data[0].ip_address
}

output "url" {
  value = "http://${var.bind_ip}:${var.host_port}"
}
