# -------------------------------------------------------------
# Data bucket
# -------------------------------------------------------------
resource "aws_s3_bucket" "ge_data_bucket" {
  bucket        = var.ge-data-bucket-name
  force_destroy = true

  tags = {
    Name = "grater_expectations_tutorial"
  }
}

resource "aws_s3_bucket_acl" "ge_data_bucket" {
  bucket = aws_s3_bucket.ge_data_bucket.id
  acl    = "private"
}

resource "aws_s3_bucket_public_access_block" "ge_data_bucket" {
  bucket = aws_s3_bucket.ge_data_bucket.id

  block_public_acls   = true
  block_public_policy = true
}
