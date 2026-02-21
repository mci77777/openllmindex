"""Generate /llm Markdown pages: products, policies, faq, about."""

from __future__ import annotations

from pathlib import Path

from cli.llmindex_cli.models import Product, SiteConfig


def generate_products_page(products: list[Product], config: SiteConfig) -> str:
    """Generate products.md with grouped product listing."""
    lines = [f"# {config.name} — Products\n"]

    # Group by category
    categories: dict[str, list[Product]] = {}
    for p in products:
        cat = p.category or "Other"
        categories.setdefault(cat, []).append(p)

    for cat in sorted(categories):
        lines.append(f"\n## {cat}\n")
        for p in categories[cat]:
            avail = "In Stock" if p.availability == "in_stock" else (
                "Pre-order" if p.availability == "preorder" else "Out of Stock"
            )
            price_str = f"{p.currency} {p.price:.2f}" if p.price is not None and p.currency else "Price on request"
            lines.append(f"- **[{p.title}]({p.url})** — {price_str} ({avail})")

    return "\n".join(lines) + "\n"


def generate_policies_page(config: SiteConfig) -> str:
    """Generate policies.md template."""
    return f"""# {config.name} — Policies

## Shipping Policy

We ship to all domestic addresses. International shipping is available for select regions.

- **Standard shipping**: 5–7 business days
- **Express shipping**: 2–3 business days
- **Free shipping**: On orders over $50

## Return Policy

We accept returns within 30 days of purchase. Items must be unused and in original packaging.

- Refunds are processed within 5–10 business days
- Return shipping is the responsibility of the customer
- Defective items are eligible for free return shipping

## Warranty

All products come with a 1-year manufacturer warranty covering defects in materials and workmanship.

## Payment Methods

We accept the following payment methods:

- Credit/Debit cards (Visa, Mastercard, Amex)
- PayPal
- Apple Pay / Google Pay
"""


def generate_faq_page(config: SiteConfig) -> str:
    """Generate faq.md template."""
    return f"""# {config.name} — FAQ

## Orders & Shipping

**Q: How long does shipping take?**
A: Standard shipping takes 5–7 business days. Express shipping takes 2–3 business days.

**Q: Do you ship internationally?**
A: Yes, we ship to select international destinations. Shipping costs and delivery times vary by location.

**Q: How can I track my order?**
A: Once your order ships, you will receive a tracking number via email.

## Returns & Exchanges

**Q: What is your return policy?**
A: We accept returns within 30 days of purchase for unused items in original packaging.

**Q: How do I start a return?**
A: Contact our support team with your order number and reason for return.

## Products

**Q: Are your products covered by warranty?**
A: Yes, all products come with a 1-year manufacturer warranty.

**Q: Where are your products made?**
A: Our products are designed in-house and manufactured by trusted partners worldwide.
"""


def generate_about_page(config: SiteConfig) -> str:
    """Generate about.md template."""
    return f"""# About {config.name}

## Our Story

{config.name} is dedicated to providing high-quality products for our customers.

## Contact

- **Website**: {config.canonical_url}
- **Email**: support@{config.canonical_url.replace('https://', '').replace('http://', '').split('/')[0]}

## Language

Primary language: {config.language}

## Topics

{', '.join(config.topics)}
"""


def write_pages(
    products: list[Product],
    config: SiteConfig,
    output_dir: str,
) -> list[str]:
    """Generate all /llm pages and write to output_dir/llm/."""
    base = Path(output_dir) / "llm"
    base.mkdir(parents=True, exist_ok=True)

    pages = {
        "products.md": generate_products_page(products, config),
        "policies.md": generate_policies_page(config),
        "faq.md": generate_faq_page(config),
        "about.md": generate_about_page(config),
    }

    written = []
    for filename, content in pages.items():
        path = base / filename
        path.write_text(content, encoding="utf-8")
        written.append(str(path))

    return written
