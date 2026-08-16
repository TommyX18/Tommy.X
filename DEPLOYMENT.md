# Deploying TOMMY.X for free (GitHub + Render)

**Important to understand first:** GitHub only stores your code — it can't *run* a Django
app with a database. GitHub Pages specifically only serves static HTML/CSS/JS, which is why
you were looking for an `index.html` that doesn't exist here. To get TOMMY.X actually live,
you need:

1. **GitHub** — holds your source code
2. **A Python hosting platform** — actually runs Django, connects to a database, serves
   requests. This guide uses **Render.com**, which has a genuinely free tier for exactly
   this kind of project and deploys directly from your GitHub repo.

---

## Part 1 — Push your code to GitHub

1. Create a new empty repository on GitHub (github.com → New repository). Don't initialize
   it with a README — you already have one. Copy the repo URL it gives you
   (`https://github.com/yourusername/tommyx.git`).

2. In PowerShell, from inside your project folder (the one with `manage.py`):
   ```powershell
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/tommyx.git
   git push -u origin main
   ```
   If `git` isn't recognized, install it from https://git-scm.com/download/win first.

3. Double-check `.env` was **not** pushed (it shouldn't be — it's in `.gitignore`). On
   GitHub, open your repo and confirm you see folders like `core/`, `products/`, `templates/`
   etc., but no `.env` file and no `venv/` folder.

## Part 2 — Deploy to Render (free tier)

1. Go to https://render.com and sign up (you can sign up directly with your GitHub account,
   which makes the next steps easier).

2. Click **New +** → **Blueprint**. Render will ask you to connect your GitHub repo — select
   the `tommyx` repo you just pushed. This project already includes a `render.yaml` file, so
   Render will automatically detect and configure:
   - A free PostgreSQL database
   - A free web service running `gunicorn tommyx_site.wsgi`
   - A generated `SECRET_KEY`
   - `DEBUG=False`
   - `DATABASE_URL` wired automatically from the database to the web service

   Click **Apply** to create both.

3. Wait for the first build to finish (a few minutes) — Render runs `build.sh`, which
   installs dependencies, collects static files, and runs migrations automatically.

4. Once it's live, open the URL Render gives you (something like
   `https://tommyx-web.onrender.com`). You should see the TOMMY.X homepage — with no
   products yet, since the database starts empty.

5. Create your admin account and seed sample data. In the Render dashboard, open your web
   service → **Shell** tab, and run:
   ```
   python manage.py createsuperuser
   python manage.py seed_data
   ```

6. Visit `https://your-app.onrender.com/admin/` to log in and manage products, or just
   browse the storefront at the root URL.

### If you'd rather configure it manually instead of using the Blueprint

- **New +** → **Web Service** → connect your repo
- Build command: `./build.sh`
- Start command: `gunicorn tommyx_site.wsgi`
- Add a **PostgreSQL** database separately (**New +** → **PostgreSQL**, free plan), then
  copy its **Internal Database URL** into the web service's environment variables as
  `DATABASE_URL`
- Add environment variable `SECRET_KEY` (any long random string) and `DEBUG=False`

## Known limitation: free-tier storage is not persistent

Render's **free** web service plan does not include a persistent disk. That means:

- Anything in your `media/` folder (uploaded/seeded product photos) will be **wiped every
  time the service redeploys or restarts** — but your PostgreSQL database (products,
  orders, users) is separate and persists fine.
- This is fine for a demo/portfolio project, but for anything real you'll want either:
  - Render's **paid** persistent disk add-on, or
  - Free image hosting like **Cloudinary** (has a generous free tier) wired in as Django's
    `DEFAULT_FILE_STORAGE` — ask me if you want this set up.

## Free-tier sleep behavior

Render's free web services "spin down" after 15 minutes of no traffic and take ~30-50
seconds to wake back up on the next request. This is normal for the free tier — fine for
sharing a portfolio link, not something you'd want for a real store with paying customers.

## After the first deploy: pushing updates

Any time you make changes locally:
```powershell
git add .
git commit -m "describe your change"
git push
```
Render automatically rebuilds and redeploys on every push to `main` — no extra steps needed.
