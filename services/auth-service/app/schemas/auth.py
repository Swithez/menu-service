import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ── Permissions ───────────────────────────────────────────────────────────────

class PermissionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    code: str
    description: str
    group: str


# ── Roles ─────────────────────────────────────────────────────────────────────

class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    permission_codes: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def name_strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Role name must not be blank")
        return v


class RoleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None

    @model_validator(mode="after")
    def at_least_one(self) -> "RoleUpdate":
        if self.name is None and self.description is None:
            raise ValueError("At least one field required")
        return self


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    description: str | None
    is_system: bool
    created_at: datetime
    permission_count: int = 0


class RoleDetailResponse(RoleResponse):
    permissions: list[PermissionSchema] = []


# ── Users ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    role_id: uuid.UUID | None = None
    is_active: bool = True

    @field_validator("full_name")
    @classmethod
    def name_strip(cls, v: str) -> str:
        return v.strip()


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    role_id: uuid.UUID | None = None
    is_active: bool | None = None
    password: str | None = Field(None, min_length=6, max_length=128)

    @model_validator(mode="after")
    def at_least_one(self) -> "UserUpdate":
        if all(v is None for v in self.model_dump().values()):
            raise ValueError("At least one field required")
        return self


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str
    full_name: str
    role_id: uuid.UUID | None
    role_name: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
