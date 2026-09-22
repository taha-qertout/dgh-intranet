# DGH Intranet Portal — Data Model & Permission Matrix

*Originally drafted in Week 1, Day 1 before implementation. The current-state
notes and matrix below record where the finished application differs from that
initial design; they do not erase the original decisions.*

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
| department | FK → Department, nullable | Demo Admin has null (org-wide); the model does not enforce that only Admins may have null |
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
| description | TextField, optional | |
| file | FileField | validated: extension + 10 MB maximum |
| department | FK → Department | scopes visibility |
| category | CharField (choices) | simple, no separate model for MVP |
| uploaded_by | FK → User | |
| uploaded_at | DateTimeField | |
| is_active | BooleanField, default True | portal soft-delete flag; Django Admin hard deletion is disabled |

### Announcement
| Field | Type | Notes |
|---|---|---|
| title | CharField | |
| body | TextField | |
| department | FK → Department, nullable | null = org-wide |
| posted_by | FK → User | |
| published_at | DateTimeField | |
| is_active | BooleanField, default True | portal deletion is soft |

### AuditLog
| Field | Type | Notes |
|---|---|---|
| user | FK → User, nullable | nullable for failed logins by unknown users |
| action | CharField | login success/failure/logout, document upload/download/delete, announcement create/delete |
| username | CharField | snapshot retained if `user` is removed |
| department | FK → Department, nullable | scopes Chef audit view |
| document | FK → Document, nullable | `SET_NULL` on model deletion outside the portal/Admin flows |
| document_title | CharField | title snapshot; also stores announcement titles |
| ip_address | GenericIPAddressField, nullable | |
| timestamp | DateTimeField, auto_now_add | |

**Append-only at the application layer** — `AuditLog.save()` rejects updates,
`AuditLog.delete()` rejects deletion, and Django Admin disables add, change,
and delete for this model. Admin can read the full log in `/admin/`; Chef has
a department-scoped portal view. Raw database access is outside these guards.

## Permission Matrix — Implemented Behavior

Portal actions and Django Admin actions are distinguished where they differ.
Portal deletion sets `is_active=False`. Django Admin denies hard deletion of
Document and Announcement records.

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
| Upload | Any department via Django Admin; no portal upload | Own department through the portal | — |
| View/download | All departments | Own department only | Own department only |
| Delete (soft, portal) | Any active document | Active documents in own department | — |
| Delete (hard, Django Admin) | Disabled | — | — |
| **Announcements** | | | |
| Create | Org-wide through the portal; any department via Django Admin | Own department through the portal | — |
| View | All | Own dept + org-wide | Own dept + org-wide |
| Edit | Django Admin; no portal edit view | No edit view | — |
| Delete (soft, portal) | Any active announcement | Only an active announcement personally posted in own department | — |
| Delete (hard, Django Admin) | Disabled | — | — |
| **Audit Log** | | | |
| View | All entries via Django Admin | Own department's entries through the portal | — |
| **Django Admin panel** | Admin access; AuditLog is read-only | No access | No access |

The original Week 1 design called for Chef announcement deletion to be limited
to the author's own posts and for portal deletes to remain soft. A final
authorization review aligned the implemented delete view and Django Admin
with those rules. The initial design also envisaged Admin document upload
through the portal; the finished portal allows Admin document deletion but
not upload, while Django Admin still permits record creation.

## Enforcement Pattern

Read views require authentication and apply the relevant visibility queryset.
Write and delete views also apply role checks. Announcement deletion adds an
author and own-department check for Chef, while Admin retains access to any
visible active announcement:

```python
# pseudocode — implemented properly in Week 2, Day 1
def can_view_document(user, document):
    if user.role == 'admin':
        return True
    return document.department_id == user.department_id
```

Role check alone is insufficient: it answers "can this kind of user act on
this kind of object," not "can this specific user act on this specific
object." The object-level checks enforce department scope and, for Chef
announcement deletion, ownership.

## Known, Documented Trade-offs

- Admin has cross-department visibility, including other departments' audit
  logs. Deliberate for a small system; no department-siloed super-admin
  split exists. Worth noting in the "known limitations" section of final docs.
- Portal deletes are soft (`is_active=False`), preserving rows and their audit
  relationships. Django Admin denies hard deletion of Document and
  Announcement records.
- Employés have read/download-only access — no upload, no posting — per
  MVP scope in the roadmap.
