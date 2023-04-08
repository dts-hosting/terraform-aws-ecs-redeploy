locals {
  handler = "redeploy.handler"
  pkg     = "${path.module}/build/terraform-ecs-redeploy.zip"
  project = "terraform-ecs-redeploy"
}

resource "aws_lambda_function" "this" {
  filename         = local.pkg
  function_name    = var.name
  role             = aws_iam_role.this.arn
  handler          = local.handler
  runtime          = "python3.9"
  source_code_hash = filebase64sha256(local.pkg)

  environment {
    variables = {
      CLUSTER   = var.cluster
      DEBUG     = false
      SLACK_KEY = var.slack_key
      TOKEN_KEY = var.token_key
    }
  }

  depends_on = [aws_iam_role.this]
}

resource "aws_lambda_function_url" "this" {
  function_name      = aws_lambda_function.this.function_name
  authorization_type = "NONE"
}

resource "aws_iam_role" "this" {
  name = var.name

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "ecs.amazonaws.com",
          "lambda.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole",
      "Sid": ""
    }
  ]
}
EOF

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/AmazonECS_FullAccess",
    "arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess",
    "arn:aws:iam::aws:policy/CloudWatchFullAccess"
  ]
}
