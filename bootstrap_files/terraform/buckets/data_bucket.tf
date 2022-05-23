# -------------------------------------------------------------
# Data bucket
# -------------------------------------------------------------
# NOTE: this configuration is commented out, as it is assumed that data will be 
# available at an existing source and this repository should not be handling data 
# storage. If this is not the case, the code below can be used to generate an S3 bucket
# to load data

# resource "aws_s3_bucket" "ge_data_bucket" {
#   bucket        = var.ge-data-bucket-name
#   force_destroy = true

#   tags = {
#     Name = "data bucket"
#   }
# }

# resource "aws_s3_bucket_acl" "ge_data_bucket" {
#   bucket = aws_s3_bucket.ge_data_bucket.id
#   acl    = "private"
# }

# resource "aws_s3_bucket_public_access_block" "ge_data_bucket" {
#   bucket = aws_s3_bucket.ge_data_bucket.id

#   block_public_acls   = true
#   block_public_policy = true
# }
