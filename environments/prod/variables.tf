variable "resource_group_name" {
  description = "Name of the resource group."
  type        = string
}

variable "location" {
  description = "Location for all resources."
  default     = "East US"
  type        = string
}

variable "vnet_name" {
  description = "Name of the virtual network."
  type        = string
}

variable "address_space" {
  description = "The address space for the virtual network."
  type        = list(string)
  default     = ["10.0.0.0/16"]  # Example default, adjust as needed
}

variable "subnet_name" {
  description = "Name of the subnet."
  type        = string
}

variable "subnet_prefixes" {
  description = "List of address prefixes for the subnet."
  type        = list(string)
}

variable "admin_username" {
  description = "Admin username for the VM."
  default     = "adminuser"
  type        = string
}

variable "public_key_path" {
  description = "Path to the public SSH key."
  default     = "~/.ssh/id_rsa.pub"
  type        = string
}

variable "vm_name" {
  description = "The name of the virtual machine."
  type        = string
}
