"""
SIH 26090: Application Configuration
Centralized configuration management powered by Pydantic v2 and pydantic-settings.
"""

from typing import List, Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Environment
    APP_ENV: str = Field(default="development", description="Environment mode: development, staging, production")
    APP_NAME: str = Field(default="SIH 26090 Artisan Market Linkage", description="Project application title")
    API_V1_PREFIX: str = Field(default="/api/v1", description="API route version prefix")
    DEBUG: bool = Field(default=True, description="Debug mode flag")
    LOG_LEVEL: str = Field(default="INFO", description="Standard logging level")

    # Security & Tokens
    SECRET_KEY: str = Field(
        default="sih26090-dev-insecure-secret-key-change-in-production-random-64-bytes",
        description="Cryptographic secret key for signing JWTs"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, description="Access token expiration in minutes")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration in days")

    # Database Configuration (PostgreSQL 16+ with pgvector)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/artisan_linkage",
        description="Async database connection URI"
    )
    DATABASE_POOL_SIZE: int = Field(default=10, description="Connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, description="Max overflow connections")
    DATABASE_POOL_RECYCLE_SECONDS: int = Field(default=3600, description="Pool recycle timeout")

    # CORS Whitelist
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Whitelisted origin domains for browser CORS"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        return ["http://localhost:3000"]

    # Storage Configuration (S3-compatible / Cloudflare R2 / MinIO)
    STORAGE_PROVIDER: str = Field(default="minio", description="Storage backend: minio, r2, s3")
    S3_ENDPOINT_URL: Optional[str] = Field(default="http://localhost:9000")
    S3_ACCESS_KEY_ID: Optional[str] = Field(default="minioadmin")
    S3_SECRET_ACCESS_KEY: Optional[str] = Field(default="minioadmin")
    S3_PUBLIC_BUCKET_NAME: str = Field(default="artisan-media-public")
    S3_PRIVATE_BUCKET_NAME: str = Field(default="artisan-documents-private")
    S3_REGION: str = Field(default="us-east-1")
    S3_PUBLIC_CDN_URL: str = Field(default="http://localhost:9000/artisan-media-public")

    # AI Provider Placeholders
    AI_VISION_PROVIDER: str = Field(default="gemini", description="Options: gemini, mock, none")
    AI_VISION_MODEL: str = Field(default="gemini-1.5-flash", description="Vision model identifier")
    AI_VISION_TIMEOUT_SECONDS: int = Field(default=30, description="Timeout for external vision API calls")
    AI_PROMPT_VERSION: str = Field(default="product_vision_v1", description="Default versioned prompt identifier")
    AI_VOICE_PROVIDER: str = Field(default="whisper")
    GEMINI_API_KEY: Optional[str] = Field(default=None)
    BHASHINI_API_KEY: Optional[str] = Field(default=None)
    # AI Embedding & Matching Providers
    AI_EMBEDDING_PROVIDER: str = Field(default="gemini", description="Options: gemini, mock, none")
    AI_EMBEDDING_MODEL: str = Field(default="gemini-embedding-2", description="Active Gemini embedding model")
    EMBEDDING_DIMENSION: int = Field(default=768, description="Target output dimensionality (768)")
    AI_EMBEDDING_TIMEOUT_SECONDS: int = Field(default=30, description="Timeout for external embedding API calls")
    AI_MATCHING_ENGINE_VERSION: str = Field(default="MATCHING_ENGINE_V1", description="Matching engine algorithm version")
    TEXT_EMBEDDING_MODEL: str = Field(default="gemini-embedding-2", description="Backwards compatibility alias")

    # Redis Cache & Rate Limiting
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60)
    MAX_REQUEST_BODY_SIZE_BYTES: int = Field(
        default=15 * 1024 * 1024,
        description="Max allowed request payload size in bytes (15MB)"
    )

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Enforces defensive configuration rules when running in production mode."""
        env = self.APP_ENV.strip().lower()
        if env == "production":
            if self.DEBUG:
                raise ValueError("Production security violation: DEBUG must be False in production environment.")
            if (
                len(self.SECRET_KEY) < 32
                or "insecure" in self.SECRET_KEY.lower()
                or "change-in-production" in self.SECRET_KEY.lower()
                or "random-64-bytes" in self.SECRET_KEY.lower()
            ):
                raise ValueError(
                    "Production security violation: Insecure or default SECRET_KEY detected. "
                    "Provide a cryptographically strong SECRET_KEY (minimum 32 characters)."
                )
            if any("*" in origin for origin in self.CORS_ORIGINS):
                raise ValueError("Production security violation: CORS_ORIGINS cannot contain wildcard '*' in production mode.")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
