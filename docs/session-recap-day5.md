# Session Recap — DGH Intranet Portal, Through Day 5
*Paste this whole document into a new chat with Claude to resume exactly
where we left off. Say: "Here's my project context, let's continue" and
attach/paste this file. This supersedes session-recap-day1.md — everything
in that file is either done or restated here.*

---

## Who I am / the situation
- Software Engineering student, first time using Claude and Claude Code.
- Internship project: a Centralized Intranet Portal for the Moroccan
  General Directorate of Hydraulics (DGH) — **this is my Projet de Fin
  d'Année (PFA)**, not a real production deployment. Evaluated by a jury.
  Honest, well-reasoned scope decisions are evaluation material, not
  weaknesses to hide.
- Only 3 weeks total for the internship — timeline is tight.
- Working solo.
- Environment: Windows, PowerShell, Python 3.14.6, VS Code, Git (GitHub),
  Claude Code (terminal-based, native install — see Environment section).
- Brief from supervisor is vague — I'm defining scope myself.
- I want Claude (chat) to act as a **senior mentor**: explain reasoning,
  teach concepts, review my work, push back on scope creep — not just
  produce code.

## How I work with Claude going forward
- **Claude (chat)** = architecture, planning, teaching, code review,
  documentation, design decisions made *before* code gets written.
- **Claude Code** = actual implementation, running tests, file edits, git
  operations — always working from a prompt we've reasoned through in
  chat first, never freelancing on design.
- Workflow per feature: understand → explain concepts → plan → implement
  → test → review → improve → summarize what I learned.
- I approve Claude Code's tool calls individually by default; I use
  "allow all edits during this session" for large multi-file tasks (e.g.
  scaffolding) once I trust the plan, but keep reviewing **git commits
  and pushes individually** even then, since those have lasting/shared
  consequences.
