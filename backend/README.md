# Bcommunity Flask backend

This backend was built after inspecting the Vue frontend. It uses Flask, SQLAlchemy, SQLite, Flask-Migrate/Alembic, Flask-CORS, python-dotenv, Werkzeug password hashing, and expiring signed authentication tokens with server-side session revocation.

## Install and run — Windows PowerShell

From the directory containing the project folder:

```powershell
cd bcommuniy-main\backend
py -m venv venv
.\venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
python app.py
```

If you are already in the project root, use `cd backend` for the first command.

If PowerShell blocks activation, use these commands from the backend directory:

```powershell
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe app.py
```

The virtual environment must first be created with `py -m venv venv`. Activation is optional when calling its executable directly.

Flask listens on http://127.0.0.1:5000. On the first run, a missing backend/.env is created with a cryptographically random SECRET_KEY. The checked-in migrations are applied automatically and create backend/database/app.db. No accounts, passwords, or demo records are preloaded.

To configure manually, copy .env.example to .env and replace SECRET_KEY with the output of:

```powershell
py -c "import secrets; print(secrets.token_hex(32))"
```

Never commit .env, a virtual environment, or the database. The root .gitignore excludes these files. Environment variables override .env values.

## Start the existing frontend

In a second PowerShell window, from the project root:

```powershell
npm ci
npm run dev
```

Open http://127.0.0.1:5173. Register through the Sign In page's "Create an account" button. Public registration always creates a normal account.

Vite proxies /api to http://127.0.0.1:5000. The optional root .env.example documents VITE_API_URL for separate hosting. If changing the frontend origin, update CORS_ORIGINS in backend/.env. If changing Flask's port, also update the Vite proxy target or VITE_API_URL.

For a built frontend, configure its web server to proxy /api to Flask, or set VITE_API_URL before building. Vite's development proxy does not configure a production web server.

## First administrator

From backend, after installation:

```powershell
venv\Scripts\python.exe app.py create-admin
```

Enter an email, display name, and password at the prompts. Password entry is hidden. Alternatively, set ADMIN_EMAIL, ADMIN_NAME, and ADMIN_PASSWORD in backend/.env before running the command. There are no default administrator credentials. Existing emails are rejected rather than silently promoted.

Admin access and profile roles are separate: Admin/User controls permissions; Beginner/Senior/Teacher is the community profile role. The last active administrator cannot be deleted, deactivated, or demoted.

## API contract

Successful responses have a data property. Lists also have meta: page, perPage, total. Use ?page=1&per_page=100; page size is capped at 100. The frontend list helper follows subsequent pages.

Errors have the form:

```json
{"error":{"message":"Authentication required.","status":401}}
```

POST /api/auth/register requires name, email, password. POST /api/auth/login requires email, password. Both return data.user, data.token, and data.expiresIn.

Send authenticated requests with Authorization: Bearer <token>. The frontend keeps the token in sessionStorage and restores the current user with /api/auth/me. Tokens expire after TOKEN_MAX_AGE seconds (default 86400). Logout invalidates that session. Password changes invalidate all sessions. Deactivated or deleted accounts cannot authenticate.

Validation rejects unexpected fields, invalid types, invalid email addresses, unsafe URL schemes, oversized input, invalid parent comments, invalid task statuses, and invalid image data. Passwords must contain 8–128 characters. Use application/json for request bodies. Codes include 400 validation, 401 authentication, 403 authorization, 404 missing resource, 409 conflict, 413 payload limit, and 415 content type.

### Endpoint summary

All paths below start with /api.

| Feature | Routes and methods | Access |
| --- | --- | --- |
| Health | GET /health | Public |
| Authentication | POST /auth/register, POST /auth/login, GET /auth/me, POST /auth/logout | Register/login public; others authenticated |
| Users | GET/POST /users; GET/PUT/DELETE /users/<id> | Collection admin; detail authenticated; changes owner or admin; account roles/status admin |
| Profile | GET/PUT /profile | Current user |
| Directory | GET /members, GET /mentors, GET /leaderboard | Public profiles; emails excluded |
| Posts | GET/POST /posts; GET/PUT/DELETE /posts/<id> | Reads public; create authenticated; changes owner/admin |
| Q&A | GET/POST /questions; GET/PUT/DELETE /questions/<id> | Same ownership as posts |
| Reviews | GET/POST /reviews; GET/PUT/DELETE /reviews/<id> | Same ownership as posts |
| Post reactions | POST/DELETE /posts/<id>/like | Authenticated; idempotent |
| Comments | GET/POST /posts/<id>/comments; GET/PUT/DELETE /comments/<id> | Reads public; writes authenticated; changes author/admin |
| Accepted answer | POST /posts/<id>/solve with commentId | Question author/admin; answer must belong to the question |
| Conversations | GET/POST /conversations; GET/DELETE /conversations/<id> | Participants only; creation takes participantId |
| Messages | GET/POST /conversations/<id>/messages; PUT/DELETE /messages/<id> | Participants; edit/delete sender only |
| Read messages | PUT /conversations/<id>/read | Participants |
| Tasks | GET/POST /tasks; GET/PUT/DELETE /tasks/<id> | Authenticated shared task board; creator/admin edits; assignee can change status |
| Articles | GET/POST /articles; GET/PUT/DELETE /articles/<id> | Reads public; author/admin changes |
| Article reactions | POST/DELETE /articles/<id>/like | Authenticated; idempotent |
| Jobs | GET/POST /jobs; GET/PUT/DELETE /jobs/<id> | Reads public; writes admin |
| Events | GET/POST /events; GET/PUT/DELETE /events/<id> | Reads public; writes admin |
| Notifications | GET /notifications; PUT /notifications/read; PUT/DELETE /notifications/<id> | Current recipient only |

