#!/bin/bash

# Configuration
REGION="us-east-1"
REPO_NAME="cyp2d6-rag-repo"

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

echo "[*] Step 1: Getting ECR Repository URL from Terraform..."
# Run terraform output from the terraform directory relative to the project root
REPO_URL=$(cd "$PROJECT_ROOT/terraform" && terraform output -raw ecr_repository_url_full)

if [ -z "$REPO_URL" ]; then
    echo "[!] Error: Could not find ECR URL."
    echo "[!] Please ensure you have fixed your IAM permissions and successfully run:"
    echo "    cd terraform && terraform apply -target=aws_ecr_repository.rag_app"
    exit 1
fi

echo "[*] Step 2: Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin "$REPO_URL"

echo "[*] Step 3: Building Docker image (forcing linux/amd64 for AWS compatibility)..."
# Build using the deploy_rag directory as context and force x86_64 platform
docker build --platform linux/amd64 -t $REPO_NAME "$PROJECT_ROOT/deploy_rag"

echo "[*] Step 4: Tagging and Pushing image..."
docker tag "$REPO_NAME:latest" "$REPO_URL:latest"
docker push "$REPO_URL:latest"

echo "[*] Success! Image is now in ECR."
