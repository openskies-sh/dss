terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">=4.0"
    }
    tls = {
      source = "hashicorp/tls"
    }
    helm = {
      source = "hashicorp/helm"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Cluster = var.cluster_name
    }
  }
}

data "aws_eks_cluster_auth" "kubernetes_cluster" {
  name = aws_eks_cluster.kubernetes_cluster.name
}

provider "helm" {
  kubernetes {
    host                   = aws_eks_cluster.kubernetes_cluster.endpoint
    cluster_ca_certificate = base64decode(aws_eks_cluster.kubernetes_cluster.certificate_authority[0].data)
    token                  = data.aws_eks_cluster_auth.kubernetes_cluster.token
  }
}
