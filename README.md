# Shopping Agent

[![CI/CD](https://github.com/Kirank0/shopping-agent/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/Kirank0/shopping-agent/actions/workflows/ci.yml)

An AI shopping assistant for a small natural-foods store. Ask it questions in plain English,
and it searches products, summarizes reviews and places orders.

Built with LangChain, Streamlit, GPT OSS 120B on Groq Cloud, and uv.

> [!IMPORTANT]
> **Create your `.env` file with a Groq API key right after cloning, before you run anything.**
> The app needs it whether you run it with Docker or with uv. It is not included in the repo.
> Without it, `docker compose up` stops with an error that `.env` is missing, and the local
> run shows "GROQ_API_KEY is not set".

## 1. Get the code

```
git clone https://github.com/Kirank0/shopping-agent.git
cd shopping-agent
```

## 2. Add your Groq API key (required)

1. Sign in at https://console.groq.com/keys and click **Create API Key**. It's free.
   Copy the key; it starts with `gsk_`.
2. In the project folder, copy the template to a new file named `.env`:
   ```
   cp .env.example .env
   ```
   On Windows Command Prompt use `copy .env.example .env` instead.
3. Open `.env` in a text editor and replace the placeholder with your key:
   ```
   GROQ_API_KEY=gsk_your_real_key_here
   ```
   No quotes and no spaces around `=`.

Keep this key private. `.env` is gitignored, so it is never committed or pushed,
and it is not copied into the Docker image either.

## 3a. Run with Docker (recommended)

Needs [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine on Linux).
**Make sure Docker is running** and that you've created `.env` (step 2) before you start.

```
docker compose up -d --build
```

Open http://localhost:8501 (or `http://<server-ip>:8501` from another computer).
The first build takes a few minutes; later starts take seconds.

| Task | Command |
|---|---|
| Start | `docker compose up -d` |
| Stop | `docker compose down` |
| Check it's running | `docker compose ps` (look for `healthy`) |
| View logs / errors | `docker compose logs -f` (Ctrl+C to exit) |
| After changing code or `git pull` | `docker compose up -d --build` (without `--build` the old code keeps running) |
| Reset the database (deletes orders) | `docker compose down -v`, then `docker compose up -d` |

The database lives in the `store-data` Docker volume, so orders survive restarts and rebuilds.
The API key is read from `.env` at runtime and is never copied into the image.
The container restarts automatically whenever Docker starts, until you run `docker compose down`.

## 3b. Run locally without Docker (for development)

Needs Python 3.12+, [uv](https://docs.astral.sh/uv/) (`pip install uv` works; if the `uv`
command isn't found afterwards, use `python -m uv` in place of `uv`), and the `.env` file from step 2.

```
uv sync
uv run streamlit run src/app.py
```

Open http://localhost:8501. Code changes apply when you refresh the browser. Stop with Ctrl+C.

Without uv: `pip install -r requirements.txt`, then `streamlit run src/app.py`.

The database (`resources/store.db`) is created automatically on first use.
To reset it, run `uv run python src/setup_db.py`.

## Good to know

- **Port in use:** if the Docker app is running, a local run opens on port 8502 instead.
  Run `docker compose down` first to use 8501.
- **Separate databases:** Docker uses its `store-data` volume and the local run uses
  `resources/store.db`, so orders placed in one don't appear in the other.
- **"GROQ_API_KEY is not set" in the app:** `.env` is missing or the key line is empty.
  With Docker, re-run `docker compose up -d` after fixing `.env`.

## Example questions

- Find me organic honey under $20 with ratings above 4.5
- What do reviewers say about the Manuka honey?
- What is the cheapest dairy-free milk alternative?
- What are the best rated coffees?
- Place an order for product ID 5
- Order the Organic Almonds

## Project layout

| File | Purpose |
|---|---|
| `src/setup_db.py` | Creates `store.db` with products, reviews and an empty orders table |
| `src/reviews_api.py` | Average rating and review count per product |
| `src/products_api.py` | Product search, product details with reviews, order placement |
| `src/agent.py` | LangChain agent: Groq model, tools and system prompt |
| `src/app.py` | Streamlit chat UI with a New chat button and example questions |
| `src/chat_ui.py` | Helpers that render the chat history (messages, tool-call expander) |
| `tests/` | Unit, integration and end-to-end tests (see below) |
| `.github/workflows/ci.yml` | GitHub Actions CI/CD pipeline |

Orders are a prototype: placing one just inserts a row into the `orders` table.

## Updating dependencies

uv is the source of truth (`pyproject.toml` + `uv.lock`). After `uv add` or `uv remove`,
regenerate `requirements.txt` so pip users get the same versions:

```
uv export --format requirements-txt --no-hashes --no-dev -o requirements.txt
```

## Tests

Install the dev tools once with `uv sync` (includes ruff, pytest and Playwright).

| Level | Folder | What it covers | Needs |
|---|---|---|---|
| Unit | `tests/unit/` | Agent tool wrappers, system prompt, chat rendering helpers, all with dependencies mocked | nothing |
| Integration | `tests/integration/` | Database seeding, ratings, product search/details/orders on a real temporary SQLite DB, and the full agent loop with a scripted fake LLM | nothing |
| End-to-end (app) | `tests/e2e/test_app_ui.py` | The real Streamlit app run headlessly: chatting, example buttons, New chat, error handling | nothing |
| End-to-end (browser) | `tests/e2e/test_browser.py` | A real Chromium browser against the running app or container | a running app |
| Live | `tests/e2e/test_live.py` | Real questions to the real Groq model | your Groq key |

Tests never touch `resources/store.db`; they use a throwaway database, and all but the live
tests use a dummy API key, so they're free and give the same result every run.

```
uv run ruff check .                 # lint
uv run ruff format .                # auto-format
uv run pytest                       # unit + integration + app end-to-end (browser/live skip themselves)
```

Browser tests (once: `uv run playwright install chromium`). Start the app, then point the tests at it:

```
docker compose up -d --build
E2E_BASE_URL=http://localhost:8501 uv run pytest -m browser
```

The browser tests expect the app to be running with a **dummy** key (they check that a failed LLM
call is shown gracefully). Against an app with a real key, run the live browser test instead.

Live tests (use a little of your free Groq quota; the key is read from `.env`):

```
RUN_LIVE=1 uv run pytest -m live
```

On Windows PowerShell set variables first, e.g. `$env:RUN_LIVE=1; uv run pytest -m live`.

## CI/CD (GitHub Actions)

The pipeline in `.github/workflows/ci.yml` runs on GitHub's free runners. No server is needed.
`master` is production.

| Event | What runs |
|---|---|
| Pull request into `master` | Lint, format check, unit + integration + app end-to-end tests with coverage, `requirements.txt` sync check, Docker build, container health check, Playwright browser tests against the container |
| Push / merge to `master` | Everything above, plus live tests with the real model, then the production image is published |

The production image is published to GitHub Container Registry:

```
docker pull ghcr.io/kirank0/shopping-agent:latest
docker run -d -p 8501:8501 --env-file .env -v store-data:/app/data ghcr.io/kirank0/shopping-agent:latest
```

Each image is also tagged `sha-<commit>`, so you can roll back to any earlier master commit.

One-time setup on GitHub:

1. **Settings → Secrets and variables → Actions → New repository secret**: `GROQ_API_KEY`. Without it,
   live tests are skipped (with a warning) and everything else still runs. Pull requests never see it.
2. **Settings → Branches → Add branch protection rule** for `master`: require a pull request and
   require the status checks *Lint, unit, integration & app tests* and *Docker build, browser tests & publish*.
3. After the first master run, the image appears under your profile's **Packages**. It is private by
   default; change it in **Package settings** if you want anyone to pull it.
