output "redeploy_hostname" {
  value = regex("https://(.*)/", aws_lambda_function_url.this.function_url)[0]
}

output "redeploy_url" {
  value = aws_lambda_function_url.this.function_url
}
