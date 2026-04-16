SHELL := /usr/bin/env bash

ENV ?= env-zjlab
TAG ?=
ARGOCD_APP ?= euclid-catalog-mcp
CLIENT_PORT ?= 6275
SERVER_PORT ?= 6278
MCP_HTTP_PORT ?= 8000

.PHONY: help release release-zjlab release-72602 tag-only sync status inspect-http inspect-stdio

help:
	@printf "%s\n" \
	  "Targets:" \
	  "  make release ENV=env-zjlab [TAG=v2026041301]     Build+push+update overlay+sync" \
	  "  make release-zjlab [TAG=...]                      Release to env-zjlab" \
	  "  make release-72602 [TAG=...]                      Release to env-72602" \
	  "  make tag-only ENV=env-zjlab TAG=v...             Update overlay tag only" \
	  "  make inspect-http [CLIENT_PORT=6275 SERVER_PORT=6278 MCP_HTTP_PORT=8000]" \
	  "                                                   Start streamable-http server + inspector" \
	  "  make inspect-stdio [CLIENT_PORT=6275 SERVER_PORT=6278]" \
	  "                                                   Start inspector in stdio mode" \
	  "  make sync [ARGOCD_APP=euclid-catalog-mcp]        Trigger Argo CD sync" \
	  "  make status [ARGOCD_APP=euclid-catalog-mcp]      Show Argo CD app status"

release:
	@./ops/release.sh --env "$(ENV)" $(if $(TAG),--tag "$(TAG)",)

release-zjlab:
	@./ops/release.sh --env env-zjlab $(if $(TAG),--tag "$(TAG)",)

release-72602:
	@./ops/release.sh --env env-72602 $(if $(TAG),--tag "$(TAG)",)

tag-only:
	@test -n "$(TAG)" || (echo "TAG is required for tag-only" >&2; exit 1)
	@./ops/release.sh --env "$(ENV)" --tag "$(TAG)" --skip-build --skip-push --skip-sync

sync:
	@if command -v argocd >/dev/null 2>&1; then \
	  argocd app sync "$(ARGOCD_APP)" --prune && \
	  argocd app wait "$(ARGOCD_APP)" --health --sync --timeout 300; \
	else \
	  kubectl -n argocd annotate application "$(ARGOCD_APP)" "euclid-mcp/sync-ts=$$(date +%s)" --overwrite; \
	  echo "argocd CLI not found; annotation refresh sent."; \
	fi

status:
	@if command -v argocd >/dev/null 2>&1; then \
	  argocd app get "$(ARGOCD_APP)"; \
	else \
	  kubectl -n argocd get application "$(ARGOCD_APP)" -o wide; \
	fi

inspect-http:
	@CLIENT_PORT="$(CLIENT_PORT)" SERVER_PORT="$(SERVER_PORT)" MCP_HTTP_PORT="$(MCP_HTTP_PORT)" ./ops/inspect-http.sh

inspect-stdio:
	@CLIENT_PORT="$(CLIENT_PORT)" SERVER_PORT="$(SERVER_PORT)" ALLOWED_ORIGINS="http://127.0.0.1:$(CLIENT_PORT),http://localhost:$(CLIENT_PORT)" DANGEROUSLY_OMIT_AUTH=true npx @modelcontextprotocol/inspector ./.venv/bin/python -m euclid_catalog_mcp.server --stdio
