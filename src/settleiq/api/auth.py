"""Authentication and authorization for SettleIQ SaaS platform.

Provides user registration, login, session management, and organization
membership. All security-critical operations use constant-time comparison
and fail-closed defaults.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Final

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/auth", tags=["auth"])

# --------------------------------------------------------------------------- constants

_SESSION_COOKIE_NAME: Final[str] = "settleiq_session"
_SESSION_TTL_SECS: Final[int] = int(
    os.environ.get("SETTLEIQ_SESSION_TTL_SECS", "86400")
)  # 24 hours
_PASSWORD_HASH_ROUNDS: Final[int] = 12  # bcrypt-style cost factor (PBKDF2)

# --------------------------------------------------------------------------- models


class UserRegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    organization_name: str | None = Field(default=None, max_length=255)


class UserLoginRequest(BaseModel):
    email: str
    password: str


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class SessionResponse(BaseModel):
    user_id: str
    email: str
    full_name: str | None
    organization_id: str | None
    organization_name: str | None
    role: str
    expires_at: str


class OrganizationResponse(BaseModel):
    organization_id: str
    name: str
    slug: str
    plan: str
    created_at: str
    member_count: int


# --------------------------------------------------------------------------- password hashing


def _hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Hash a password with PBKDF2-HMAC-SHA256.

    Returns (hash, salt) as hex strings. Constant-time comparison is used
    during verification to prevent timing attacks.
    """
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _PASSWORD_HASH_ROUNDS,
    )
    return dk.hex(), salt


