# DGH Intranet Portal — Data Model & Permission Matrix

*Design doc — Week 1, Day 1. Written before any code, per project roadmap.*

## Role Model

Roles are implemented as an explicit `role` CharField on a custom `User` model
(not Django Groups alone), for readability in application code. Admins are
additionally flagged `is_staff=True, is_superuser=True` to gain Django admin
panel access — Groups/Permissions are not used for department-scoped checks,
since Django's built-in permission system is model-level only, not
object-level. Department scoping is enforced with custom logic in views.

## Data Model

### User (custom, extends AbstractUser)
| Field | Type | Notes |
|---|---|---|
| department | FK → Department, nullable | null only for Admins (org-wide) |
| role | CharField, choices: `admin`, `chef`, `employe` | drives permission checks |

### Department
| Field | Type |
|---|---|
| name | CharField |
| code | CharField, unique |

### Document
| Field | Type | Notes |
|---|---|---|
| title | CharField | |
| file | FileField | validated: type + size |
| department | FK → Department | scopes visibility |
| category | CharField (choices) | simple, no separate model for MVP |
| uploaded_by | FK → User | |
| created_at | DateTimeField | |
| is_active | BooleanField, default True | soft-delete only — never hard delete |

### Announcement
| Field | Type | Notes |
|---|---|---|
| title | CharField | |
| content | TextField | |
| department | FK → Department, nullable | null = org-wide |
| posted_by | FK → User | |
| created_at | DateTimeField | |

### AuditLog
| Field | Type | Notes |
|---|---|---|
| user | FK → User, nullable | nullable for failed logins by unknown users |
| action | CharField, choices: `LOGIN`, `LOGIN_FAILED`, `DOCUMENT_UPLOAD`, `DOCUMENT_DOWNLOAD`, `DOCUMENT_DELETE`, `PERMISSION_CHANGE`, `ANNOUNCEMENT_POST` | |
| target_model | CharField | e.g. `"Document"` |
| target_id | IntegerField, nullable | |
| timestamp | DateTimeField, auto_now_add | |
| details | TextField, optional | freeform context |

**Append-only at the application layer** — no UI path allows editing or
deleting AuditLog entries, for any role, including Admin. (Django superusers
retain raw `/admin/` access as a known, documented trade-off — not hidden
from evaluators.)

## Permission Matrix

| Action | Admin | Chef de Département | Employé |
|---|---|---|---|
| **Users** | | | |
| View users | All | — | — |
| Create/edit/deactivate users | All | — | — |
| Assign roles/departments | Yes | — | — |
| **Departments** | | | |
| Create/edit departments | Yes | — | — |
| View department list | All | Own only (implicit) | Own only (implicit) |
| **Documents** | | | |
| Upload | Any department | Own department only | — |
| View/download | All departments | Own department only | Own department only |
| Delete (soft) | Any | Own department only | — |
| **Announcements** | | | |
| Create | Org-wide or any dept | Own department only | — |
| View | All | Own dept + org-wide | Own dept + org-wide |
| Edit/delete own post | Yes | Yes (own posts only) | — |
| **Audit Log** | | | |
| View | All entries | Own department's entries only | — |
| **Django Admin panel** | Full access | No access | No access |

## Enforcement Pattern

Every view touching Documents / Announcements / AuditLog applies two checks,
not one — a role check, then a department-scope check:

```python
# pseudocode — implemented properly in Week 2, Day 1
def can_view_document(user, document):
    if user.role == 'admin':
        return True
    return document.department_id == user.department_id
```

Role check alone is insufficient: it answers "can this kind of user act on
this kind of object," not "can this specific user act on this specific
object." The second check is the one most likely to have subtle bugs and
gets a dedicated design/review pass in Week 2.

## Known, Documented Trade-offs

- Admin has cross-department visibility, including other departments' audit
  logs. Deliberate for a small system; no department-siloed super-admin
  split exists. Worth noting in the "known limitations" section of final docs.
- Deletes are soft (`is_active=False`) everywhere, to keep audit log
  references intact. No hard-delete path exists in the app UI for any role.
- Employés have read/download-only access — no upload, no posting — per
  MVP scope in the roadmap.
