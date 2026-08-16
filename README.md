# TOMMY.X — Men's Fashion E-commerce

A full-stack men's fashion storefront: Django Templates + Bootstrap 5 frontend, Django REST
Framework + JWT API backend, PostgreSQL database. Styled after a clean, minimal
"DUSTED"-style reference (top contact bar, centered logo, uppercase nav, filterable shop
pages, gray hanger-style product cards) — rebranded in TOMMY.X orange/black/white.

- **Brand:** TOMMY.X
- **Email:** tommy.xattire@gmail.com
- **Phone:** 9751999225
- **Navbar (exactly this, nothing else):** Home · Shirts · Pants · TShirts · Accessories · Footwear

---

## 1. Tech stack

| Layer | Choice |
|---|---|
| Backend | Python, Django 6, Django REST Framework |
| Database | PostgreSQL (SQLite fallback for quick local testing) |
| Auth (site) | Django session auth — login/register/profile/addresses |
| Auth (API) | JWT via `djangorestframework-simplejwt` (access + refresh + blacklist-on-logout) |
| Frontend | Django Templates, Bootstrap 5, vanilla JavaScript, Bootstrap Icons |
| Images | Pillow (also used to generate placeholder product photography in the seed command) |

## 2. Project structure

```
tommyx_site/        # Django settings/urls/wsgi/asgi (env-driven config)
core/                # Home page, offers, contact, custom error views (404/403/500)
accounts/            # Register/login/profile/addresses (template-based session auth)
products/            # Category, Size, Color, Product, ProductImage, ProductVariant
cart/                # Session-based cart (works for guests), variant + coupon aware
wishlist/            # DB-backed wishlist — requires login (guests are redirected to login)
orders/              # Checkout, Order/OrderItem, Coupon
payments/            # Payment model (pending/processing/paid/failed/refunded)
api/                 # DRF serializers/views/urls — the full REST API + JWT auth
templates/           # All HTML (base.html has the navbar/footer; 404/403/500 at the root)
static/css/tommyx.css    # Design tokens + all styling
static/js/tommyx.js      # Page loader, scroll reveal, gallery zoom, live search
TOMMYX_API.postman_collection.json   # Import into Postman — see section 8
```

**Note on scope:** `Category` lives inside the `products` app rather than a separate
`categories` app — functionally identical, just fewer files to navigate. Everything else
(models, REST surface, JWT, variants, wishlist-requires-login, coupons, Postman collection)
matches the brief.

## 3. Setup — Mac/Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit .env with your real DB credentials
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_data        # 5 categories, sizes, colors, 22 products w/ variants, 3 coupons
python manage.py runserver
```

Visit http://127.0.0.1:8000/ and http://127.0.0.1:8000/admin/.

## 4. Setup — Windows PowerShell

Run **one line at a time**, from the folder that directly contains `manage.py`:

```powershell
cd C:\path\to\tommyx_site
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_data
python manage.py runserver
```

If `Activate.ps1` is blocked, run PowerShell as Administrator once:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
then reopen a normal PowerShell window and try activating again.

## 5. PostgreSQL setup

1. Create a database and user (example using `psql`):
   ```sql
   CREATE DATABASE tommyx_db;
   CREATE USER tommyx_user WITH PASSWORD 'change-me';
   GRANT ALL PRIVILEGES ON DATABASE tommyx_db TO tommyx_user;
   ```
2. In `.env`, set:
   ```
   DB_ENGINE=postgresql
   DB_NAME=tommyx_db
   DB_USER=tommyx_user
   DB_PASSWORD=change-me
   DB_HOST=localhost
   DB_PORT=5432
   ```
3. Run `python manage.py migrate` — Django will create all tables in PostgreSQL.

**Quick local testing without PostgreSQL:** set `DB_ENGINE=sqlite` in `.env` and Django will
use a local `db.sqlite3` file instead — useful for a fast first run before your Postgres
server is ready. Switch back to `DB_ENGINE=postgresql` for real development/deployment.

## 6. Environment variables (`.env`)

Copy `.env.example` to `.env` and fill in real values. **Never commit `.env`** — it's in
`.gitignore`. Key variables:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django's secret key — generate a long random string for production |
| `DEBUG` | `True` for local dev, `False` in production |
| `ALLOWED_HOSTS` | Comma-separated hostnames allowed to serve the site |
| `DB_ENGINE` | `postgresql` or `sqlite` |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | PostgreSQL credentials |
| `ACCESS_TOKEN_LIFETIME_MIN` / `REFRESH_TOKEN_LIFETIME_DAYS` | JWT token lifetimes |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | Leave blank to keep demo-mode checkout |
| `EMAIL_HOST` / `EMAIL_PORT` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | For real transactional email; leave blank to print emails to the console |
| `BRAND_EMAIL` / `BRAND_PHONE` | Store contact details shown across the site |

## 7. Seed data

```bash
python manage.py seed_data          # add data (skips products that already exist)
python manage.py seed_data --flush  # wipe categories/products/variants first, then reseed
```

Creates: 5 categories (Shirts, Pants, TShirts, Accessories, Footwear), 6 sizes (XS–XXL),
7 colors, 22 products each with realistic size×color variant combinations and randomized
per-variant stock, and 3 sample coupons (`WELCOME10`, `FREESHIP`, `FLAT200`).

Product photos are simple generated placeholders (gray background, hanger silhouette,
product name) — replace them per-product in `/admin/products/product/` with real photography.

## 8. REST API + JWT + Postman

All endpoints are under `/api/`. Full list:

**Auth**
```
POST   /api/auth/register/     — public, returns access + refresh tokens immediately
POST   /api/auth/login/        — returns access + refresh tokens
POST   /api/auth/refresh/      — exchange refresh token for a new access token
POST   /api/auth/logout/       — blacklists the given refresh token
GET    /api/auth/me/           — the authenticated user's own profile (never exposes others')
```

**Catalog (public, read-only)**
```
GET    /api/categories/
GET    /api/categories/<slug>/
GET    /api/categories/<slug>/products/
GET    /api/products/                         — supports ?search=, ?ordering=, pagination
GET    /api/products/?category__slug=shirts&is_featured=true&ordering=price
GET    /api/products/<id>/
```

**Cart** (session-based — works for guests, no login required)
```
GET    /api/cart/
POST   /api/cart/add/                {"variant_id": 1, "quantity": 2}
PATCH  /api/cart/update/<key>/       {"quantity": 3}
DELETE /api/cart/remove/<key>/
```

**Wishlist** (requires login — matches the "guest must log in" rule)
```
GET    /api/wishlist/
POST   /api/wishlist/                {"product_id": 5}
DELETE /api/wishlist/remove/<product_id>/
```

**Addresses** (requires login)
```
GET/POST/PATCH/DELETE   /api/addresses/
```

**Orders & Payments**
```
POST   /api/orders/create/     — places an order from the caller's current cart;
                                  totals/prices/stock are always recalculated server-side,
                                  never trusted from the request body
