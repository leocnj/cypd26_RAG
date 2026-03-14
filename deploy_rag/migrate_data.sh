#!/bin/bash

# Configuration
LOCAL_CHROMA_DIR="../chroma_db"
# Using a unique name with today's date
S3_BUCKET="cyp2d6-rag-data-$(date +%Y%m%d)"
S3_PREFIX="migration/cyp2d6_knowledge_base"

echo "[*] Step 1: Checking/Creating S3 bucket s3://$S3_BUCKET..."
aws s3 mb "s3://$S3_BUCKET" 2>/dev/null || true

echo "[*] Step 2: Syncing ChromaDB to S3..."
echo "[*] Source: $LOCAL_CHROMA_DIR"
echo "[*] Destination: s3://$S3_BUCKET/$S3_PREFIX"

aws s3 sync "$LOCAL_CHROMA_DIR" "s3://$S3_BUCKET/$S3_PREFIX" --delete

echo "[*] Success!"
echo "[*] Next, set these environment variables in AWS App Runner:"
echo "    MIGRATION_S3_BUCKET=$S3_BUCKET"
echo "    MIGRATION_S3_PREFIX=$S3_PREFIX"
