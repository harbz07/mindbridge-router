# CI/CD Runbook (Frontend, Backend, Cloudflare Worker + Databases)

This repository is the backend router, but it now includes workflow definitions for:

- Backend CI + CD to Railway
- Frontend CI + CD to Cloudflare Pages (conditional)
- Cloudflare Worker CI + CD + D1 migrations (conditional)

The frontend and worker workflows are path-scoped and only run when those folders exist in this repository.

## Pipeline Topology

### 1) Backend (FastAPI) on Railway

- **CI workflow:** `.github/workflows/backend-ci.yml`
  - Runs on PRs and pushes that modify backend files.
  - Installs Python dependencies and runs:
    - `pytest -q`
    - `python -m compileall -q app`
- **CD workflow:** `.github/workflows/backend-cd-railway.yml`
  - Runs on `main` when backend files change, or manually via workflow dispatch.
  - Deploys with Railway CLI using:
    - project: `7f011784-7ff6-408e-9322-f31a3a7e596e`
    - environment: `dd73b5dc-4703-43ee-ad35-0389dac2d529`
    - service: `e2cacd2b-15cf-41d4-9efd-cd43a1416b7f`

Equivalent targeting (for local debugging) is:

```bash
railway ssh \
  --project=7f011784-7ff6-408e-9322-f31a3a7e596e \
  --environment=dd73b5dc-4703-43ee-ad35-0389dac2d529 \
  --service=e2cacd2b-15cf-41d4-9efd-cd43a1416b7f
```

### 2) Frontend on Cloudflare Pages

- **Workflow:** `.github/workflows/frontend-ci-cd.yml`
  - Runs only when `frontend/**` changes.
  - CI: install, lint, test, build.
  - CD (`main` or manual): deploy `frontend/dist` using Wrangler Pages.

### 3) Cloudflare Worker + D1 Database

- **Workflow:** `.github/workflows/cloudflare-worker-ci-cd.yml`
  - Runs only when `worker/**` changes.
  - CI: install, lint, test, optional build.
  - CD (`main` or manual): deploy Worker.
  - DB migrations: applies `wrangler d1 migrations apply <db-name> --remote` when enabled.

## Required GitHub Secrets and Variables

Set these in **Settings > Secrets and variables > Actions**.

### Required secrets

- `RAILWAY_TOKEN`
- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

### Recommended repository variables

- `BACKEND_HEALTHCHECK_URL`  
  Example: `https://<railway-backend-domain>`
- `RAILWAY_PROJECT_ID` (optional override)
- `RAILWAY_ENVIRONMENT_ID` (optional override)
- `RAILWAY_SERVICE_ID` (optional override)
- `CF_PAGES_PROJECT_NAME` (for frontend deploys)
- `CF_D1_DATABASE_NAME` (for Worker migration step)

## Suggested Deployment Policy

- Use PRs for all changes.
- Let CI pass before merging.
- Deploy production from `main` only.
- Keep `production` environment protection enabled in GitHub for manual approvals if needed.

## Notes

- Backend deploy is pinned to your provided Railway target IDs by default.
- Frontend and worker workflows are intentionally conditional so they do not fail in a backend-only repo.
- If frontend/worker live in separate repos, copy the corresponding workflow file into each repository.
