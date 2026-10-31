#!/bin/bash
# ECS Deployment Script for Music Backend
# Run from the backend-ecs/ directory
# Prerequisites: AWS CLI configured, Docker installed

set -e

REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REPO_NAME="music-backend"
CLUSTER_NAME="music-backend-cluster"
SERVICE_NAME="music-backend-service"
IMAGE_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest"

echo "==> Account ID: $ACCOUNT_ID"
echo "==> Image URI:  $IMAGE_URI"


# ECR Repo Creation (skips if already exists)

echo ""
echo "Creating ECR repository"
aws ecr describe-repositories --repository-names "$REPO_NAME" --region "$REGION" 2>/dev/null || \
  aws ecr create-repository \
    --repository-name "$REPO_NAME" \
    --region "$REGION" \
    --image-scanning-configuration scanOnPush=true


# Authenticate Docker to ECR

echo ""
echo "Logging in to ECR"
aws ecr get-login-password --region "$REGION" | \
  docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"


# Build, tag and push docker image

echo ""
echo "Building Docker image"
docker build -t "$REPO_NAME" .

echo "Tagging image"
docker tag "$REPO_NAME:latest" "$IMAGE_URI"

echo "Pushing image to ECR"
docker push "$IMAGE_URI"


# Create CloudWatch log group

echo ""
echo "Creating CloudWatch log group"
aws logs create-log-group --log-group-name "/ecs/music-backend" --region "$REGION" 2>/dev/null || true

# Use labrole for each task 

echo ""
echo "LabRole for ECS task"
LAB_ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/LabRole"
echo "    Role ARN: $LAB_ROLE_ARN"

# Register ECS task definition

echo ""
echo "Registering task definition"
sed "s/ACCOUNT_ID/$ACCOUNT_ID/g" task-definition.json > ./task-def-resolved.json

aws ecs register-task-definition \
  --cli-input-json file://./task-def-resolved.json \
  --region "$REGION"


# Create ECS cluster using AWS Fargate

echo ""
echo "Creating ECS cluster"
aws ecs create-cluster \
  --cluster-name "$CLUSTER_NAME" \
  --capacity-providers FARGATE \
  --region "$REGION" 2>/dev/null || \
  echo "Cluster already exists, skipping."


# Get default VPC and a public subnet

echo ""
echo "Getting VPC/subnet info"
VPC_ID=$(aws ec2 describe-vpcs \
  --filters "Name=isDefault,Values=true" \
  --query "Vpcs[0].VpcId" \
  --output text \
  --region "$REGION")

SUBNET_ID=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" "Name=defaultForAz,Values=true" \
  --query "Subnets[0].SubnetId" \
  --output text \
  --region "$REGION")

echo "    VPC:    $VPC_ID"
echo "    Subnet: $SUBNET_ID"


# Create security group
echo ""
echo "Creating security group"
SG_ID=$(aws ec2 create-security-group \
  --group-name "music-backend-sg" \
  --description "Allow port 80 for music backend ECS" \
  --vpc-id "$VPC_ID" \
  --region "$REGION" \
  --query "GroupId" \
  --output text 2>/dev/null) || \
  SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=music-backend-sg" "Name=vpc-id,Values=$VPC_ID" \
    --query "SecurityGroups[0].GroupId" \
    --output text \
    --region "$REGION")

aws ec2 authorize-security-group-ingress \
  --group-id "$SG_ID" \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0 \
  --region "$REGION" 2>/dev/null || true

echo "    Security Group: $SG_ID"


# Create or update ECS service
echo ""
echo "Creating or updating ECS service"
if aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --region "$REGION" | grep -q '"status": "ACTIVE"'; then
  aws ecs update-service \
    --cluster "$CLUSTER_NAME" \
    --service "$SERVICE_NAME" \
    --task-definition "music-backend-task" \
    --force-new-deployment \
    --region "$REGION"
  echo "Service updated"
else
  aws ecs create-service \
    --cluster "$CLUSTER_NAME" \
    --service-name "$SERVICE_NAME" \
    --task-definition "music-backend-task" \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
    --region "$REGION"
  echo "Service created"
fi


# Wait for task to be running and print public IP

echo ""
echo "Waiting for task to start"
sleep 30

TASK_ARN=$(aws ecs list-tasks \
  --cluster "$CLUSTER_NAME" \
  --service-name "$SERVICE_NAME" \
  --query "taskArns[0]" \
  --output text \
  --region "$REGION")

ENI_ID=$(aws ecs describe-tasks \
  --cluster "$CLUSTER_NAME" \
  --tasks "$TASK_ARN" \
  --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" \
  --output text \
  --region "$REGION")

PUBLIC_IP=$(aws ec2 describe-network-interfaces \
  --network-interface-ids "$ENI_ID" \
  --query "NetworkInterfaces[0].Association.PublicIp" \
  --output text \
  --region "$REGION")

echo ""
echo "=============================================="
echo "  ECS deployment complete"
echo "  Backend URL: http://$PUBLIC_IP"
echo "=============================================="
