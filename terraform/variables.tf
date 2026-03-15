variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "cyp2d6-rag"
}

variable "migration_s3_bucket" {
  description = "S3 bucket containing the ChromaDB data for migration"
  type        = string
  default     = "cyp2d6-rag-data-20260314"
}

variable "migration_s3_prefix" {
  description = "S3 prefix for ChromaDB data"
  type        = string
  default     = "migration/cyp2d6_knowledge_base"
}

variable "llm_provider" {
  description = "LLM provider (gemini or openai)"
  type        = string
  default     = "gemini"
}

variable "gemini_api_key" {
  description = "Gemini API Key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openai_api_key" {
  description = "OpenAI API Key"
  type        = string
  sensitive   = true
  default     = ""
}
