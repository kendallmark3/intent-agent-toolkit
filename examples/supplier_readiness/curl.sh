#!/usr/bin/env bash
# Exercise a running server (make run) from another terminal. Requires IAT_JWT_SECRET in .env.
set -euo pipefail
BASE="${IAT_BASE_URL:-http://127.0.0.1:8000}"
TOKEN="$(uv run iat-token --sub alice)"
curl -s "$BASE/health/ready"; echo
curl -s -X POST "$BASE/v1/agents/supplier-readiness/invoke" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -H "X-Request-ID: demo-request-0001" \
  -d '{"message": "Can Supplier Acme be approved for onboarding?"}'; echo
