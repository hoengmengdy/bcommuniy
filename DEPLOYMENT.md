# Bcommunity: authentication, profile photos, and Render deployment

This version uses the existing Vue/Pinia frontend, Flask API, SQLAlchemy models, and signed bearer sessions. Public account creation is disabled. Login contains Email Address, Password, and Sign In only. Existing accounts continue working; administrators can provision users using the existing admin screen or trusted CLI.

## Run locally (Windows PowerShell)

Use Node 22.18+ or Node 24.12+, Python 3.13+, and run these commands from the repository root. Do not recreate the existing virtual environment if it already exists.

```powershell
py -m venv backend/venv
backend/venv/Scripts/python.exe -m pip install -r backend/requirements.txt
npm ci
backend/venv/Scripts/python.exe backend/app.py
```

In a second terminal at the repository root:

```powershell
npm run dev
```

Open http://127.0.0.1:5173 and sign in with an existing account. Backend development storage defaults to `backend/database/app.db`. A missing `backend/.env` is created with a random secret on the first development start. Keep that file to preserve valid sessions between restarts. Migrations run automatically; existing records are retained.

Create the first administrator using the trusted local command (password entry is hidden):

```powershell
backend/venv/Scripts/python.exe backend/app.py create-admin
```

The command prompts for email, display name, and a hidden password. It refuses to overwrite an existing account. Existing Admin > Manage Users functionality remains available.

## Authentication and route protection

The only public authentication page is `/auth` (Login). `/register`, `/signup`, and `/create-account` redirect to Login and cannot create accounts. Only `POST /api/auth/login` accepts public authentication requests. The registration API has been removed. Public `/healthz` returns only `{"status":"ok"}` after checking connectivity.

Protected pages: `/`, `/questions`, `/knowledge`, `/reviews`, `/mentorship`, `/leaderboard`, `/profile`, `/messages`, `/post/:id`, `/admin`, and `/admin/users`. Admin pages also require the Admin account role. All other `/api` routes, including content reads and `/api/health`, require a valid active session by default. Data-free CORS OPTIONS preflights are allowed.

The router verifies the session with the backend before rendering a protected page, including on refresh and direct URL navigation. The frontend stores the bearer token and its fixed expiration time in sessionStorage. Session expiry, logout, and API 401 responses clear protected stores and redirect to Login. Logout revokes the session in the database. Late responses from an old session are discarded. Server revocation is rechecked on navigation, focus, visibility, and every 30 seconds while visible.

Passwords are hashed using Werkzeug scrypt, with existing hashes still supported by password verification. Trusted account provisioning validates name, email, password length (8-128), and duplicate normalized email. Anonymous visitors and ordinary users cannot create accounts through `/api/users`; only administrators can use it. Login has per-IP limits backed by Redis in production. Password hashes and session internals are never returned by APIs. Member directories omit contact information; the owner and administrators retain authorized access.

## Profile photo upload

Go to **Profile > Edit Profile > Upload Photo**, choose a photo, then **Save Changes**. The preview appears before saving. JPEG, PNG, WebP, and GIF files up to 5 MB and 20 megapixels are supported. The backend decodes and re-encodes the first frame as a 256 ? 256 WebP avatar and strips metadata. SVG, corrupt image data, oversized files, and unsafe URL schemes are rejected. The existing `users.avatar` text column stores the resulting data URL, so photos are returned only through authenticated data APIs and persist in PostgreSQL across web-service restarts. No upload directory or extra storage service is required.

## Database models and migrations

No new tables or columns are needed for login protection or photo uploads. Existing models are reused:

| Model/table | Use |
| --- | --- |
| User / users | Existing identity fields, unique email, scrypt password_hash, avatar, and roles |
| AuthSession / auth_sessions | Existing signed-token session IDs and logout revocation |
| All existing content tables | Posts, comments, likes, conversations, messages, tasks, articles, jobs, events, notifications stay intact |

`User.to_dict()` now includes phone numbers only in authorized owner/admin responses. Migration `a08c0deba4d8` adds the previously introduced phone column with an empty default so upgrades from populated older databases preserve users and password hashes. Existing databases already at this migration need no schema change for this release.

## Required environment variables

The checked-in `render.yaml` supplies the production values below, including generated secrets and private datastore connections. Do not commit `.env` files, database files, or real connection strings.