- Effort level in Claude Code: left on **high** (Sonnet 5's default) —
  appropriate for this project. Model: **Sonnet 5** as default; reserve
  switching to **Opus 5** for the one genuinely ambiguous design task
  still ahead — Week 2 Day 1's document permission access-control logic.

---

## Tech stack (final, ADR-0001)
**Django 5.2 LTS + SQLite (dev) → PostgreSQL (prod, later) + server-rendered
Django templates + Bootstrap 5.** No DRF, no separate JS frontend, no i18n
framework.

**Why Django 5.2 specifically (not 6.0/6.1):** Django has two release
tracks — standard releases get only 16 months of support; LTS releases
(5.2, and eventually 7.2) get 3 years, until April 2028 for 5.2. For a PFA
that might outlive the 3-week build, LTS is the defensible choice, not
just "whatever's newest." Confirmed installed: **Django 5.2.17**.

**Why SQLite now, not Postgres (ADR-0002, informal — not yet written as a
file, worth adding to docs/ eventually):** Docker isn't installed on this
machine (confirmed `docker --version` → command not found). SQLite lets
me build without fighting a native Postgres install mid-internship.
`DATABASES` in settings is deliberately field-by-field (`DB_ENGINE`,
`DB_NAME`, etc. via env vars), not a `DATABASE_URL` shortcut, so switching
to Postgres later is a `.env` edit, not a rewrite. No Postgres-specific
features (JSONField advanced queries, full-text search) are needed for
this MVP.

**Why no i18n framework:** UI is French-only, written directly in
templates/labels — no `{% trans %}`, no `.po` files. `LANGUAGE_CODE =
"fr-fr"`, `USE_I18N = False` in `dgh_intranet/settings/base.py`.
**Known gotcha (currently unresolved, see "Immediate next step" below):**
turning off `USE_I18N` also disables Django's own built-in translations
for its default form labels/validator messages — these need manual
French overrides, they don't come for free.

## Roles (RBAC) — confirmed, Option B
Three roles: **Admin**, **Chef de Département**, **Employé**.

**Design decision:** implemented as an explicit `role` CharField on the
custom `User` model (choices: `admin`/`chef`/`employe`), **not** Django's
built-in Groups system. Reasoning: Django's permission system is
model-level only, not object-level — it can't natively express
"can view Documents in *their own* department," so Groups would only
solve half the problem anyway. An explicit field is more readable in
application code than Group-name string matching. Admins are additionally
flagged `is_staff=True, is_superuser=True` for Django admin panel access.
**Django's Groups section still exists in the admin UI (0 groups, unused)
because it ships by default with `django.contrib.auth` — this is expected,
not a bug, and worth being able to explain to a jury if asked.**

## Scope — MVP (in scope)
Authentication, RBAC (3 roles), document management (upload/categorize/
download, permission-scoped), announcements/news feed, audit log, Django
admin for user/role/department management.

## Explicitly out of scope (documented to supervisor)
Workflow/approval engines, **real email/notification integration** (see
Day 5 — password reset uses Django's console email backend in dev
instead, which is *not* extra scope, just a dev-appropriate substitute
for the one part — actual delivery — that's genuinely out of scope),
advanced search/analytics dashboards, mobile-responsive polish beyond
"looks decent."

---

## Data Model & Permission Matrix
**Full detail committed at `docs/permission-matrix.md` in the repo** —
if that file isn't available in a new context, ask Claude to regenerate
it from this summary (the design is also fully described below).

### Models (as currently implemented)
**User** (custom, extends `AbstractUser`, in `accounts` app)
- `department` — FK → `core.Department`, `null=True, blank=True`,
  `on_delete=models.PROTECT`, `related_name="users"`. Nullable because an
  Admin genuinely has no department — enforcing that via a fake
  required value would misrepresent the data. Trade-off: needs an
  app-level validation rule later ("if role != admin, department
  required") — not a DB-level constraint, deliberately deferred, not yet
  built.
- `role` — CharField, choices `admin`/`chef`/`employe`.
- Both fields have French `verbose_name` ("Département", "Rôle").
- `on_delete=PROTECT` is deliberate: Django refuses to delete a
  Department if any User still references it — better a blocked delete
  than orphaned/null-department users silently losing access scope.

**Department** (in `core` app — chosen over `accounts` because Documents
and Announcements will also FK to it later; keeping shared reference data
in `core` avoids cross-app coupling)
- `name` (CharField), `code` (CharField, unique). French
  `verbose_name`/`verbose_name_plural` ("Département"/"Départements").

**Document, Announcement, AuditLog** — designed on paper (see permission
matrix doc) but **not yet implemented in code**. That's Week 2 work.

### Permission Matrix (summary — full table in docs/permission-matrix.md)
- **Admin**: full access everywhere, including cross-department audit
  logs and Django admin panel. Deliberate trust decision for a small
  system — no department-siloed super-admin split. Worth a line in
  "known limitations" later.
- **Chef de Département**: manage (upload/soft-delete/view) documents
  and announcements scoped to their own department only; view their own
  department's audit log only. No Django admin access.
- **Employé**: view/download documents and announcements in their
  department + org-wide announcements. **No upload, no posting** — matches
  roadmap's original scope. No Django admin access.
- **Deletes are soft everywhere** (`is_active=False` flag, not yet
  implemented on Document since Document doesn't exist yet) — keeps audit
  log references intact, no hard-delete path anywhere in the app UI.
- **AuditLog is append-only at the application layer** — no UI path lets
  anyone, including Admin, edit/delete entries (Django superusers retain
  raw `/admin/` access as a documented trade-off, not hidden).
- **Enforcement pattern** (not yet coded, since Document doesn't exist
  yet): every view needs a two-layer check — role check, then a
  department-scope check (`if user.role == 'admin': return True; return
  obj.department_id == user.department_id`). This is Week 2 Day 1's task,
  flagged in the original roadmap as needing careful chat-first design —
  likely the spot to consider switching to Opus 5.

---

## Environment — fully set up and verified (Day 1)
- **Docker**: not installed → confirmed SQLite-first decision above.
- **Python venv**: `C:\dgh_intranet\venv`, created via `python -m venv
  venv`, activated via `.\venv\Scripts\Activate.ps1` (must reactivate
  every new terminal session — this bit me once on Day 2, forgetting to
  activate before `python manage.py runserver` outside Claude Code).
- **Django 5.2.17** installed in the venv.
- **Git**: `git init` done, `.gitignore` created *before* first commit
  (covers `venv/`, `__pycache__/`, `.env`, `db.sqlite3`, `media/`, `.log`,
  `.vscode/`) — verified working via `git status` never showing these
  paths, even after real project content exists.
- **Claude Code**: native install (not npm — npm is deprecated as an
  install method). Installed via `irm https://claude.ai/install.ps1 |
  iex` in PowerShell. Binary at `C:\Users\taha0\.local\bin\claude.exe` —
  **had to be manually added to User PATH** via Environment Variables
  (System Properties → Edit User PATH → New), then terminal fully
  restarted. Authenticated via `claude auth login` — **signed in under a
  friend's account** (`omarskefkef@gmail.com`, Claude Pro subscription —
  Claude Code requires Pro/Max/Team/Enterprise/Console, not the free
  tier). `claude doctor` confirms no installation issues.
- **GitHub remote**: repo created at
  `https://github.com/taha-qertout/dgh-intranet` (private). Local branch
  renamed `master` → `main` to match GitHub's default before first push
  (`git branch -M main`). Remote `origin` configured, tracking set up via
  `git push -u origin main`. **All commits through Day 5 are pushed.**

---

## Day-by-day build log

### Day 1 — Planning (done)
Scope, roles, tech stack, and full roadmap discussed and locked in.
Environment checklist run live (see Environment section above).
Data model + permission matrix designed in chat, written to
`docs/permission-matrix.md`, committed (first real project commit, after
the initial `.gitignore`-only commit).

### Day 2 — Scaffolding (done, committed `14ed8eb`)
Claude Code scaffolded: Django project `dgh_intranet`, apps `accounts`/
`documents`/`audit`/`core`, settings split into `base.py`/`dev.py`/
`prod.py` (not a single `settings.py`), `.env`-based config via
**django-environ** (chosen over python-decouple — no Django-specific
coupling issues, typed casting via `env.bool()`/`env.list()`, has
`env.db()` available if a `DATABASE_URL`-style config is wanted later even
though current setup uses plain field-by-field vars). Custom `User(
AbstractUser)` stub created and `AUTH_USER_MODEL = "accounts.User"` set
in `base.py` **before** the first `makemigrations`/`migrate` ever ran —
avoiding Django's classic "can't swap User model after first migrate"
trap. `requirements.txt` pinned. Dev server verified running (`python
manage.py runserver`, saw the Django rocket page myself in browser).
`.env` (real secret) correctly gitignored; `.env.example` (template)
correctly tracked.

**Reusable lesson (why this ordering matters):** Django's `auth` app
creates FK references to whatever model `AUTH_USER_MODEL` points to, the
first time `migrate` runs. Change `AUTH_USER_MODEL` after that point and
every other app's User FK is now pointing at the wrong table — requires
either painful manual migration surgery or nuking the DB. Setting it
*before* migrate avoids this entirely. Custom User model *fields* can
still be added anytime afterward via normal migrations (that's what Day 3
did) — it's specifically *which model Django considers "the" User model*
that can't change after the fact.

### Day 3 — Department model + User fields (done, committed `f02c492`,
pushed)
Added `Department` model to `core/models.py` and `department`/`role`
fields to `accounts/models.py`'s `User`, per the design above. Registered
both in Django admin with French-labeled `list_display`. Migrations
reviewed (contents shown before applying, not just trusted) — Django
prompted for a one-off migration-time default for `role` since it's
non-nullable with no model default (table was empty, so inert); answered
`"employe"`, confirmed `preserve_default=False` in the migration, meaning
that default lives only in migration history, **not** silently baked into
`models.py` — new users must explicitly set `role` in code. First push to
GitHub happened after this commit.

### Day 4 — Seed script (done, committed — hash not recorded here, check
`git log`, pushed)
Built `core/management/commands/seed_demo_data.py`, a proper Django
management command (not a one-off script) — idempotent (`get_or_create`
pattern, safe to re-run, verified by running it twice: second run created
zero duplicates). Seeds:
- 2 Departments: **Ressources Humaines (RH)**, **Informatique (INFO)**
- 3 demo Users, password **`DemoPass123!`** on all three:
  - `admin_demo` — role=admin, is_staff=True, is_superuser=True,
    department=None
  - `chef_demo` — role=chef, department=RH
  - `employe_demo` — role=employe, department=RH

Manually verified in the actual browser admin panel (`127.0.0.1:8000/
admin/`, logged in as `admin_demo`) — saw "Utilisateurs" and
"Départements" (French labels working), all three demo users listed with
correct `département`/`rôle` columns, both departments listed.
`is_staff` correctly False for chef_demo/employe_demo (they can't access
this admin panel themselves) — matches the permission matrix.

### Day 5 — Auth flows (done, committed `22aedf5`, pushed to
`origin/main`)
Built login, logout, and password reset, all via Django's **built-in**
auth views (no custom auth logic) — `accounts/urls.py` wires up
`LoginView`, `LogoutView`, `PasswordResetView`,
`PasswordResetDoneView`, `PasswordResetConfirmView`,
`PasswordResetCompleteView` using standard Django URL names. Templates
at `accounts/templates/accounts/*.html`, all extending a shared
`templates/base.html` (Bootstrap 5.3.8 via official CDN + SRI hashes,
`lang="fr"`), all UI text in French.

