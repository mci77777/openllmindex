"""llmindex CLI — generate LLM-ready index artifacts for your website."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from cli.llmindex_cli.generators.feed import write_feed
from cli.llmindex_cli.generators.manifest import generate_manifest, write_manifest
from cli.llmindex_cli.generators.pages import write_pages
from cli.llmindex_cli.models import SiteConfig
from cli.llmindex_cli.validators import validate_all, validate_feed, validate_manifest
from cli.importers.csv_importer import import_csv
from cli.importers.json_importer import import_json
from cli.importers.shopify_importer import import_shopify_csv

app = typer.Typer(
    name="llmindex",
    help="Generate LLM-ready index artifacts (llmindex.json, /llm pages, feeds) for your website.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def generate(
    site: str = typer.Option(..., "--site", "-s", help="Entity/brand name"),
    url: str = typer.Option(..., "--url", "-u", help="Canonical HTTPS URL of the site"),
    input_csv: Optional[Path] = typer.Option(
        None, "--input-csv", "-i", help="Path to products CSV file"
    ),
    input_json: Optional[Path] = typer.Option(
        None, "--input-json", help="Path to products JSON file (array of objects)"
    ),
    input_shopify_csv: Optional[Path] = typer.Option(
        None, "--input-shopify-csv", help="Path to Shopify product export CSV"
    ),
    output_dir: Path = typer.Option(
        "dist", "--output-dir", "-o", help="Output directory (default: dist)"
    ),
    language: str = typer.Option("en", "--language", "-l", help="Primary language (BCP-47)"),
    topics: Optional[list[str]] = typer.Option(
        None, "--topic", "-t", help="Category topics (repeatable)"
    ),
    base_url: Optional[str] = typer.Option(
        None, "--base-url", help="Base URL for endpoints (defaults to --url)"
    ),
    currency: str = typer.Option(
        "USD", "--currency", help="Default currency for Shopify imports (default: USD)"
    ),
) -> None:
    """Generate llmindex artifacts from product data (CSV, JSON, or Shopify export)."""

    # Require exactly one input source
    inputs = [input_csv, input_json, input_shopify_csv]
    provided = [x for x in inputs if x is not None]
    if len(provided) == 0:
        console.print("[red]Error:[/red] Provide one of --input-csv, --input-json, or --input-shopify-csv")
        raise typer.Exit(1)
    if len(provided) > 1:
        console.print("[red]Error:[/red] Provide only one input source")
        raise typer.Exit(1)

    input_path = provided[0]
    if not input_path.exists():
        console.print(f"[red]Error:[/red] Input file not found: {input_path}")
        raise typer.Exit(1)

    if not url.startswith("https://"):
        console.print("[red]Error:[/red] --url must be an HTTPS URL")
        raise typer.Exit(1)

    # Build config
    config = SiteConfig(
        name=site,
        canonical_url=url,
        language=language,
        topics=topics or ["general"],
        base_url=base_url,
    )

    console.print(f"[bold]Generating llmindex artifacts for {site}[/bold]")
    console.print(f"  Source: {input_path}")
    console.print(f"  Output: {output_dir}")

    # Import products from the appropriate source
    if input_csv is not None:
        products = import_csv(input_csv)
    elif input_json is not None:
        products = import_json(input_json)
    elif input_shopify_csv is not None:
        products = import_shopify_csv(input_shopify_csv, base_url=url, currency=currency)
    else:
        products = []

    console.print(f"  Imported: {len(products)} products")

    if not products:
        console.print("[yellow]Warning:[/yellow] No products imported. Generating without feed.")

    # Generate manifest
    manifest = generate_manifest(config, has_feed=len(products) > 0)
    manifest_path = str(output_dir / ".well-known" / "llmindex.json")
    write_manifest(manifest, manifest_path)
    console.print(f"  [green]✓[/green] {manifest_path}")

    # Generate pages
    page_paths = write_pages(products, config, str(output_dir))
    for p in page_paths:
        console.print(f"  [green]✓[/green] {p}")

    # Generate feed
    if products:
        feed_path = write_feed(products, str(output_dir))
        console.print(f"  [green]✓[/green] {feed_path}")

    console.print(f"\n[bold green]Done![/bold green] Generated {4 + (1 if products else 0) + 1} files in {output_dir}/")


@app.command()
def version() -> None:
    """Show llmindex CLI version."""
    console.print("llmindex v0.1.0")


@app.command()
def validate(
    manifest: Path = typer.Argument(..., help="Path to llmindex.json manifest file"),
    feed: Optional[Path] = typer.Option(
        None, "--feed", "-f", help="Path to products.jsonl feed file (auto-detected if omitted)"
    ),
) -> None:
    """Validate a manifest (and optionally its feed) against the llmindex v0.1 schema."""

    console.print(f"[bold]Validating:[/bold] {manifest}")

    result = validate_all(manifest, feed)

    # Display warnings
    for w in result.warnings:
        console.print(f"  [yellow]![/yellow] {w}")

    # Display errors
    for e in result.errors:
        console.print(f"  [red]✗[/red] {e}")

    if result.valid:
        console.print("[bold green]Valid![/bold green] Manifest passes llmindex v0.1 schema.")
    else:
        console.print(f"\n[bold red]Invalid.[/bold red] {len(result.errors)} error(s) found.")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
