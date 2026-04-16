# Euclid MCP Monorepo

This repository contains MCP services and deployment assets for Euclid data workflows.

## Projects

- `analysis-catalog/`: Euclid Catalog MCP service (FITS parsing, S3/local catalog access)
- `mcp-inspector/`: Kubernetes/Argo CD manifests related to inspector deployment

## Local Development (quick)

For local testing, use the user guide in:

- `analysis-catalog/README.md`

Fast path:

```bash
cd /workspaces/euclid-mcp/analysis-catalog
make inspect-http
```

## Deployment / Release

Release commands are executed in `analysis-catalog/`:

```bash
cd /workspaces/euclid-mcp/analysis-catalog
make release-zjlab
```

Common variants:

```bash
make release-72602 TAG=v2026041301
make tag-only ENV=env-zjlab TAG=v2026041301
```

Detailed deployment and Argo CD operations:

- `analysis-catalog/docs/release-ops.md`

## Documentation Map

- User guide: `analysis-catalog/README.md`
- Developer/update guide: `analysis-catalog/UPDATE.md`
- Release/Ops guide: `analysis-catalog/docs/release-ops.md`
