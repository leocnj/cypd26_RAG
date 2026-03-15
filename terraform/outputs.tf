output "app_runner_service_url" {
  value = aws_apprunner_service.main.service_url
}

output "ecr_repository_url_full" {
  value = aws_ecr_repository.rag_app.repository_url
}

output "vpc_id" {
  value = aws_vpc.main.id
}
