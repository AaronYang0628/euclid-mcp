# Kubernetes Manifests for Euclid Catalog MCP Service

This directory contains Kubernetes manifests for deploying the Euclid Catalog MCP service.

## Resources

- **pvc.yaml**: PersistentVolumeClaim for storing catalog data (100Gi, local-path storage)
- **configmap.yaml**: Environment variables for the service
- **deployment.yaml**: Deployment with 2 replicas, resource limits, and TCP health checks
- **service.yaml**: ClusterIP service exposing port 8000
- **ingress.yaml**: Ingress configuration with TLS support (self-signed CA)

## Important Notes

- This is an MCP (Model Context Protocol) server, not a traditional HTTP API
- The service uses SSE (Server-Sent Events) transport on port 8000
- Health checks use TCP socket probes instead of HTTP endpoints
- Catalog files should be placed in `/data/catalogs` within the container

## Prerequisites

1. Kubernetes cluster (v1.19+)
2. kubectl configured
3. NGINX Ingress Controller installed
4. cert-manager installed with self-signed CA issuer configured
5. Storage class "local-path" available (or modify pvc.yaml)

## Build Docker Image

```bash
cd /workspaces/euclid-mcp/analysis-catalog
docker build -t euclid-catalog-mcp:latest .
```

If using a private registry:
```bash
docker tag euclid-catalog-mcp:latest your-registry.com/euclid-catalog-mcp:latest
docker push your-registry.com/euclid-catalog-mcp:latest
```

## Deploy

### Deploy all resources at once:
```bash
kubectl apply -f manifests/
```

### Or deploy individually in order:
```bash
kubectl apply -f manifests/pvc.yaml
kubectl apply -f manifests/configmap.yaml
kubectl apply -f manifests/deployment.yaml
kubectl apply -f manifests/service.yaml
kubectl apply -f manifests/ingress.yaml
```

## Configuration

### Update Ingress Host

Edit `manifests/ingress.yaml` and replace `euclid-catalog.example.com` with your actual domain.

### Update Storage Class

The PVC is configured for `local-path` storage with `ReadWriteOnce` access. If your cluster uses a different storage class, edit `manifests/pvc.yaml`:

```yaml
spec:
  accessModes:
    - ReadWriteMany  # Change if needed
  storageClassName: your-storage-class
```

### Adjust Resources

Edit `manifests/deployment.yaml` to adjust CPU/memory limits based on your needs:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

### Environment Variables

Edit `manifests/configmap.yaml` to configure:
- `CATALOG_DATA_PATH`: Path where catalog files are stored (default: /data/catalogs)
- `MCP_SERVER_NAME`: Name of the MCP server instance

## Verify Deployment

```bash
# Check pods
kubectl get pods -l app=euclid-catalog-mcp

# Check service
kubectl get svc euclid-catalog-mcp

# Check ingress
kubectl get ingress euclid-catalog-mcp

# Check PVC
kubectl get pvc euclid-catalog-pvc

# View logs
kubectl logs -l app=euclid-catalog-mcp -f
```

## Upload Catalog Data

```bash
# Get pod name
POD_NAME=$(kubectl get pods -l app=euclid-catalog-mcp -o jsonpath='{.items[0].metadata.name}')

# Copy catalog files to the pod
kubectl cp your-catalog.fits $POD_NAME:/data/catalogs/
```

## Access the Service

### From within the cluster:
```
http://euclid-catalog-mcp:8000
```

### From outside (via Ingress):
```
https://euclid-catalog.example.com
```

Note: This is an MCP server using SSE transport, not a REST API. You'll need an MCP client to interact with it.

## Scaling

### Manual scaling:
```bash
kubectl scale deployment euclid-catalog-mcp --replicas=5
```

## Troubleshooting

### Check pod status:
```bash
kubectl describe pod -l app=euclid-catalog-mcp
```

### Check events:
```bash
kubectl get events --sort-by='.lastTimestamp'
```

### Check logs:
```bash
kubectl logs -l app=euclid-catalog-mcp --tail=100
```

### Test service connectivity:
```bash
# Test TCP connection
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  nc -zv euclid-catalog-mcp 8000
```

## Cleanup

```bash
kubectl delete -f manifests/
```
