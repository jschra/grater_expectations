# -------------------------------------------------------------
# Great expectations output S3 bucket
# -------------------------------------------------------------
resource "aws_s3_bucket" "ge_bucket" {
  bucket        = var.ge-bucket-name
  force_destroy = true

  tags = {
    Name = "${var.ge-bucket-name}"
  }
}

resource "aws_s3_bucket_acl" "ge_bucket" {
  bucket = aws_s3_bucket.ge_bucket.id
  acl    = "private"
}

resource "aws_s3_bucket_public_access_block" "ge_bucket" {
  bucket = aws_s3_bucket.ge_bucket.id

  block_public_acls   = true
  block_public_policy = true
}

# -------------------------------------------------------------
# Great expectations website S3 bucket
# -------------------------------------------------------------
resource "aws_s3_bucket" "ge_site_bucket" {
  bucket        = var.ge-site-bucket-name
  force_destroy = true

  tags = {
    Name = "${var.ge-site-bucket-name}"
  }
}

resource "aws_s3_bucket_acl" "ge_site_bucket" {
  bucket = aws_s3_bucket.ge_site_bucket.id
  acl    = "public-read"
}

resource "aws_s3_bucket_public_access_block" "ge_site_bucket" {
  bucket = aws_s3_bucket.ge_site_bucket.id

  block_public_acls   = false
  block_public_policy = false
}

resource "aws_s3_bucket_policy" "allow_public_access" {
  bucket = aws_s3_bucket.ge_site_bucket.id
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "${aws_s3_bucket.ge_site_bucket.arn}/*"
        }
    ]
}
EOF
}

resource "aws_s3_bucket_website_configuration" "ge_site_bucket" {
  bucket = aws_s3_bucket.ge_site_bucket.bucket

  index_document {
    suffix = "index.html"
  }
}
