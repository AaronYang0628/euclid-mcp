SHELL := /usr/bin/env bash

ENV ?= env-zjlab
TAG ?=
ARGOCD_APP ?= euclid-catalog-mcp

.PHONY: help release release-zjlab release-72602 tag-only sync status

help:
	@printf "%s\n" \
	  "Targets:" \
	  "  make release ENV=env-zjlab [TAG=v2026041301]     Build+push+update overlay+sync" \
	  "  make release-zjlab [TAG=...]                      Release to env-zjlab" \
	  "  make release-72602 [TAG=...]                      Release to env-72602" \
	  "  make tag-only ENV=env-zjlab TAG=v...             Update overlay tag only" \
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
