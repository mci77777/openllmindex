"""Pydantic models for llmindex data structures."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Product(BaseModel):
    """A single product entry for the products.jsonl feed."""

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    url: str  # validated as URI in serialization
    image_url: Optional[str] = None
    price: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, pattern=r"^[A-Z]{3}$")
    price_range: Optional[PriceRange] = None
    availability: str = Field(pattern=r"^(in_stock|out_of_stock|preorder)$")
    brand: Optional[str] = None
    category: Optional[str] = None
    updated_at: str  # ISO 8601

    @field_validator("availability", mode="before")
    @classmethod
    def normalize_availability(cls, v: str) -> str:
        mapping = {
            "in stock": "in_stock",
            "out of stock": "out_of_stock",
            "pre-order": "preorder",
            "pre order": "preorder",
        }
        return mapping.get(v.lower().strip(), v.strip())


class PriceRange(BaseModel):
    min: float = Field(ge=0)
    max: float = Field(ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")


# Rebuild Product now that PriceRange is defined
Product.model_rebuild()


class Entity(BaseModel):
    name: str = Field(min_length=1)
    canonical_url: str  # HTTPS URL


class Endpoints(BaseModel):
    products: str
    policies: str
    faq: str
    about: str


class Feeds(BaseModel):
    products_jsonl: Optional[str] = None
    offers_json: Optional[str] = None


class Verify(BaseModel):
    method: str = Field(pattern=r"^(dns_txt|http_file)$")
    value: str = Field(min_length=1)


class Sig(BaseModel):
    alg: str
    kid: str
    jws: str


class LLMIndexManifest(BaseModel):
    """The top-level /.well-known/llmindex.json manifest."""

    version: str = "0.1"
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    entity: Entity
    language: str = Field(pattern=r"^[a-z]{2,3}(-[A-Z][a-zA-Z]{1,7})?$")
    topics: list[str] = Field(min_length=1)
    endpoints: Endpoints
    feeds: Optional[Feeds] = None
    verify: Optional[Verify] = None
    sig: Optional[Sig] = None
    license: Optional[str] = None


class SiteConfig(BaseModel):
    """Configuration for generating llmindex artifacts from CLI."""

    name: str = Field(min_length=1)
    canonical_url: str
    language: str = "en"
    topics: list[str] = Field(default_factory=lambda: ["general"])
    base_url: Optional[str] = None  # base URL for endpoint paths, defaults to canonical_url

    def get_base_url(self) -> str:
        return (self.base_url or self.canonical_url).rstrip("/")
