# Shopping Agent

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

Orders are a prototype: placing one just inserts a row into the `orders` table.

## Updating dependencies

uv is the source of truth (`pyproject.toml` + `uv.lock`). After `uv add` or `uv remove`,
regenerate `requirements.txt` so pip users get the same versions:

```
uv export --format requirements-txt --no-hashes --no-dev -o requirements.txt
```
