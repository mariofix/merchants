# merchants-store

**merchants-store** is a minimal demo storefront bundled with the merchants repository. It shows a complete payment flow — product catalogue → checkout → provider redirect → success/cancel — using flask-merchants and SQLite.

Source: [`store/`](https://github.com/mariofix/merchants/tree/main/store)

---

## Quick start (local)

```bash
git clone https://github.com/mariofix/merchants.git
cd merchants/store

pip install -r requirements.txt

# Optional: copy and edit environment variables
cp .env.example .env

flask --app app run --debug
```

Open [http://localhost:5000](http://localhost:5000) — you'll see the demo catalogue.
The admin panel is at [http://localhost:5000/admin/](http://localhost:5000/admin/).

---

## Docker

```bash
docker run \
  -p 8000:8000 \
  -v merchants_data:/data \
  -e SECRET_KEY=change-me \
  mariofix/merchants-store
```

Open [http://localhost:8000](http://localhost:8000).

The SQLite database is stored in the `/data` volume so it survives container restarts.

### Building locally

```bash
cd store
docker build -t merchants-store .
docker run -p 8000:8000 -v merchants_data:/data -e SECRET_KEY=change-me merchants-store
```

---

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | **yes** | `dev-secret-change-me` | Flask session signing key |
| `DATABASE_URL` | no | `sqlite:////data/store.db` | SQLAlchemy database URL |
| `MERCHANTS_PROVIDER` | no | `dummy` | Provider key to use at checkout |
| `MERCHANTS_WEBHOOK_BASE_URL` | no | — | Public base URL for webhook callbacks |
| `STRIPE_API_KEY` | no | — | Required when `MERCHANTS_PROVIDER=stripe` |
| `KHIPU_RECEIVER_ID` | no | — | Required when `MERCHANTS_PROVIDER=khipu` |
| `KHIPU_SECRET` | no | — | Required when `MERCHANTS_PROVIDER=khipu` |

---

## Swapping the payment provider

By default the store uses `DummyProvider` — no credentials needed, payments always succeed instantly.

To use a real provider, set the relevant env vars:

=== "Stripe"

    ```bash
    docker run -p 8000:8000 -v merchants_data:/data \
      -e SECRET_KEY=change-me \
      -e MERCHANTS_PROVIDER=stripe \
      -e STRIPE_API_KEY=sk_test_... \
      mariofix/merchants-store
    ```

=== "Khipu"

    ```bash
    docker run -p 8000:8000 -v merchants_data:/data \
      -e SECRET_KEY=change-me \
      -e MERCHANTS_PROVIDER=khipu \
      -e KHIPU_RECEIVER_ID=12345 \
      -e KHIPU_SECRET=... \
      mariofix/merchants-store
    ```

    Install the Khipu extra first:

    ```bash
    pip install "merchants-sdk[khipu]"
    ```

---

## What's inside

```
store/
├── app.py            # Flask app factory — routes, models, Flask-Admin
├── templates/
│   ├── base.html     # Shared layout (dark theme)
│   ├── catalog.html  # Product listing
│   ├── checkout.html # Order review + email capture
│   ├── success.html  # Post-payment success
│   └── cancel.html   # Post-payment cancel
├── requirements.txt
├── Dockerfile
└── .env.example
```

The store is intentionally small (~100 lines of Python). It is designed to be read, copied, and adapted — not deployed as-is in production.

---

## Admin panel

Flask-Admin is mounted at `/admin/`. It shows all payment records with search, filter, and bulk actions (refund, cancel, sync from provider).

!!! warning "No authentication"
    The admin panel has no authentication in the demo. Before any public deployment add Flask-Security or similar.
