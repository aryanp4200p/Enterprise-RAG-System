"""Role based access control: which document departments each role may read."""

DEPARTMENTS = ["finance", "hr", "engineering", "stock_market"]

ROLE_PERMISSIONS = {
    "finance": ["finance"],
    "hr": ["hr"],
    "engineering": ["engineering"],
    "stock_market": ["stock_market"],
    # Executives can read every department.
    "executive": ["finance", "hr", "engineering", "stock_market", "general"],
}


class UnknownRoleError(ValueError):
    """Raised when a role is not defined in ROLE_PERMISSIONS."""


def list_roles():
    return list(ROLE_PERMISSIONS)


def normalize_role(role):
    return (role or "").strip().lower()


def allowed_departments(user_role):
    """Departments the role may read. Raises UnknownRoleError for unknown roles
    so a typo can never silently turn into 'no filter' or 'empty filter'."""
    role = normalize_role(user_role)
    if role not in ROLE_PERMISSIONS:
        raise UnknownRoleError(f"Unknown role: {user_role!r}")
    return list(ROLE_PERMISSIONS[role])


def has_access(user_role, document_department):
    try:
        return document_department in allowed_departments(user_role)
    except UnknownRoleError:
        return False
