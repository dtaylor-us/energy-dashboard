from constructs import Construct
from cdktf import App, TerraformStack
from imports.azurerm import AzurermProvider, ResourceGroup, VirtualNetwork, Subnet, NetworkInterface, NetworkInterfaceIpConfiguration, VirtualMachine, ContainerRegistry, PostgreSqlServer, PostgreSqlDatabase, PostgreSqlFirewallRule
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class MyStack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        resource_group_name = os.getenv('RESOURCE_GROUP_NAME')
        location = os.getenv('LOCATION')
        vnet_name = os.getenv('VNET_NAME')
        subnet_name = os.getenv('SUBNET_NAME')
        nic_name = os.getenv('NIC_NAME')
        vm_name = os.getenv('VM_NAME')
        vm_size = os.getenv('VM_SIZE')
        admin_username = os.getenv('ADMIN_USERNAME')
        admin_password = os.getenv('ADMIN_PASSWORD')
        acr_name = os.getenv('ACR_NAME')
        pg_server_name = os.getenv('POSTGRES_SERVER_NAME')
        pg_db_name = os.getenv('POSTGRES_DB_NAME')
        pg_admin_username = os.getenv('POSTGRES_ADMIN_USERNAME')
        pg_admin_password = os.getenv('POSTGRES_ADMIN_PASSWORD')

        # Initialize the Azure provider
        AzurermProvider(self, 'AzureRM', features={})

        # Create a resource group
        resource_group = ResourceGroup(self, 'resource_group', name=resource_group_name, location=location)

        # Create a virtual network
        vnet = VirtualNetwork(self, 'vnet',
            name=vnet_name,
            location=resource_group.location,
            resource_group_name=resource_group.name,
            address_space=['10.0.0.0/16']
        )

        # Create a subnet
        subnet = Subnet(self, 'subnet',
            name=subnet_name,
            resource_group_name=resource_group.name,
            virtual_network_name=vnet.name,
            address_prefixes=['10.0.1.0/24']
        )

        # Create a network interface
        ip_config = NetworkInterfaceIpConfiguration(name='internal', subnet_id=subnet.id, private_ip_address_allocation='Dynamic')
        nic = NetworkInterface(self, 'nic',
            name=nic_name,
            location=resource_group.location,
            resource_group_name=resource_group.name,
            ip_configurations=[ip_config]
        )

        # Create a virtual machine
        vm = VirtualMachine(self, 'vm',
            name=vm_name,
            location=resource_group.location,
            resource_group_name=resource_group.name,
            network_interface_ids=[nic.id],
            vm_size=vm_size,
            delete_os_disk_on_termination=True,
            delete_data_disks_on_termination=True,
            os_profile={
                'computer_name': 'hostname',
                'admin_username': admin_username,
                'admin_password': admin_password
            },
            os_profile_linux_config={
                'disable_password_authentication': False
            },
            storage_os_disk={
                'name': 'my_os_disk',
                'caching': 'ReadWrite',
                'create_option': 'FromImage',
                'managed_disk_type': 'Standard_LRS'
            },
            storage_image_reference={
                'publisher': 'Canonical',
                'offer': 'UbuntuServer',
                'sku': '18.04-LTS',
                'version': 'latest'
            }
        )

        # Create a container registry
        registry = ContainerRegistry(self, 'acr',
            name=acr_name,
            resource_group_name=resource_group.name,
            location=resource_group.location,
            sku='Basic',
            admin_enabled=True
        )

        # Create PostgreSQL server
        pg_server = PostgreSqlServer(self, 'pg_server',
            name=pg_server_name,
            resource_group_name=resource_group.name,
            location=resource_group.location,
            administrator_login=pg_admin_username,
            administrator_login_password=pg_admin_password,
            version='11',
            sku={
                'name': 'B_Gen5_1'
            },
            storage_profile={
                'storage_mb': 5120
            }
        )

        # Create PostgreSQL database
        pg_database = PostgreSqlDatabase(self, 'pg_database',
            name=pg_db_name,
            resource_group_name=resource_group.name,
            server_name=pg_server.name
        )

        # Allow Azure services to access the PostgreSQL server
        PostgreSqlFirewallRule(self, 'pg_firewall_rule',
            name='AllowAllWindowsAzureIps',
            resource_group_name=resource_group.name,
            server_name=pg_server.name,
            start_ip_address='0.0.0.0',
            end_ip_address='0.0.0.0'
        )

        # Add environment variables to the VM
        vm.os_profile['custom_data'] = f"""#!/bin/bash
        echo 'export PGHOST={pg_server_name}.postgres.database.azure.com' >> /etc/environment
        echo 'export PGDATABASE={pg_db_name}' >> /etc/environment
        echo 'export PGUSER={pg_admin_username}' >> /etc/environment
        echo 'export PGPASSWORD={pg_admin_password}' >> /etc/environment
        source /etc/environment
        """

app = App()
MyStack(app, "my-stack")
app.synth()
