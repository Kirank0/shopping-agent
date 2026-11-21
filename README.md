# Shopping Agent

An AI shopping assistant for a small natural-foods store. Ask it questions in plain English,
and it searches products, summarizes reviews and places orders.

Built with LangChain, Streamlit, GPT OSS 120B on Groq Cloud, and uv.

## Setup

1. Install [uv](https://docs.astral.sh/uv/) (or run `pip install uv`).
2. Install dependencies:
   ```
   uv sync
   ```
   Without uv, use pip instead: `pip install -r requirements.txt`
   (then run the app with `streamlit run src/app.py`).
3. Get an API key from https://console.groq.com/keys, then copy `.env.example` to `.env`
   and paste the key in:
   ```
   GROQ_API_KEY=gsk_...
   ```

## Run

```
uv run streamlit run src/app.py
```

The database (`resources/store.db`) is created automatically on first run.
To reset it, run `uv run python src/setup_db.py`.

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
