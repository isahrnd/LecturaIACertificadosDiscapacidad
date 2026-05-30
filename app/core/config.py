from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


def _split_csv_env(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _normalize_origin(value: str) -> str:
    return value.rstrip("/")


def _combine_origin_regex(*patterns: str | None) -> Optional[str]:
    cleaned = [pattern.strip() for pattern in patterns if pattern and pattern.strip()]
    if not cleaned:
        return None
    if len(cleaned) == 1:
        return cleaned[0]
    return "|".join(f"(?:{pattern})" for pattern in cleaned)


class Settings(BaseModel):
    app_name: str = "Lectura IA Certificados Discapacidad"
    app_version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = Field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))
    max_file_size_mb: int = Field(
        default_factory=lambda: int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    )
    storage_backend: str = Field(default_factory=lambda: os.getenv("STORAGE_BACKEND", "memory"))
    frontend_url: str = Field(default_factory=lambda: os.getenv("FRONTEND_URL", ""))
    allow_origins: list[str] = Field(
        default_factory=lambda: [
            _normalize_origin(origin)
            for origin in _split_csv_env(
                os.getenv(
                    "ALLOW_ORIGINS",
                    ",".join(
                        [
                            "http://localhost:3000",
                            "http://127.0.0.1:3000",
                            "http://localhost:8080",
                            "http://127.0.0.1:8080",
                            "http://localhost:5173",
                            "http://127.0.0.1:5173",
                        ]
                    ),
                )
            )
        ]
    )
    allow_origin_regex: Optional[str] = Field(
        default_factory=lambda: os.getenv("ALLOW_ORIGIN_REGEX") or None
    )
    request_timeout_seconds: float = Field(
        default_factory=lambda: float(os.getenv("REQUEST_TIMEOUT_SECONDS", "90"))
    )
    analysis_debug: bool = Field(
        default_factory=lambda: os.getenv("ANALYSIS_DEBUG", "false").strip().lower()
        in {"1", "true", "yes", "on"}
    )
    max_pdf_pages_for_vision: int = Field(
        default_factory=lambda: int(os.getenv("MAX_PDF_PAGES_FOR_VISION", "5"))
    )
    pdf_always_include_images_for_openai: bool = Field(
        default_factory=lambda: os.getenv("PDF_ALWAYS_INCLUDE_IMAGES_FOR_OPENAI", "true").strip().lower()
        in {"1", "true", "yes", "on"}
    )
    max_image_dimension: int = Field(
        default_factory=lambda: int(os.getenv("MAX_IMAGE_DIMENSION", "1600"))
    )
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def cors_allow_origins(self) -> list[str]:
        origins = list(self.allow_origins)
        if self.frontend_url:
            origins.append(_normalize_origin(self.frontend_url))
        return list(dict.fromkeys(origins))

    @property
    def cors_allow_origin_regex(self) -> Optional[str]:
        return _combine_origin_regex(
            self.allow_origin_regex,
            r"^https://[a-zA-Z0-9-]+\.vercel\.app$",
            r"^https://([a-zA-Z0-9-]+\.)?almia\.com\.co$",
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