| Variable | Production value / default |
| --- | --- |
| APP_ENV | `production`; development defaults to `development` |
| SECRET_KEY | Required stable random secret of at least 32 characters; Render generates it |
| DATABASE_URL | Required persistent PostgreSQL URL; Render injects the private database connectionString. `postgres://`, `postgresql://`, and `postgresql+psycopg://` are accepted |
| RATELIMIT_STORAGE_URI | Required `redis://` or `rediss://` URL; Render injects the private Key Value connectionString. Development defaults to `memory://` |
| TRUST_PROXY | `1` on Render; `0` when running directly. Trust exactly one Render forwarding proxy |
| HOST | `0.0.0.0` on Render; development `127.0.0.1` |
| PORT | `10000` on Render; production entry defaults to `8080`, development `5000` |
| TOKEN_MAX_AGE | Optional session lifetime in seconds; default `86400` |
| AUTH_LOGIN_LIMIT | Optional; default `10 per minute;100 per hour` |
| WAITRESS_THREADS | Optional; default `4` |
| CORS_ORIGINS | Optional comma-separated allowed origins for separately hosted frontends. Leave unset for the same-origin Render deployment |
| FRONTEND_DIST | Optional absolute path; defaults to the repository's `dist` build |
| FLASK_DEBUG | Development only; default `0`; unused by the production entry |
| ADMIN_EMAIL, ADMIN_NAME, ADMIN_PASSWORD | Optional CLI inputs for first admin provisioning; interactive prompts avoid saving these |
| VITE_API_URL | Optional frontend build-time override; leave unset for `/api` on the same Render service |

`POSTGRES_PASSWORD`, `POSTGRES_USER`, and `POSTGRES_DB` are local Docker Compose inputs, not additional Render variables. Keep SECRET_KEY stable across restarts; rotating it intentionally signs out existing sessions without changing account passwords.

## Production deployment to Render

The deployment is prepared in `render.yaml` and `Dockerfile`. It creates **new resources** named `bcommunity-auth-web`, `bcommunity-auth-db`, and `bcommunity-auth-rate-limits` in Singapore. Rename all three names and their references first if those names already exist in your Render workspace. The web and PostgreSQL plans in the Blueprint are paid; review Render's displayed cost before creating them. Key Value uses the free plan only for disposable rate counters. Accounts, content, photos, and revocation state live in persistent PostgreSQL.

1. Install/connect the Render integration if you want Codex to operate your Render account, or sign in at https://dashboard.render.com yourself. No new hosted URL has been created by this local implementation.
2. Commit and push these changes to a **new branch**, reviewing the files first. From the project root:

   ```powershell
   git switch -c hosted-auth-photos
   git status --short
   git add .
   git diff --cached --stat
   git commit -m "Protect existing-account login, add profile photos, and prepare Render deployment"
   git push -u origin hosted-auth-photos
   ```

   Ignored local secrets, databases, virtual environments, and build output are excluded. Only commit the intended reviewed source changes.
3. In Render, choose **New > Blueprint**, connect `hoengmengdy/bcommuniy` (or your fork), select branch `hosted-auth-photos`, and use the root `render.yaml`.
4. Review the three new resources, region, plans, and generated environment variables, then create the Blueprint. PostgreSQL and Redis have no public IP allowlist entries. The web service builds the Vue site inside the Node stage and serves `dist` and `/api` together using Flask/Waitress. The start command `python -m backend.production` applies the existing Alembic migrations before listening. No seed users, database resets, or password resets run on startup.
5. Wait for the database and web service to be healthy. Open the actual HTTPS URL shown on the web service's Render dashboard. `/healthz` should return only `{"status":"ok"}`. Anonymous `/api/posts` should return `401`.
6. If preserving existing local accounts/content, perform the empty-database import below **before** creating any new accounts. Otherwise create the first administrator from the Render web-service Shell, sign in, and provision users through Admin > Manage Users:

   ```sh
   python -m flask --app backend.app create-admin
   ```

7. Test the checklist below on the actual hosted URL, then use Render's **Restart service** and verify the same account and photo still work. Automatic deployment is off in this Blueprint; for later updates push the branch and select **Manual Deploy > Deploy latest commit**. Keep the existing PostgreSQL service and SECRET_KEY.

