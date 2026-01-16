# LL-238: Vertex AI RAG Init Failure - Root Cause Identified

**ID**: LL-238
**Date**: 2026-01-16
**Severity**: CRITICAL
**Category**: Operational Integrity

## Problem
Vertex AI RAG showing `vertex_ai_rag_enabled: false` with no visible error.

## Root Cause (Identified via /diagnostics endpoint)
```json
{
  "vertex_ai": {
    "enabled": false,
    "init_error": "Vertex AI RAG not initialized - check GCP credentials/permissions",
    "package_available": true,
    "env_vars": {
      "GOOGLE_CLOUD_PROJECT": "igor-trading-2025-v2",
      "VERTEX_AI_LOCATION": "us-central1",
      "GOOGLE_APPLICATION_CREDENTIALS": "NOT SET"
    }
  }
}
```

Cloud Run service account needs:
1. `roles/aiplatform.user` permission
2. OR RAG Engine API enabled in GCP project

## Fix Applied
1. Added `/diagnostics` endpoint to webhook (PR #2045)
2. Exposed `vertex_ai_init_error` in `/health` response
3. Version bumped to 3.6.0

## Remaining Action
Grant IAM permission to Cloud Run service account:
```bash
PROJECT_NUMBER=$(gcloud projects describe igor-trading-2025-v2 --format="value(projectNumber)")
gcloud projects add-iam-policy-binding igor-trading-2025-v2 \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

## Tags
vertex-ai, rag, iam, permissions, cloud-run, diagnostics

