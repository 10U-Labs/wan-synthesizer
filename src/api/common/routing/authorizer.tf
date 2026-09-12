locals {
  authorizer_role_name = "wan-synthesizer-authorizer-lambda"
}

resource "random_password" "api_key" {
  length  = 48
  special = false
}

resource "aws_ssm_parameter" "api_key" {
  name  = "/wan-synthesizer/api-key"
  type  = "SecureString"
  value = random_password.api_key.result
}

data "archive_file" "authorizer" {
  type        = "zip"
  source_file = "${path.module}/lambdas/authorizer.py"
  output_path = "${path.module}/.terraform/lambda_packages/authorizer.zip"
}

resource "aws_lambda_function" "authorizer" {
  filename         = data.archive_file.authorizer.output_path
  function_name    = module.common.lambda_handler_names.authorizer
  role             = aws_iam_role.authorizer.arn
  handler          = "authorizer.lambda_handler"
  source_code_hash = data.archive_file.authorizer.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 10
  memory_size      = 128
  description      = "Authorizer: admit a Google account on the hosted domain, or the API key the seed holds."

  environment {
    variables = {
      GOOGLE_CLIENT_ID  = "846587722064-qjou8en4tk96n12ii3rgnpjshnbqovok.apps.googleusercontent.com"
      HOSTED_DOMAIN     = "10ulabs.com"
      API_KEY_PARAMETER = aws_ssm_parameter.api_key.name
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.authorizer.name
  }

  lifecycle {
    replace_triggered_by = [aws_iam_role.authorizer.id]
  }
}

resource "aws_cloudwatch_log_group" "authorizer" {
  name              = "/aws/lambda/${module.common.lambda_handler_names.authorizer}"
  retention_in_days = 7
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.authorizer.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${local.aws_region}:${local.aws_account_id}:${aws_api_gateway_rest_api.api.id}/authorizers/*"
}
