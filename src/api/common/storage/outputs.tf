output "bucket_name" {
  description = "Name of the product's S3 store (the carrier, provider and tenant inputs, and the WANs synthesized from them)."
  value       = aws_s3_bucket.store.id
}

output "bucket_arn" {
  description = "ARN of the product's S3 store."
  value       = aws_s3_bucket.store.arn
}
