#AWS doesn't let you attach an IAM role directly to an EC2 instance — 
#you have to wrap it in an instance profile first. This resource is that wrapper. 
#It's given the same name as the role (var.role_name) and points at aws_iam_role.ec2_role — 
#note the reference aws_iam_role.ec2_role.name, which is Terraform's way of saying 
#"use the actual name of that role resource, once it's created," rather than hardcoding the string twice.

resource "aws_iam_instance_profile" "this" {
  name = var.role_name
  role = aws_iam_role.ec2_role.name

  tags = {
    Environment        = var.environment
    Owner              = "security-team"
    Project            = "security-lab"
    DataClassification = "internal"
  }
}


resource "aws_iam_role" "ec2_role" {
  name = var.role_name
  
#only trust policy is in the project as of now, no permission policy is defined. Excluded from the scope
#so, if this role is applied, as the role currently has zero actual permissions
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
  tags = {
    Environment        = var.environment
    Owner              = "security-team"
    Project            = "security-lab"
    DataClassification = "internal"
  }
}
