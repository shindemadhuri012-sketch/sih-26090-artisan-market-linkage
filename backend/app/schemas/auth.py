"""
SIH 26090: Authentication Schemas
Pydantic v2 schemas for registration, login, token refresh, and OTP challenges.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class UserRegisterRequest(BaseModel):
    phone_number: str = Field(..., description="E.164 formatted mobile phone number, e.g., +919876543210")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    email: Optional[EmailStr] = Field(default=None, description="Optional user email address")
    role: str = Field(default="artisan", description="User role: artisan or buyer")
    preferred_language: str = Field(default="en", description="Language preference code (en, hi, mr, ta, etc.)")

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^\+[1-9]\d{7,14}$", v):
            raise ValueError("Phone number must be in E.164 international format (e.g. +919876543210)")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ["artisan", "buyer"]:
            raise ValueError("Direct registration role must be either 'artisan' or 'buyer'")
        return v


class UserLoginRequest(BaseModel):
    login_identifier: str = Field(..., description="Mobile phone number (+91...) or email address")
    password: str = Field(..., description="Account password")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    role: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Cryptographic refresh token")


class OTPRequestPayload(BaseModel):
    phone_number: str = Field(..., description="E.164 formatted mobile number")

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^\+[1-9]\d{7,14}$", v):
            raise ValueError("Phone number must be in E.164 international format")
        return v


class OTPVerifyPayload(BaseModel):
    phone_number: str = Field(..., description="E.164 formatted mobile number")
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit numeric OTP code")


class UserResponse(BaseModel):
    id: str
    phone_number: str
    email: Optional[str]
    role: str
    preferred_language: str
    is_active: bool
    is_verified: bool
    created_at: str

    model_config = {"from_attributes": True}
