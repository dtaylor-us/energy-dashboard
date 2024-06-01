### `README.md`

```markdown
# Energy Dashboard Terraform Configuration

Welcome to the Terraform configuration for the Energy Dashboard project. This guide will help you set up and manage the infrastructure required for the Energy Dashboard application.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Terraform Commands](#terraform-commands)
- [Environment Specific Configurations](#environment-specific-configurations)
- [Docker Configuration](#docker-configuration)
- [Adding New Resources](#adding-new-resources)
- [Best Practices](#best-practices)

## Prerequisites

Before you begin, ensure you have the following installed:
- [Terraform](https://www.terraform.io/downloads.html)
- [Git](https://git-scm.com/downloads)
- An [Azure](https://azure.microsoft.com/en-us/free/) account with sufficient permissions to create resources
- [Docker](https://www.docker.com/products/docker-desktop)

## Project Structure

The project is organized into modules and environment-specific configurations to maintain a clean and scalable setup.

```
energy-dashboard/
├── environments/
│   └── prod/
│       ├── main.tf
│       ├── variables.tf
│       ├── terraform.tfvars
│       └── README.md
├── global/
│   ├── main.tf
│   └── variables.tf
├── modules/
│   ├── network/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── vm/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── docker/
│   ├── Dockerfile
├── scripts/
│   ├── package.sh
│   ├── publish.sh
│   └── deploy.sh
└── README.md
```

## Getting Started

### 1. Clone the Repository

Clone the repository to your local machine:

```bash
git clone https://github.com/traliach/energy-dashboard.git
cd energy-dashboard
```

### 2. Set Up Your Environment

Navigate to the `environments/prod` directory:

```bash
cd environments/prod
```

### 3. Configure Variables

Edit the `terraform.tfvars` file to set the appropriate values for your environment. Here's an example:

```hcl
resource_group_name = "your_resource_group_name"
location            = "East US"
vnet_name           = "your_vnet_name"
address_space       = ["10.0.0.0/16"]
subnet_name         = "your_subnet_name"
subnet_prefixes     = ["10.0.1.0/24"]
vm_name             = "your_vm_name"
vm_size             = "Standard_DS1_v2"
admin_username      = "adminuser"
public_key_path     = "path_to_your_public_ssh_key"
pg_host             = "your_postgresql_host"
pg_user             = "your_postgresql_user"
pg_password         = "your_postgresql_password"
```

## Terraform Commands

### Initialize Terraform

Initialize the Terraform configuration. This step downloads the required providers and sets up your environment.

```bash
terraform init
```

### Validate the Configuration

Validate the Terraform configuration files to ensure syntax correctness and configuration validity.

```bash
terraform validate
```

### Plan the Deployment

Create an execution plan, which shows the changes that Terraform will make to your infrastructure.

```bash
terraform plan -var-file="terraform.tfvars"
```

### Apply the Configuration

Apply the changes required to reach the desired state of the configuration. Terraform will prompt for confirmation before making any changes.

```bash
terraform apply -var-file="terraform.tfvars"
```

### Destroy the Infrastructure

If you need to tear down the infrastructure, you can use the `destroy` command.

```bash
terraform destroy -var-file="terraform.tfvars"
```

## Environment Specific Configurations

Each environment (e.g., `prod`, `dev`, `staging`) has its own directory under `environments/`. These directories contain the environment-specific `main.tf`, `variables.tf`, and `terraform.tfvars` files. This organization helps manage configurations for different stages of development and deployment.

## Docker Configuration

### Dockerfile

A Dockerfile is provided to containerize the application. The Dockerfile is located in the `docker` directory.

#### `docker/Dockerfile`
```Dockerfile
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Run app.py when the container launches
CMD ["python", "app.py"]
```

### Bash Scripts

Several bash scripts are provided to automate the packaging, publishing, and deploying processes.

#### `scripts/package.sh`

```bash
#!/bin/bash

# Build the Docker image
docker build -t energy-dashboard:latest .
```

#### `scripts/publish.sh`

```bash
#!/bin/bash

# Variables
ACR_NAME="yourACRName"

# Log in to Azure Container Registry
az acr login --name $ACR_NAME

# Tag the Docker image
docker tag energy-dashboard:latest $ACR_NAME.azurecr.io/energy-dashboard:latest

# Push the Docker image to ACR
docker push $ACR_NAME.azurecr.io/energy-dashboard:latest
```

#### `scripts/deploy.sh`

```bash
#!/bin/bash

# Variables
VM_IP="your_vm_ip"
VM_USERNAME="your_vm_username"
DOCKER_IMAGE="yourACRName.azurecr.io/energy-dashboard:latest"

# SSH into the VM and pull the Docker image
ssh $VM_USERNAME@$VM_IP << EOF
docker pull $DOCKER_IMAGE
docker run -d -p 80:80 $DOCKER_IMAGE
EOF
```

### Verify App is Accessible

You can manually check if the app is running by accessing `http://<your_vm_ip>` in a web browser.

## Adding New Resources

### Adding a New Module

1. Create a new directory under `modules/` for the new resource (e.g., `database`).
2. Add `main.tf`, `variables.tf`, and `outputs.tf` files to define the resource.
3. Reference the new module in the environment-specific `main.tf` file.

Example of referencing a new module in `environments/prod/main.tf`:

```hcl
module "database" {
  source              = "../../modules/database"
  resource_group_name = var.resource_group_name
  location            = var.location
  ...
}
```

### Define Variables and Outputs

Ensure all necessary variables are declared in the module’s `variables.tf` and corresponding outputs are declared in `outputs.tf`.

## Best Practices

1. **Keep Modules Reusable**: Write modules to be reusable across different environments and projects.
2. **Use .tfvars for Sensitive Data**: Store sensitive data like passwords and keys in `.tfvars` files or use Terraform Cloud/Enterprise for secret management.
3. **Version Control**: Commit your configuration files to version control but exclude sensitive information and state files.
4. **Consistent Naming**: Use a consistent naming convention for resources to avoid confusion and make management easier.

## Conclusion

By following this guide, you should be able to set up and manage the infrastructure for the Energy Dashboard project using Terraform. If you encounter any issues or have questions, feel free to reach out to the team for support.

Happy coding!
```

