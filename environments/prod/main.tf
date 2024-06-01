module "network" {
  source              = "../../modules/network"
  resource_group_name = var.resource_group_name
  location            = var.location
  vnet_name           = var.vnet_name
  subnet_name         = var.subnet_name
  subnet_prefixes     = var.subnet_prefixes
  address_space       = var.address_space
}

module "vm" {
  source              = "../../modules/vm"
  nic_name            = "prodNIC"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = module.network.subnet_id  # Ensure this references the correct output
  vm_name             = var.vm_name
  vm_size             = "Standard_DS1_v2"
  admin_username      = var.admin_username
  image_publisher     = "Canonical"
  image_offer         = "UbuntuServer"
  image_sku           = "18.04-LTS"
  image_version       = "latest"
  public_key_path     = var.public_key_path
}
