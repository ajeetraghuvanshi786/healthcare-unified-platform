from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Annotated, cast

from fastapi import Header, HTTPException, Request, status

from healthcare_pipeline.config.settings import Settings
from healthcare_pipeline.identity.models import IdentityScope

_MAX_CONTEXT_LENGTH = 128


@dataclass(frozen=True, slots=True)
class RequestIdentityContext:
    scope: IdentityScope
    actor_id: str


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _required_context_value(value: str | None, label: str) -> str:
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label} context is required",
        )
    normalized = value.strip()
    if not normalized or len(normalized) > _MAX_CONTEXT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {label} context",
        )
    return normalized


def require_request_identity(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_tenant_id: Annotated[str | None, Header()] = None,
    x_identity_domain: Annotated[str | None, Header()] = None,
    x_actor_id: Annotated[str | None, Header()] = None,
) -> RequestIdentityContext:
    settings = cast(Settings, request.app.state.settings)
    expected = settings.require_api_auth_token()
    prefix = "Bearer "

    if authorization is None or not authorization.startswith(prefix):
        raise _unauthorized()
    supplied = authorization[len(prefix) :]
    if not supplied or not secrets.compare_digest(supplied, expected):
        raise _unauthorized()

    tenant_id = _required_context_value(x_tenant_id, "tenant")
    identity_domain = _required_context_value(x_identity_domain, "identity-domain")
    actor_id = _required_context_value(x_actor_id, "actor")

    try:
        scope = IdentityScope(tenant_id, identity_domain)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid identity scope",
        ) from exc

    return RequestIdentityContext(scope=scope, actor_id=actor_id)
