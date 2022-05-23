# -------------------------------------------------------------
# Great expectations output bucket
# -------------------------------------------------------------
resource "aws_s3_bucket" "tutorial_data_bucket" {
  bucket        = var.tutorial-bucket-name
  force_destroy = true

  tags = {
    Name = "grater_expectations_tutorial"
  }
}

resource "aws_s3_bucket_acl" "tutorial_data_bucket" {
  bucket = aws_s3_bucket.tutorial_data_bucket.id
  acl    = "private"
}

resource "aws_s3_bucket_public_access_block" "tutorial_data_bucket" {
  bucket = aws_s3_bucket.tutorial_data_bucket.id

  block_public_acls   = true
  block_public_policy = true
}
