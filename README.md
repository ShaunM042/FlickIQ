# FlickIQ

A hybrid movie recommendation system: a FastAPI backend backed by PostgreSQL/pgvector serving collaborative-filtering recommendations trained on the MovieLens 25M dataset and enriched with TMDB metadata, with a React + TypeScript frontend.

## Project Structure

```
backend/
  api/main.py         # FastAPI app (routes, DB queries)
  config/settings.py  # env-based configuration
  data/                # MovieLens loading + TMDB enrichment scripts
  db/                  # schema.sql, pgvector index
  model/               # LightFM training and evaluation
  requirements.txt
frontend/
  src/                 # React app (pages, components, api client)
  vite.config.ts       # dev server + /api proxy to the backend
```

## Prerequisites

- Python 3.11 (required for `psycopg2-binary`/LightFM compatibility)
- Node.js 18+
- PostgreSQL with the `pgvector` extension enabled (Supabase works out of the box)
- A TMDB API key
- The MovieLens 25M dataset (`movies.csv`, `ratings.csv`) placed in `backend/data/movielens/`

## Backend Setup

```bash
cd backend
python3.11 -m venv .venv-3.11
source .venv-3.11/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Create a `.env` file in the repo root (loaded by `backend/config/settings.py`):

```env
DATABASE_URL=postgresql+psycopg://user:password@host:5432/postgres?sslmode=require

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

TMDB_API_KEY=your-api-key
TMDB_ACCESS_TOKEN=your-access-token
TMDB_IMAGE_BASE=https://image.tmdb.org/t/p/w342
POSTER_PLACEHOLDER=https://placehold.co/342x513?text=No+Poster
```

Enable pgvector and load the schema:

```bash
# In psql or the Supabase SQL editor:
CREATE EXTENSION IF NOT EXISTS vector;

# From backend/, with DATABASE_URL set:
python -m data.load_schema
python -m data.load_movielens
python -m data.enrich_tmdb_async
```

Train the recommendation model:

```bash
python model/train_model.py
```

Start the API (from `backend/`):

```bash
uvicorn api.main:app --reload --port 8000
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

This starts Vite on `http://localhost:3000` and proxies `/api` requests to the backend at `http://localhost:8000`. For a production build, set `VITE_API_BASE` to the deployed backend URL and run `npm run build`.

## API Endpoints

- `GET /healthz` - DB health check
- `GET /docs` - interactive API docs
- `GET /movies` - browse movies
- `GET /movies/search?q=` - search movies by title
- `GET /similar/{movie_id}` - item-to-item similarity via pgvector
- `GET /recommendations/{user_id}` - personalized recommendations
- `GET /trending` - popularity-based fallback
- `POST /users` - create/ensure a user exists
- `POST /interactions` - upsert a user-movie interaction
- `GET /interactions/{user_id}` - list a user's interactions
- `DELETE /interactions/{user_id}/{movie_id}` - remove an interaction
- `GET /users/{user_id}/liked` - a user's liked movies

## Useful Scripts

```bash
# From backend/
python -m data.table_counts          # row counts per table
python -m data.peek_table movies     # inspect a table's contents
python model/evaluate_model.py --train --epochs 5 --no_components 64

# From the repo root
python test_connection.py            # verify DB connectivity
```

## Deployment

`Procfile` and `nixpacks.toml` assume the backend directory is the deploy root, running `uvicorn api.main:app --host 0.0.0.0 --port $PORT`. Set the platform's root/working directory to `backend/` and configure the same environment variables listed above.

## Common Issues

- **LightFM/psycopg2 build errors**: use Python 3.11; `psycopg2-binary` avoids source compilation issues.
- **Database connection errors**: confirm the `vector` extension is enabled and `DATABASE_URL` uses the `postgresql+psycopg://` scheme (SQLAlchemy/psycopg format).
- **TMDB rate limits**: use the async enrichment script and its `--limit` flag during development.
