output "aws_account_id" {
  description = "The AWS account every stack deploys into."
  value       = "781581267945"
}

output "aws_region" {
  description = "The region every stack deploys into."
  value       = "us-east-2"
}

output "state_bucket" {
  description = "The shared OpenTofu state bucket."
  value       = "10ulabs-terraform-state-us-east-2"
}


output "lambda_handler_names" {
  description = "Deterministic Lambda function names, one per REST resource, and the authorizer in front of them all."
  value = {
    prune      = "wan-synthesizer-prune"
    authorizer = "wan-synthesizer-authorizer"
  }
}

output "store_principals" {
  description = "Every role that reads or writes the store, the handlers' and the deploy role; the store's bucket policy denies every other principal."
  value = [
    "TenULabsWanSynthesizerRole",
    "wan-synthesizer-prune-lambda",
  ]
}
