# NOTE: It's best to run Terraform using state stored in a state bucket. For more
# information, please refer to https://www.terraform.io/language/state/remote
{% raw %}
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0.0"
    }
  }
}

provider "aws" {
  {% endraw %}region = "{{cfg_global["region"] }}"{% raw %}
}
{% endraw %}