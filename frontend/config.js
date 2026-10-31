// ============================================================
// BACKEND URL - set this one line to choose which backend to use
// ============================================================

// Option 1: Flask on EC2 (port 80)
// const BACKEND_URL = "http://<ec2-public-ip>";

// Option 2: Flask in Docker on ECS Fargate (port 80)
// const BACKEND_URL = "http://<ecs-task-public-ip>";

// Option 3: API Gateway + Lambda
// const BACKEND_URL = "https://<api-id>.execute-api.us-east-1.amazonaws.com/prod";

// ACTIVE (replace with your own deployment's URL):
const BACKEND_URL = "https://<api-id>.execute-api.us-east-1.amazonaws.com/prod";
