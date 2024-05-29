# dev-dashboard

A platform where developers can manage their tasks, view GitHub repositories, monitor AWS resources, and check relevant programming news.

# ArgoCD Setup

## 1. Setting Up ArgoCD in Your Cluster

### 1.1 Install ArgoCD:

```shell
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```   

### 1.2. Access the ArgoCD API Server:

For simplicity, you can expose the ArgoCD API server using a NodePort:

```shell
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "NodePort"}}'
```
To find out the NodePort allocated to ArgoCD:

```shell
kubectl get svc argocd-server -n argocd
```
The NodePort will be an integer in the 30000-32767 range.

To access the ArgoCD dashboard, navigate to `https://<your-cluster-ip>:<node-port>`. The default username is `admin`, and the password is the pod name of the ArgoCD API server.

Retrieve it using:

````shell
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d; echo
 ````

## 2. Setting Up the ArgoCD CLI
   Download the appropriate version of the ArgoCD CLI from the official releases page. Instructions differ based on your operating system:

For macOS:

```shell
brew install argocd
```
For Linux:

```shell
curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x /usr/local/bin/argocd
```

## 3. Login to ArgoCD
   Use the CLI to log in:
```shell
argocd login <your-cluster-ip>:<node-port> --username admin --password <argocd-server-pod-name>
```

## 4. Create an ArgoCD Application
   An ArgoCD application is a logical grouping of Kubernetes resources that come from a Git source repository.

```shell
argocd app create <app-name> \
--repo https://github.com/<username>/<repo>.git \
--path <path-in-repo> \
--dest-server https://kubernetes.default.svc \
--dest-namespace default
```

Ensure that the path you provide exists within the repository and contains Kubernetes manifests.

## 5. Synchronize the Application
   To deploy the Kubernetes resources:

```shell
argocd app sync <app-name>
```

## 6. Continuous Synchronization
   By default, ArgoCD only deploys resources when you explicitly synchronize an application. However, you can enable automatic synchronization:

```shell
argocd app set <app-name> --sync-policy automated
```
This way, if you change your Git repo, ArgoCD will automatically apply those changes to the cluster.

## 7. Granting Access & Projects
   ArgoCD has a detailed RBAC system and organizes deployments into "projects." The default project is "default", but for finer-grained access control, consider creating separate
   projects and grant necessary permissions.