The resource and environment-reference syntax follows [Render's Blueprint reference](https://render.com/docs/blueprint-spec); the container is deployed using [Render's Docker workflow](https://render.com/docs/docker). One web instance is configured; coordinate migration execution before introducing concurrent deployments or multiple instances.

### Preserve existing local data on the new hosted version

A fresh Render database starts empty; existing local SQLite data is not automatically uploaded. `backend.transfer_data` copies all existing application tables, IDs, password hashes, avatar images, and relationships in one destination transaction. It refuses a nonempty destination and leaves the source unchanged. PostgreSQL sequences are advanced after copying. A new SECRET_KEY means imported accounts must sign in again with their existing passwords.

Stop local writers and keep the new service's database empty during the transfer. Back up the SQLite database using Python's SQLite backup API (from the repository root):

```powershell
backend/venv/Scripts/python.exe -c "import sqlite3; source=sqlite3.connect('backend/database/app.db'); target=sqlite3.connect('backend/database/pre-hosting-backup.db'); source.backup(target); target.close(); source.close()"
```

Apply the latest local migrations if needed:

```powershell
backend/venv/Scripts/python.exe -m flask --app backend.app db upgrade
```

Temporarily allow **only your current IP** in the Render PostgreSQL access settings and copy its External Database URL privately. The private hostname is for Render services; a local import needs the external hostname. Run in a separate local PowerShell terminal:

```powershell
$env:DATABASE_URL = Read-Host 'Render external PostgreSQL URL'
$env:APP_ENV = 'development'
$sourceDbUrl = 'sqlite:///' + ((Resolve-Path 'backend/database/app.db').Path.Replace('\', '/'))
backend/venv/Scripts/python.exe -m backend.transfer_data --source $sourceDbUrl
Remove-Item Env:DATABASE_URL
Remove-Item Env:APP_ENV
```

Require TLS in the external database URL (`sslmode=require`). Remove the temporary public IP entry after the copy. Resume the web service and verify an existing account can sign in, its photo/content remain, and a newly administrator-provisioned account receives a fresh unique ID. Never publish the backup or connection string. Keep the new database empty until this transfer finishes; the tool deliberately does not merge or overwrite populated databases.

## Optional local production stack with Docker

Requires Docker Desktop/Compose. From the root:

```powershell
Copy-Item .env.production.example .env.production
py -c "import secrets; print(secrets.token_hex(32))"
py -c "import secrets; print(secrets.token_hex(32))"
```

Put the two different generated hex values into `.env.production` as SECRET_KEY and POSTGRES_PASSWORD, then:

```powershell
docker compose --env-file .env.production up --build -d
docker compose --env-file .env.production logs -f web
```

Open http://127.0.0.1:8080. PostgreSQL 18 uses the named `postgres-data` volume, mounted at `/var/lib/postgresql`; web container restarts do not delete it. Redis stores only rate counters. For a restart:

```powershell
docker compose --env-file .env.production restart web
```

To stop the stack while retaining the database:

```powershell
docker compose --env-file .env.production down
```

## Verification

Run from the root after dependencies are installed:

```powershell
backend/venv/Scripts/python.exe -m pytest backend/tests -q
npm run test:auth
npm run test:auth:browser
npm run test:auth:production
```

The browser tests use isolated temporary databases and accounts, not existing user records. They require installed Chrome; alternatively install Playwright Chromium (`npx playwright install chromium`) and set PLAYWRIGHT_CHANNEL=chromium. Tests cover all protected direct URLs, blocked signup links, signup URLs and registration API requests, existing-account login, ordinary/admin access, photo selection and persistence on refresh, immediate logout, revoked tokens, browser Back, invalid login, expiry, and server revocation. The feature smoke also covers posts, comments, likes, accepted answers, chat, tasks, articles, jobs/events, notifications, and existing administrator provisioning.

Backend checks also cover image decoding and size limits, API protection, contact-data visibility, rate limiting, migrations with existing users, data transfer, and account/session/photo persistence across application recreation. PostgreSQL migration SQL is checked offline. Docker/PostgreSQL runtime and a live Render deployment still need verification in the hosting environment; Docker and PostgreSQL executables are unavailable on this machine.

Hosted manual checklist:

1. In a private browser window, open `/profile` or `/questions` directly: Login appears and no content is shown.
2. Confirm Login has no Create account/Register/Sign up option. Open `/register`, `/signup`, or `/create-account`: Login appears. `POST /api/auth/register` cannot create users.
3. An unknown account cannot sign in. Administrators can provision accounts through Admin > Manage Users; anonymous and ordinary users cannot use that API.
4. Sign in: the requested protected page opens. Refresh and navigate normally.
5. Profile > Edit Profile > Upload Photo > Save Changes: the circular photo updates. Refresh and restart the web service; account and photo persist.
6. Sign Out: protected content disappears immediately. Browser Back and direct protected URLs require Login again; the old bearer token returns 401.
7. An ordinary account cannot enter `/admin/users`. Existing administrator features still work.

## Files involved

| Area | Files |
| --- | --- |
| Login and shared design | `src/views/AuthView.vue`, `src/assets/auth.css`, `src/router/index.js`, `src/services/api.js`; obsolete `src/views/RegisterView.vue` removed |
| Photo upload and profile refresh | `src/components/EditProfileModal.vue`, `src/views/community/ProfileView.vue`, `src/stores/posts.js` |
| API authentication, rate limiting, configuration | `backend/app.py`, `backend/config.py`, `backend/extensions.py`, `backend/routes/auth.py`, `backend/services/auth.py`, `backend/requirements.txt` |
| Profile validation and private serialization | `backend/routes/users.py`, `backend/services/images.py`, `backend/models/__init__.py` |
| Hosting and persistence | `backend/production.py`, `backend/transfer_data.py`, `Dockerfile`, `.dockerignore`, `compose.yaml`, `render.yaml`, `.env.production.example`, `backend/.env.example`, `.gitignore`, phone-column migration |
| Verification and documentation | `backend/tests/test_api.py`, `backend/tests/test_auth_access.py`, `backend/tests/test_production_uploads.py`, `backend/tests/conftest.py`, `backend/tests/frontend-auth.test.mjs`, `backend/tests/auth-browser-smoke.mjs`, `backend/tests/frontend-smoke.mjs`, `package.json`, `backend/README.md`, `backend/API_ENDPOINTS.md`, this guide |
