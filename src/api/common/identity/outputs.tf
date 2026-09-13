output "role_arn" {
  description = "ARN of the role every workflow assumes, which vars.OIDC_ROLE_ARN must equal."
  value       = aws_iam_role.deploy.arn
}

output "role_name" {
  description = "Name of the role every workflow assumes."
  value       = aws_iam_role.deploy.name
}

output "seed_role_arn" {
  description = "ARN of the role seed.yml assumes, which vars.SEED_ROLE_ARN must equal."
  value       = aws_iam_role.seed.arn
}

output "seed_role_name" {
  description = "Name of the role seed.yml assumes."
  value       = aws_iam_role.seed.name
}

output "subject" {
  description = "The one GitHub OIDC subject the trust admits: this repository by its immutable ids, on main."
  value       = local.subject
}