The exact route inventory, including every method/path pair, is in [API_ENDPOINTS.md](API_ENDPOINTS.md).

Post lists support tag, author_id, and q filters. Articles/jobs/events support q title search. Mentors are Senior or Teacher profiles; the skill query filters their skills. Leaderboard uses stored reputation. No reputation scoring formula was invented.

Q&A and reviews are views of the posts table. Questions set isQuestion and #Q&A; review requests use #Review. Answer comments, likes, and permissions use /posts routes for these same IDs. Reviews with comments appear in the frontend's Completed tab. Accepting an answer sets isSolved and isBestAnswer.

Post creation accepts content, title, tag, tags, codeSnippet, codeLanguage, image, projectUrl, isQuestion. It requires content, code, or an image. Inline PNG/JPEG/GIF/WebP images are validated and limited to 5 MB; SVG data URLs are rejected. JSON requests are limited to 8 MB.

Comments accept text, parentId, codeSnippet, codeLanguage; text or code is required. Reply parents must be in the same post. Deleting a comment removes descendant replies.

Messages accept text and optional attachment metadata containing only name and size, matching the original chat sample. Metadata is not a binary file upload. Messages use "me" for senderId when serialized for their sender. Chat refreshes every five seconds. Deleting a conversation removes its messages for both participants.

Tasks accept title, description, assigneeId, status. Status is todo, in-progress, or done. Members are real user profiles; projects.js did not define project records, so no project fields were invented.

Articles accept title, excerpt, content, coverImage, readTime, tags. Jobs accept title, company, location, type, salary, logo, description, tags. Events accept title, date, time, location, type, coverImage, description, attendeesCount, speakers, price. Event date/time remain display strings, matching the existing store rather than guessing a timezone.

Notifications are generated for post likes, comments/replies, and messages. Clients cannot create arbitrary notifications for other users.

## Database and migrations

Default database: backend/database/app.db. Its path is absolute and does not depend on the working directory.

Tables: users, auth_sessions, posts, comments, post_likes, conversations, conversation_members, messages, tasks, articles, article_likes, jobs, events, notifications, and Alembic's alembic_version. Foreign keys and deletion rules are enforced in SQLite. Posts/comments/articles serialize their current author profile instead of storing stale copies.

From backend, explicit schema setup and future migration commands are:

```powershell
venv\Scripts\python.exe -m flask --app app:create_app db upgrade
venv\Scripts\python.exe -m flask --app app:create_app db migrate -m "Describe schema change"
venv\Scripts\python.exe -m flask --app app:create_app db upgrade
```

Review generated migrations before applying them. The migration repository is already included; do not run db init again. [Flask-Migrate documents this migration workflow](https://flask-migrate.readthedocs.io/en/latest/index.html).

For PostgreSQL install psycopg[binary] and set DATABASE_URL=postgresql+psycopg://user:password@host/database. For MySQL install pymysql and set DATABASE_URL=mysql+pymysql://user:password@host/database. Run db upgrade on the new database. Changing the URL does not copy existing SQLite records.

For a Windows WSGI server, from backend:

```powershell
venv\Scripts\python.exe -m flask --app app:create_app db upgrade
venv\Scripts\waitress-serve.exe --listen=127.0.0.1:5000 --call app:create_app
```

## Tests

From the project root:

```powershell
backend\venv\Scripts\python.exe -m pytest backend/tests -q
npm run build
npm audit
```

With Flask and Vite running, also run:

```powershell
node backend/tests/frontend-smoke.mjs
```

The Python suite tests every declared API method/path pair, authentication, ownership, privacy, validation, CORS, database migrations, token expiration, session revocation, and the exact create-admin command. Tests use isolated databases. The live frontend smoke test exercises the actual Pinia stores through Vite's proxy and removes its temporary accounts and related data.

## Frontend scope and verification

Existing frontend files and layouts remain in place. Mock login and in-memory mutations were replaced with API calls. Q&A, knowledge, code review, mentoring, and leaderboard screens are connected and reachable through the navigation. Registration and a new conversation member picker are available. Admin-created passwords are now submitted rather than discarded. Success notifications wait for API success, and private cached data is cleared on session changes. Rendered comment text and code fallback are escaped.

The original task and opportunity stores have API-backed actions; the original project had no routed task/job/event screens. Static profile portfolio links, decorative badges, follower counters, and inert attachment buttons remain frontend prototype content. The backend does not invent follow graphs, SMS delivery, binary attachment storage, mentor ratings, availability scheduling, or a reputation scoring policy.

Verified on this workspace: Python tests, frontend production build, SQLite creation/migrations, and the live Pinia/Vite/Flask workflow. Browser interaction could not be checked because the browser tool's environment handshake fails. A non-fatal Vite warning about the existing large syntax-highlighting bundle remains. No Python/API failures remain.
