# -------------------------------------------------------------
# Lambda function
# -------------------------------------------------------------

resource "random_uuid" "force_refresh" {
}

resource "aws_lambda_function" "validation_lambda" {
  function_name    = "grater_expectations_validation_tutorial"
  role             = aws_iam_role.validation_lambda_role.arn
  image_uri        = var.image_uri
  package_type     = "Image"
  memory_size      = 1024
  timeout          = 60
  source_code_hash = base64sha256(random_uuid.force_refresh.result)

  tags = {
    Name = "Grater Expectations validation lambda tutorial"
  }
}

# -------------------------------------------------------------
# Lambda policies
# -------------------------------------------------------------

# Create role for creating lambda function
resource "aws_iam_role" "validation_lambda_role" {
  name = "grater_expectations_validation_lambda_tutorial"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}


# Create policy to access s3 bucket
resource "aws_iam_policy" "validation_lambda_policy" {
  name        = "grater_expectations_validation_lambda_s3_access_tutorial"
  description = "Policy for accessing s3 buckets containing data and configurations"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "s3:*"
      ],
      "Effect": "Allow",
      "Resource": [
        "arn:aws:s3:::${var.ge-bucket-name}",
        "arn:aws:s3:::${var.ge-site-bucket-name}",
        "arn:aws:s3:::${var.ge-data-bucket-name}",
        "arn:aws:s3:::${var.ge-bucket-name}/*",
        "arn:aws:s3:::${var.ge-site-bucket-name}/*",
        "arn:aws:s3:::${var.ge-data-bucket-name}/*"
        ]
    }
  ]
}
EOF
}

# Add policy to lambda role
resource "aws_iam_role_policy_attachment" "validation_lambda_policy" {
  role       = aws_iam_role.validation_lambda_role.name
  policy_arn = aws_iam_policy.validation_lambda_policy.arn
}
