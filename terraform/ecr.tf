resource "aws_ecr_repository" "rag_app" {
  name                 = "${var.project_name}-repo"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  force_delete = true
}

output "ecr_repository_url" {
  value = aws_ecr_repository.rag_app.repository_url
}