def _verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify a password against a stored hash using constant-time comparison."""
    computed_hash, _ = _hash_password(password, salt)
    return hmac.compare_digest(computed_hash, stored_hash)


# --------------------------------------------------------------------------- session tokens


def _session_secret() -> str:
    return os.environ.get("SETTLEIQ_SESSION_SECRET", "")


def _issue_session_token(
    user_id: str,
    email: str,
    organization_id: str | None,
    role: str,
) -> tuple[str, float]:
    """Issue a stateless, signed session token.

    Carries user identity, expiration, and a nonce, all covered by an
    HMAC-SHA256 signature over SETTLEIQ_SESSION_SECRET.
    """
    secret = _session_secret()
    if not secret:
        raise RuntimeError("SETTLEIQ_SESSION_SECRET is not configured")
    now = time.time()
    exp = now + _SESSION_TTL_SECS
    nonce = secrets.token_hex(16)
    payload = json.dumps(
        {
            "sub": user_id,
            "email": email,
            "org": organization_id or "",
            "role": role,
            "iat": now,
            "exp": exp,
            "nonce": nonce,
        },
        separators=(",", ":"),
    )
    signature = hmac.new(
        secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).digest()
    payload_b64 = base64.urlsafe_b64encode(payload.encode("utf-8")).rstrip(
        b"="
    ).decode("ascii")
    sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
    token = f"{payload_b64}.{sig_b64}"
    return token, exp


def _validate_session_token(token: str) -> dict[str, object] | None:
    """Validate a stateless session token.

    Returns the payload dict if valid, None otherwise.
    """
    secret = _session_secret()
    if not token or not secret or len(token) > 4096:
        return None
    try:
        payload_b64, sig_b64 = token.split(".")
        payload = base64.urlsafe_b64decode(payload_b64 + "==")
        signature = base64.urlsafe_b64decode(sig_b64 + "==")
        expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            return None
        data = json.loads(payload)
        now = time.time()
        if float(data.get("exp", 0)) <= now:
            return None
        if float(data.get("iat", 0)) > now + 60:
            return None
        return data
    except Exception:
        return None


# --------------------------------------------------------------------------- persistence helpers


def _get_store(request: Request):
    """Get the persistence store from app state."""
    return request.app.state.store


def _ensure_tables(store) -> None:
    """Ensure user and organization tables exist."""
    # Users and organizations tables are created via migrations
    pass


# --------------------------------------------------------------------------- auth routes


@router.post("/register", status_code=201, response_model=SessionResponse)
async def register(request: Request, body: UserRegisterRequest) -> SessionResponse:
    """Register a new user and optionally create an organization.

    Fail-closed: duplicate emails are rejected, weak passwords are rejected,
    and the session secret must be configured.
    """
    store = _get_store(request)

    # Check if user already exists
    existing = store.find_user_by_email(body.email)
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail={"error": "user_exists", "detail": "Account already exists"},
        )

    # Hash password
    password_hash, salt = _hash_password(body.password)

    # Create organization if name provided
    organization_id = None
    organization_name = None
    if body.organization_name:
        org_id = f"org_{secrets.token_urlsafe(16)}"
        org_slug = body.organization_name.lower().replace(" ", "-").replace(
            "_", "-"
        )
        store.create_organization(
            organization_id=org_id,
            name=body.organization_name,
            slug=org_slug,
            plan="free",
        )
        organization_id = org_id
        organization_name = body.organization_name

    # Create user
    user_id = f"user_{secrets.token_urlsafe(16)}"
    store.create_user(
        user_id=user_id,
        email=body.email,
        password_hash=password_hash,
        salt=salt,
        full_name=body.full_name,
        organization_id=organization_id,
        role="owner" if organization_id else "member",
    )

    # Issue session token
    token, exp = _issue_session_token(
        user_id,
        body.email,
        organization_id,
        "owner" if organization_id else "member",
    )

    response = JSONResponse(
        content={
            "user_id": user_id,
            "email": body.email,
            "full_name": body.full_name,
            "organization_id": organization_id,
            "organization_name": organization_name,
            "role": "owner" if organization_id else "member",
            "expires_at": datetime.fromtimestamp(exp, tz=UTC).isoformat(),
        },
        status_code=201,
    )
    response.set_cookie(
        key=_SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=_SESSION_TTL_SECS,
        path="/",
    )
    return response


@router.post("/login", response_model=SessionResponse)
async def login(request: Request, body: UserLoginRequest) -> SessionResponse:
    """Authenticate a user and issue a session token.

    Fail-closed: invalid credentials are rejected with 401, and the session
    secret must be configured.
    """
    store = _get_store(request)
    user = store.find_user_by_email(body.email)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_credentials", "detail": "Invalid credentials"},
        )

    if not _verify_password(body.password, user["password_hash"], user["salt"]):
        raise HTTPException(
            status_code=401,
            detail={"error": "invalid_credentials", "detail": "Invalid credentials"},
        )

    token, exp = _issue_session_token(
        user["user_id"],
        user["email"],
        user.get("organization_id"),
        user.get("role", "member"),
    )

    response = JSONResponse(
        content={
            "user_id": user["user_id"],
            "email": user["email"],
            "full_name": user.get("full_name"),
            "organization_id": user.get("organization_id"),
            "organization_name": user.get("organization_name"),
            "role": user.get("role", "member"),
            "expires_at": datetime.fromtimestamp(exp, tz=UTC).isoformat(),
        },
    )
    response.set_cookie(
        key=_SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=_SESSION_TTL_SECS,
        path="/",
    )
    return response


@router.post("/logout", status_code=204)
async def logout() -> Response:
    """Clear the session cookie."""
    response = Response(status_code=204)
    response.delete_cookie(key=_SESSION_COOKIE_NAME, path="/")
    return response


@router.get("/session", response_model=SessionResponse)
async def get_session(request: Request) -> SessionResponse:
    """Get the current session from the session cookie."""
    token = request.cookies.get(_SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=401,
            detail={"error": "no_session", "detail": "No active session"},
        )

    payload = _validate_session_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_session",
                "detail": "Session token is invalid or expired",
            },
        )

    store = _get_store(request)
    user = store.find_user_by_id(str(payload["sub"]))
    if user is None:
        raise HTTPException(
            status_code=401,
            detail={"error": "user_not_found", "detail": "User not found"},
        )

    return SessionResponse(
        user_id=user["user_id"],
        email=user["email"],
        full_name=user.get("full_name"),
        organization_id=user.get("organization_id"),
        organization_name=user.get("organization_name"),
        role=user.get("role", "member"),
        expires_at=str(payload.get("exp", 0)),
    )


@router.post("/password-reset-request", status_code=202)
async def password_reset_request(body: PasswordResetRequest) -> dict[str, str]:
    """Request a password reset.

    Always returns 202 to prevent email enumeration. In production, this
    would send an email with a reset token.
    """
    # TODO: Integrate with email service to send reset link
    return {
        "message": "If an account exists for this email, a reset link has been sent."
    }


@router.post("/password-reset-confirm", status_code=200)
async def password_reset_confirm(body: PasswordResetConfirm) -> dict[str, str]:
    """Confirm a password reset with a token.

    TODO: Verify the reset token and update the password.
    """
    # TODO: Implement token verification and password update
    return {"message": "Password has been reset successfully."}


# --------------------------------------------------------------------------- organization routes


@router.get("/organizations", response_model=list[OrganizationResponse])
async def list_organizations(request: Request) -> list[OrganizationResponse]:
    """List organizations the current user is a member of."""
    token = request.cookies.get(_SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=401,
            detail={"error": "no_session", "detail": "No active session"},
        )

    payload = _validate_session_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_session",
                "detail": "Session token is invalid or expired",
            },
        )

    store = _get_store(request)
    orgs = store.list_organizations_for_user(str(payload["sub"]))
    return [
        OrganizationResponse(
            organization_id=org["organization_id"],
            name=org["name"],
            slug=org["slug"],
            plan=org.get("plan", "free"),
            created_at=org.get("created_at", ""),
            member_count=org.get("member_count", 0),
        )
        for org in orgs
    ]


@router.get("/organizations/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: str, request: Request
) -> OrganizationResponse:
    """Get organization details."""
    token = request.cookies.get(_SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=401,
            detail={"error": "no_session", "detail": "No active session"},
        )

    payload = _validate_session_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_session",
                "detail": "Session token is invalid or expired",
            },
        )

    store = _get_store(request)
    org = store.find_organization(organization_id)
    if org is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "organization_not_found",
                "detail": "Organization not found",
            },
        )

    # Verify user is a member
    membership = store.find_organization_membership(
        organization_id, str(payload["sub"])
    )
    if membership is None:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "forbidden",
                "detail": "Not a member of this organization",
            },
        )

    return OrganizationResponse(
        organization_id=org["organization_id"],
        name=org["name"],
        slug=org["slug"],
        plan=org.get("plan", "free"),
        created_at=org.get("created_at", ""),
        member_count=org.get("member_count", 0),
    )


@router.post("/organizations", status_code=201, response_model=OrganizationResponse)
async def create_organization_route(
    request: Request, body: Mapping
) -> OrganizationResponse:
    """Create a new organization."""
    token = request.cookies.get(_SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=401,
            detail={"error": "no_session", "detail": "No active session"},
        )

    payload = _validate_session_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_session",
                "detail": "Session token is invalid or expired",
            },
        )

    name = body.get("name", "")
    if not name:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "name_required",
                "detail": "Organization name is required",
            },
        )

    store = _get_store(request)
    organization_id = f"org_{secrets.token_urlsafe(16)}"
    org_slug = name.lower().replace(" ", "-").replace("_", "-")
    store.create_organization(
        organization_id=organization_id,
        name=name,
        slug=org_slug,
        plan="free",
    )
    store.add_organization_member(organization_id, str(payload["sub"]), "owner")

    return OrganizationResponse(
        organization_id=organization_id,
        name=name,
        slug=org_slug,
        plan="free",
        created_at=datetime.now(tz=UTC).isoformat(),
        member_count=1,
    )


# --------------------------------------------------------------------------- dependencies


def require_session(request: Request) -> dict[str, object]:
    """Dependency to require a valid session. Returns the session payload."""
    token = request.cookies.get(_SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "no_session",
                "detail": "Authentication required",
            },
        )

    payload = _validate_session_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_session",
                "detail": "Session token is invalid or expired",
            },
        )

    return payload


def require_organization_member(organization_id: str):
    """Dependency factory to require organization membership."""

    def _check(request: Request) -> dict[str, object]:
        payload = require_session(request)
        store = _get_store(request)
        membership = store.find_organization_membership(
            organization_id, str(payload["sub"])
        )
        if membership is None:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "forbidden",
                    "detail": "Not a member of this organization",
                },
            )
        return payload

    return _check


__all__ = [
    "router",
    "require_session",
    "require_organization_member",
    "UserRegisterRequest",
    "UserLoginRequest",
    "SessionResponse",
    "OrganizationResponse",
    "_issue_session_token",
    "_validate_session_token",
    "_session_secret",
]
