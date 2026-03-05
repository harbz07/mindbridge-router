# CI/CD Architecture

This document describes the CI/CD pipeline strategy for the MindBridge infrastructure:
the **backend** (Railway), **Cloudflare Workers** (including D1 databases), and the **frontend** (Cloudflare Pages).

---

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Actions                           │
│                                                                 │
│  ┌──────────────┐  ┌───────────────────┐  ┌──────────────────┐  │
│  │  Backend CI   │  │ Cloudflare Workers│  │  Frontend Deploy │  │
│  │              │  │                   │  │                  │  │
│  │ Lint → Test  │  │ TypeCheck → Test  │  │ Lint → Build     │  │
│  │ → Docker     │  │ → Migrate D1     │  │ → Deploy Pages   │  │
│  │ → Railway    │  │ → Deploy Worker  │  │                  │  │
│  └──────┬───────┘  └────────┬──────────┘  └────────┬─────────┘  │
│         │                   │                      │            │
└─────────┼───────────────────┼──────────────────────┼────────────┘
          │                   │                      │
          ▼                   ▼                      ▼
    ┌──────────┐     ┌──────────────┐       ┌──────────────┐
    │ Railway  │     │  Cloudflare  │       │  Cloudflare  │
    │ (Docker) │     │   Workers    │       │    Pages     │
    └──────────┘     │   + D1 DB   │       └──────────────┘
                     └──────────────┘
```

---

## 1. Backend (Railway)

**Workflow files:** `backend-ci.yml` + `backend-deploy.yml`

### CI Pipeline (`backend-ci.yml`)

Triggers on push/PR to `main` when `app/`, `requirements.txt`, `Dockerfile`, or `tests/` change.

| Job | What it does |
|-----|-------------|
| **Lint** | Runs `ruff check` and `ruff format --check` on `app/` |
| **Test** | Runs `pytest tests/` with a mock API key |
| **Docker Build** | Builds the Docker image and verifies the container starts and `/health` responds |

### CD Pipeline (`backend-deploy.yml`)

Triggers on push to `main` (same path filters). Calls the CI workflow as a gate.

| Step | What it does |
|------|-------------|
| **CI Gate** | Runs the full CI pipeline first |
| **Deploy** | Uses `railway up` CLI to deploy to the configured service |
| **Health Check** | Waits for deployment, then hits `/health` |

### Railway Service Details

```
Project ID:     7f011784-7ff6-408e-9322-f31a3a7e596e
Environment ID: dd73b5dc-4703-43ee-ad35-0389dac2d529
Service ID:     e2cacd2b-15cf-41d4-9efd-cd43a1416b7f
```

### Required Secrets

| Secret | Where to set | Description |
|--------|-------------|-------------|
| `RAILWAY_TOKEN` | GitHub repo secrets | Railway API token from [railway.app/account/tokens](https://railway.app/account/tokens) |

---

## 2. Cloudflare Workers + D1 Database

**Workflow file:** `cloudflare-workers.yml`

Triggers on push/PR to `main` when `worker/`, `wrangler.toml/jsonc/json`, or `migrations/` change.
Also supports `workflow_dispatch` with options to skip migrations or do a dry run.

### Pipeline Stages

| Job | What it does |
|-----|-------------|
| **Type Check** | Runs `tsc --noEmit` and `wrangler deploy --dry-run` |
| **Test** | Runs `npm test` (Vitest with `@cloudflare/vitest-pool-workers`) |
| **Migrate** | Applies D1 migrations via `wrangler d1 migrations apply DB --remote` |
| **Deploy** | Runs `wrangler deploy` to push the Worker live |

### D1 Database Migrations

Migrations live in the `migrations/` directory. The naming convention is:

```
migrations/
  0001_create_initial_tables.sql
  0002_add_indexes.sql
  ...
```

Wrangler tracks which migrations have been applied and only runs new ones.

### Required Secrets

| Secret | Where to set | Description |
|--------|-------------|-------------|
| `CLOUDFLARE_API_TOKEN` | GitHub repo secrets | Cloudflare API token with Workers/D1 permissions |
| `CLOUDFLARE_ACCOUNT_ID` | GitHub repo secrets | Your Cloudflare account ID |

---

## 3. Frontend (Cloudflare Pages)

**Workflow file:** `frontend-deploy.yml`

Triggers on push/PR to `main` when `frontend/` changes.

### Pipeline Stages

| Job | What it does |
|-----|-------------|
| **Lint & Type Check** | Runs ESLint and TypeScript checks |
| **Build** | Runs `npm run build`, uploads artifacts |
| **Deploy Preview** | On PRs: deploys a preview branch to Cloudflare Pages |
| **Deploy Production** | On push to main: deploys to production on Cloudflare Pages |

### Required Secrets / Variables

| Secret/Variable | Where to set | Description |
|--------|-------------|-------------|
| `CLOUDFLARE_API_TOKEN` | GitHub repo secrets | Same token as Workers (needs Pages permissions too) |
| `CLOUDFLARE_ACCOUNT_ID` | GitHub repo secrets | Your Cloudflare account ID |
| `CLOUDFLARE_PAGES_PROJECT` | GitHub repo variables (optional) | Pages project name (defaults to `mindbridge-frontend`) |

---

## Setup Instructions

### 1. Generate a Railway Token

1. Go to [railway.app/account/tokens](https://railway.app/account/tokens)
2. Create a new token with deploy permissions
3. Add it as `RAILWAY_TOKEN` in GitHub repo Settings > Secrets and variables > Actions

### 2. Generate a Cloudflare API Token

1. Go to [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens)
2. Create a new token with these permissions:
   - **Account** > Workers Scripts > Edit
   - **Account** > D1 > Edit
   - **Account** > Cloudflare Pages > Edit
3. Add it as `CLOUDFLARE_API_TOKEN` in GitHub repo secrets
4. Add your account ID as `CLOUDFLARE_ACCOUNT_ID` in GitHub repo secrets

### 3. Create GitHub Environment

1. Go to GitHub repo Settings > Environments
2. Create an environment called `production`
3. Optionally add protection rules (required reviewers, wait timer)

### 4. Verify

Push a change to `main` or open a PR to trigger the workflows.
Check the Actions tab to see pipeline execution.

---

## Manual Triggers

All deploy workflows support `workflow_dispatch` for manual runs from the GitHub Actions UI.

The Cloudflare Workers workflow also supports:
- **Skip migrations**: Run deployment without applying D1 migrations
- **Dry run**: Validate configuration without deploying

---

## Directory Structure (Expected)

```
.
├── .github/workflows/
│   ├── backend-ci.yml           # Backend lint, test, docker build
│   ├── backend-deploy.yml       # Backend deploy to Railway
│   ├── cloudflare-workers.yml   # Workers + D1 deploy
│   └── frontend-deploy.yml      # Frontend deploy to Pages
├── app/                          # Backend (FastAPI)
│   ├── main.py
│   ├── models.py
│   ├── auth.py
│   ├── memory.py
│   └── providers/
├── tests/                        # Backend tests
├── worker/                       # Cloudflare Worker source (if co-located)
│   └── index.ts
├── migrations/                   # D1 database migrations
├── frontend/                     # Frontend source (if co-located)
│   ├── package.json
│   ├── src/
│   └── dist/
├── Dockerfile
├── railway.json
├── requirements.txt
├── pyproject.toml
└── wrangler.toml                 # Wrangler config (if co-located)
```

> If the frontend or workers live in separate repos, copy the relevant
> workflow file to that repo and adjust paths accordingly.
