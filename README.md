# MindBridge Backend Router

This is a FastAPI-based backend router that acts as an OpenAI-compatible gateway to various LLM providers. It is designed to be deployed as a standalone service and integrated with the MindBridge Cloudflare Worker.

## Features

- **OpenAI-Compatible API:** Drop-in replacement for the OpenAI Chat Completions API (`/v1/chat/completions`) and Models API (`/v1/models`).
- **Multi-Provider Routing:** Route requests to different LLM providers (OpenAI, Anthropic, Google, etc.) using a simple model naming convention (`mindbridge:provider/model`).
- **Centralized Authentication:** Secure the router with a single API key.
- **CORS Support:** Configurable CORS for easy integration with web frontends.
- **Easy Deployment:** Deploy to Railway, Fly.io, or any other container-based platform using the provided Dockerfile.

## Prerequisites

- Python 3.11+
- Docker (for containerized deployment)
- A Railway account (or another container hosting provider)
- API keys for the LLM providers you want to use (OpenAI, Anthropic, Google, etc.)

## Installation & Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd mindbridge-router
    ```

2.  **Install dependencies (for local development):**

    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configure environment variables:**

    Copy the `.env.example` file to `.env` and fill in the required values:

    ```bash
    cp .env.example .env
    ```

## Configuration

### `.env` File

-   `MINDBRIDGE_API_KEY`: **(Required)** A secret key to authenticate requests to this router. This is the key your Cloudflare Worker will use.
-   `PORT`: The port the FastAPI server will run on (default: `8000`).
-   `CORS_ORIGINS`: A comma-separated list of allowed origins for CORS (e.g., `https://api.soul-os.cc,http://localhost:3000`).
-   `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`: Your API keys for the respective LLM providers.

## Running Locally

To run the server locally for development:

```bash
python app/main.py
```

The server will be available at `http://localhost:8000`. You can access the interactive API documentation at `http://localhost:8000/docs`.

## Deployment to Railway

This project is configured for easy deployment to Railway.

1.  **Create a new project on Railway.**
2.  **Connect your GitHub repository.**
3.  **Configure environment variables** in the Railway project settings. Add the same variables from your `.env` file.
4.  **Railway will automatically build and deploy** the application using the provided `Dockerfile` and `railway.json`.
5.  Once deployed, Railway will provide you with a public URL for your router service. This is your `MINDBRIDGE_ROUTER_URL`.

## CI/CD Workflows

GitHub Actions workflows are provided for:

- Backend CI + Railway CD
- Frontend CI/CD (Cloudflare Pages, path-scoped)
- Cloudflare Worker CI/CD + D1 migrations (path-scoped)

See `docs/ci-cd.md` for setup details (required secrets/variables and deployment policy).

## Integration with Cloudflare Worker

To integrate the router with your existing MindBridge Cloudflare Worker:

1.  **Set Environment Variables in Cloudflare:**

    In your Cloudflare Worker settings, add the following environment variables:

    -   `MINDBRIDGE_ROUTER_URL`: The public URL of your deployed FastAPI router (from Railway).
    -   `MINDBRIDGE_API_KEY`: The secret key you configured for the router.

2.  **Update Worker Code:**

    Modify your Cloudflare Worker (`worker/index.ts`) to forward `/v1/chat/completions` requests to the new router.

    ```typescript
    // In your worker's fetch handler

    const url = new URL(request.url);
    const path = url.pathname;

    if (path === '/v1/chat/completions' && request.method === 'POST') {
      const MINDBRIDGE_ROUTER_URL = env.MINDBRIDGE_ROUTER_URL;
      const MINDBRIDGE_API_KEY = env.MINDBRIDGE_API_KEY;

      if (!MINDBRIDGE_ROUTER_URL || !MINDBRIDGE_API_KEY) {
        return new Response('MindBridge router is not configured', { status: 500 });
      }

      // Forward the request to the router
      const routerUrl = `${MINDBRIDGE_ROUTER_URL}/v1/chat/completions`;

      const response = await fetch(routerUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${MINDBRIDGE_API_KEY}`,
        },
        body: await request.text(),
      });

      return response;
    }

    // ... (rest of your worker code)
    ```

## API Reference

### `POST /v1/chat/completions`

-   **Description:** Creates a chat completion.
-   **Request Body:** OpenAI-compatible `ChatCompletionRequest`.
-   **Response:** OpenAI-compatible `ChatCompletionResponse`.

### `GET /v1/models`

-   **Description:** Lists all available models.
-   **Response:** OpenAI-compatible `ModelList`.

### `GET /health`

-   **Description:** Health check endpoint.

### `GET /providers`

-   **Description:** (Debug) Lists all configured providers and their models.
