resource "aws_apprunner_service" "main" {
  service_name = var.project_name

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.app_runner_access_role.arn
    }

    image_repository {
      image_identifier      = "${aws_ecr_repository.rag_app.repository_url}:latest"
      image_repository_type = "ECR"
      image_configuration {
        port = "8000"
        runtime_environment_variables = {
          CHROMA_PATH         = "/app/chroma_db"
          MIGRATION_S3_BUCKET = var.migration_s3_bucket
          MIGRATION_S3_PREFIX = var.migration_s3_prefix
          LLM_PROVIDER        = var.llm_provider
          GEMINI_API_KEY      = var.gemini_api_key
          OPENAI_API_KEY      = var.openai_api_key
          GEMINI_MODEL        = "gemini-flash-latest"
          GEMINI_API_VERSION  = "v1beta"
        }
      }
    }
    auto_deployments_enabled = true
  }

  network_configuration {
    egress_configuration {
      egress_type       = "VPC"
      vpc_connector_arn = aws_apprunner_vpc_connector.main.arn
    }
  }

  instance_configuration {
    instance_role_arn = aws_iam_role.app_runner_instance_role.arn
    cpu               = "1 vCPU"
    memory            = "2 GB"
  }

  health_check_configuration {
    protocol            = "TCP"
    interval            = 20
    timeout             = 10
    healthy_threshold   = 1
    unhealthy_threshold = 15 # Allow up to 300 seconds (20*15) for startup sync
  }
}

# The above resource might need 'storage_configuration' block depending on provider version
# For simplicity in this plan, we focus on the core logic.
