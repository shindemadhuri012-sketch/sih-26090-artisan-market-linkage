# SIH 26090: Role-Based & Object-Level Access Control (RBAC)
## Authorization Matrix, Dependency Guards & IDOR Defense Engineering

---

## 1. Role Hierarchy & Principles

The platform enforces zero-trust role-based access control (RBAC) complemented by object-level ownership guards (Insecure Direct Object Reference / IDOR defenses).

### System Roles:
1. `artisan`: Producer entity. Can create and edit own profile, upload craft verification documents, issue draft craft passports, and view own enquiries and orders. Strictly denied access to buyer RFQ pipelines and admin moderation panels.
2. `buyer`: Institutional or retail procurement entity. Can manage procurement preferences, post requirements, and view public/verified artisan catalogues. Strictly denied access to artisan profile modification, verification submission, or administrative controls.
3. `admin`: Platform governance and government nodal officer role. Can inspect all pending KYC and GI verification submissions, review and approve/reject artisan credentials, audit system logs, and inspect platform provenance data.

---

## 2. Granular Permissions Matrix

| Resource / Action | Artisan | Buyer | Admin | Anonymous |
|---|---|---|---|---|
| **User Registration / Login** | Allowed | Allowed | Allowed | Allowed |
| **GET /auth/me** | Own | Own | Own | Denied (401) |
| **GET/POST/PUT /artisans/me** | Own | Denied (403) | View / Audit | Denied (401) |
| **GET /artisans/{id}/public** | Allowed | Allowed | Allowed | Allowed |
| **GET/POST/PUT /buyers/me** | Denied (403) | Own | View / Audit | Denied (401) |
| **POST /passports/** (Issue Draft) | Own | Denied (403) | Denied (403) | Denied (401) |
| **GET /passports/my** | Own | Denied (403) | Denied (403) | Denied (401) |
| **POST /passports/{id}/submit** | Own (IDOR Check) | Denied (403) | Denied (403) | Denied (401) |
| **GET /public/passports/{public_id}** | Allowed | Allowed | Allowed | Allowed |
| **POST /verifications/submit** | Own | Denied (403) | Denied (403) | Denied (401) |
| **GET /verifications/my** | Own | Denied (403) | Denied (403) | Denied (401) |
| **GET /verifications/admin/pending** | Denied (403) | Denied (403) | Allowed | Denied (401) |
| **POST /verifications/admin/{id}/review** | Denied (403) | Denied (403) | Allowed | Denied (401) |

---

## 3. Implementation Guards

### 3.1 Role Guard Dependency Factory: `require_roles`

The `require_roles` dependency factory enforces role constraints before route execution:

```python
# backend/app/core/permissions.py
def require_roles(allowed_roles: List[str]):
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role in {allowed_roles}, your role is '{current_user.role}'."
            )
        return current_user
    return role_checker
```

### 3.2 Object-Level Authorization Guard: `check_object_ownership`

Prevents Insecure Direct Object Reference (IDOR) attacks:
- Ensures an artisan cannot submit, view, or alter resources belonging to another artisan simply by enumerating resource IDs.
- Admins are granted bypass capability for audit and moderation purposes.

```python
# backend/app/core/permissions.py
def check_object_ownership(current_user: User, resource_owner_id: str, resource_name: str = "resource"):
    if current_user.role == "admin":
        return True
    if str(current_user.id) != str(resource_owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: You do not own this {resource_name}."
        )
    return True
```

---

## 4. Inactive & Disabled Account Handling

If a user account is suspended or flagged for fraudulent activity:
- `is_active` flag is set to `False`.
- `get_current_active_user` dependency rejects every request with `403 Forbidden` (`"User account is inactive or disabled."`).
- Active refresh sessions are invalidated immediately in the database.
