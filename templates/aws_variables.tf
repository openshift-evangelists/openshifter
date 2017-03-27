//  AWS region to deploy our cluster
variable "region" {
  description = "Region to deploy the cluster into"
  default = "{{.Aws.Region}}"
}

// Machine type
variable "machine" {
  description = "Machine type to use for the cluster"
  default = "{{.Nodes.Type}}"
}

// Number of worker nodes
variable "workernodes" {
  description = "Number of worker nodes to deploy"
  default = "{{.Nodes.Count}}"
}

// SSH key name
variable "key_name" {
  description = "The name of the key to user for ssh access, e.g: os-cluster"
  default = "os-cluster"
}

// Public key to use for SSH access.
variable "public_key_path" {
  description = "The local path to the public SSH key path, e.g. ~/.ssh/id_rsa.pub"
  default = "~/.ssh/aws.pub"
}

variable "vpc_cidr" {
  description = "The CIDR block for the VPC, e.g: 10.0.0.0/16"
  default = "10.0.0.0/16"
}

variable "subnetaz" {
  description = "The AZ for the public subnet, e.g: us-east-1a"
  default = {
    us-east-1 = "us-east-1a"
    us-east-2 = "us-east-2a"
    us-west-1 = "us-west-1a"
    us-west-2 = "us-west-2a"
    eu-west-1 = "eu-west-1a"
    eu-west-2 = "eu-west-2a"
    eu-central-1 = "eu-central-1a"
    ap-southeast-1 = "ap-southeast-1a"
  }
}

variable "subnet_cidr" {
  description = "The CIDR block for the public subnet, e.g: 10.0.1.0/24"
  default = "10.0.1.0/24"
}
