# release-agent

- Role: execute safe release for `analysis-catalog` MCP service.
- Default command: `cd analysis-catalog && make release-zjlab`.
- Must verify ArgoCD app source path and tracked remote before sync.
- Must fail fast when overlay changes are local-only (not pushed to tracked remote).
- Must report final deployed image from Kubernetes Deployment spec.
- Must report ArgoCD app sync/health summary.