GET    /api/orders/            — the caller's own orders only
GET    /api/orders/<id>/
GET    /api/payments/<order_number>/
```

### Using the Postman collection

1. Import `TOMMYX_API.postman_collection.json` into Postman.
2. Set the `base_url` collection variable (defaults to `http://127.0.0.1:8000`).
3. Run **Auth → Login** (or **Register**) first — its test script automatically saves
   `access_token` and `refresh_token` as collection variables. Every other request in the
   collection is pre-configured to send `Authorization: Bearer {{access_token}}`.
4. For cart/wishlist/order requests, update the `variant_id` / `product_id` / `cart_key`
   collection variables to match real IDs from your database (or from a `GET /api/products/`
   response).
5. Postman keeps cookies per-domain automatically, so the session-based cart will persist
   across requests as long as you're hitting the same `base_url`.

## 9. Authentication & authorization summary

- **Customers** can browse, search, filter, add to cart (as a guest or logged in), manage
  their own wishlist/addresses/orders — never anyone else's.
- **Staff/admin** manage products, categories, variants, orders, coupons, payments via
  `/admin/` (Django admin) — separate from the customer-facing JWT API.
- DRF `IsAuthenticated` / `IsAuthenticatedOrReadOnly` permission classes are applied per
  view; wishlist, addresses, and order-history endpoints all filter by
  `request.user` so customers can never see another customer's data.
- Passwords are hashed via Django's built-in password hashers — never stored in plaintext.

## 10. Business rules wired in

- **Pan-India delivery**, **online payment only** — checkout simulates a successful Razorpay
  payment and creates a linked `Payment` record (`orders/views.py` → `checkout_view`, and
  `api/views.py` → `CreateOrderView`). Swap in the real Razorpay Orders API + webhook
  signature verification when going live — the `Payment` model already has the fields for it
  (`provider_order_id`, `provider_payment_id`, `provider_signature`).
- **No returns / exchanges** — "All orders are final" is shown on the cart, checkout, and
  product pages. There is no return button anywhere in the app.
- **Stock is tracked per size+color variant**, not per product. Checkout re-validates stock
  inside a database transaction immediately before creating the order (so two people can't
  both buy the last unit), decrements stock on order placement, and restores it if an order
  is cancelled while still `placed`/`confirmed`.
- **Coupons** support either a percentage or a flat amount, a minimum order value, an
  optional expiry window, and a usage limit.

## 11. Replacing placeholder assets

- `static/img/hero-placeholder.jpg` — swap with real brand photography.
- Product photos — replace the generated placeholders per-product in
  `/admin/products/product/` (each product supports multiple images).
- The inline SVG logo mark in `templates/base.html` (`tx-logo-mark`) — swap for your real logo.

## 12. Admin login (seed data)

- Username: `admin`
- Password: `TommyX@2026`

**Change this immediately before deploying anywhere public.**

## 13. Error pages, security, and performance notes

- Custom `404.html` / `403.html` / `500.html` templates at the template root, wired via
  `handler404` / `handler403` / `handler500` in `tommyx_site/urls.py`. These only render in
  production (`DEBUG=False`) — with `DEBUG=True` Django shows its own debug page instead.
- CSRF protection is on for every state-changing view; the base template renders a silent
  `{% csrf_token %}` on every page so the CSRF cookie is always present, even on pages with
  no visible form (e.g. an empty cart).
- `python manage.py check --deploy` will flag HSTS/SSL-redirect/secure-cookie settings —
  those are intentionally off in dev and should be turned on via your production settings
  once you're serving over HTTPS.
- Product/category querysets use `select_related` / `prefetch_related` where it matters
  (product list, product detail, cart, orders) to avoid N+1 queries.
- Pagination, search, and ordering are enabled by default on `/api/products/` via DRF's
  `PageNumberPagination`, `SearchFilter`, and `OrderingFilter`.

## 14. GitHub readiness

`.gitignore` already excludes `venv/`, `__pycache__/`, `*.pyc`, `db.sqlite3`,
`/staticfiles/`, `/media/`, and `.env`. Never commit `.env`, `SECRET_KEY`, database
passwords, or Razorpay/email secrets — only `.env.example` should be committed.