**Password reset uses Django's console email backend**
(`EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"`,
set in `dev.py` only, not `base.py`/`prod.py`) — this is the deliberate
substitute for real SMTP (out of scope), letting the *complete* reset
flow (request → "email" → link → new password) be built and demoed
without real email infrastructure. Production would need a real
transactional email provider (e.g. SendGrid) — documented future
decision, explicitly not this task's job.

**Bug found and fixed during implementation:** `base.html` was initially
created at `dgh_intranet/templates/base.html` per the literal prompt
wording, but the project's `TEMPLATES` `DIRS` setting (from Day 2
scaffolding) resolves to `BASE_DIR / "templates"` where `BASE_DIR` is the
**repo root**, not the inner `dgh_intranet/` package folder. Caused a
`TemplateDoesNotExist` 500 error. Fixed by moving the file to
`templates/base.html` at repo root, matching the existing settings
convention rather than changing settings to match the mistaken path.
Flagged clearly by Claude Code as a deviation from the literal
instruction — good instinct, worth recognizing that pattern when it
happens again.

**Full end-to-end flow verified twice** — once via `curl` (CSRF token
extraction, form POST, following the real reset link, setting a new
password, then logging in with the new password to prove it actually
took effect, confirmed `LOGIN_REDIRECT_URL = "/admin/"` fires correctly)
and once **by me, manually, in a real browser** — which is what surfaced
the issue below that curl-based testing missed.

