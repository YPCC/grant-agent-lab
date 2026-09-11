"""Actor / role identity for guarded calls."""
from __future__ import annotations

import os
from typing import Any

from src.control_plane.profile import current


class IdentityRequired(PermissionError):
    """Production requires GRANT_ACTOR + GRANT_ROLE (or explicit kwargs)."""


def resolve(actor: str | None = None, role: str | None = None) -> dict[str, Any]:
    p = current()
    ident = (actor or os.environ.get("GRANT_ACTOR") or "").strip()
    who = (role or os.environ.get("GRANT_ROLE") or "").strip()
    if p.identity_required:
        if not ident or not who:
            raise IdentityRequired(
                "Production requires identity: set GRANT_ACTOR and GRANT_ROLE "
                "(PI | Navigator | Office of Research Aid | Admin)."
            )
        allowed = {r.lower() for r in p.identity_roles}
        if who.lower() not in allowed:
            raise IdentityRequired(f"Role {who!r} is not in {list(p.identity_roles)}")
    return {"actor": ident or "anonymous", "role": who or "unspecified"}
