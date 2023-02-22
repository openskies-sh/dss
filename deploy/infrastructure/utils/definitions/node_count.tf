variable "node_count" {
  type        = number
  description = <<-EOT
    Number of Kubernetes nodes which should correspond to the desired CockroachDB nodes.
    **Always 3.**

    Example: `3`
  EOT

  validation {
    condition     = var.node_count == 3
    error_message = "Node count should be 3. Only configuration supported at the moment"
  }
}