`admin_demo`'s password was reset back to the documented `DemoPass123!`
after the curl test changed it. A test email
(`admin_demo@dgh-intranet.local`) was left on that account — harmless,
useful for re-testing resets later.

**Known, not-yet-fixed issue (see "Immediate next step" below):** the
password reset **confirm** page (`/accounts/reset/<uid>/set-password/`)
renders Django's built-in `SetPasswordForm` labels and password-validator
help text in **English** ("New password:", "Your password can't be too
similar to your other personal information," etc.) — not from our
templates, but from Django's form class defaults. Since `USE_I18N =
False`, Django's own built-in translations for these strings don't apply
either — they were never going to come for free once i18n was turned
off; they need explicit manual override.

**Separately noted, not a bug, no action needed:** visiting
`/accounts/logout/` directly in a browser (typing the URL / clicking a
plain link) returns `HTTP 405 Method Not Allowed`. This is expected —
Django's `LogoutView` has required POST-only since 5.0/5.1 for CSRF
safety (a GET-able logout link is exploitable by malicious third-party
pages). The fix is a proper `<form method="post">` with a submit button,
which needs a page for a logged-in user to click it from — that page
doesn't exist yet (no dashboard/navbar built). Genuinely Week 2+ work,
not a Day 5 defect.

---

## Immediate next step (pick this up first in the new chat)

Fix the English-label issue on the password reset confirm page. The
prompt is already written and ready to run in Claude Code — paste this
in once the new chat session confirms it has this context:

```
The password reset confirm page is rendering Django's built-in
SetPasswordForm labels and validator messages in English (since
USE_I18N is deliberately off, Django's own translations don't apply).
Override them to French.

In accounts/forms.py (create this file), subclass Django's
SetPasswordForm and PasswordResetForm to override field labels:

- SetPasswordForm: new_password1 label → "Nouveau mot de passe",
  new_password2 label → "Confirmation du nouveau mot de passe"
- Also override help_text on new_password1 to French equivalents of
  Django's default password validator messages (length, similarity,
  common password, not-all-numeric) — write these as a single French
  help_text list, don't try to translate Django's validator classes
  themselves.

Wire these custom forms into accounts/urls.py's
PasswordResetConfirmView (form_class=...) and PasswordResetView
(form_class=... for the request-email form too, check if that one
has any English-default field labels rendering as well — the
password_reset.html screenshot showed correct French, so it may
already be fine, but verify).

Do not change validator behavior (min length, etc.) — only the
displayed label/help text language. Re-test the reset-confirm page
in a browser-equivalent way (curl, checking the HTML for French vs
English strings) and report what you find.
```

**Important:** after Claude Code reports this fixed, don't just trust the
curl-based report — actually reload the password-reset-confirm page in a
real browser yourself and look at it, the way the English-label issue was
caught in the first place. Curl-based testing already missed this once.

## After that — remaining Week 1 roadmap
- **Day 5 leftover**: none beyond the fix above — auth flows are
  otherwise complete.
- **Weekend/buffer**: first unit tests for auth + RBAC (not started yet).
- **Week 1 checkpoint**: review models + permission matrix before Week 2
  — largely already done via this recap and the committed doc, but worth
  a deliberate pause before starting Week 2's Document model work.
- **Week 2 Day 1** (next major task after the fix + buffer): Document
  model + department-scoped permissions — the trickiest access-control
  logic in the whole project, explicitly flagged for careful chat-first
  design. Strong candidate for switching to **Opus 5** given genuine
  ambiguity/judgment involved, per the model-selection reasoning noted
  earlier in this doc.

---

## Where we stopped
Day 5 was fully implemented, tested twice (curl + manual browser), and
committed/pushed. While manually verifying in-browser, I found the
English-label bug described above and got the fix prompt ready — but
have not yet run it, since I need to preserve this session context
before continuing (this chat is an Incognito conversation, no memory
persists). **First message in the next session: paste this whole
document, then run the "Immediate next step" prompt above.**
