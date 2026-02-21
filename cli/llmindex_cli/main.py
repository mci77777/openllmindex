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
from cli.importers.csv_importer import import_csv

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
    input_csv: Path = typer.Option(..., "--input-csv", "-i", help="Path to products CSV file"),
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
) -> None:
    """Generate llmindex artifacts from a products CSV."""

    # Validate input
    if not input_csv.exists():
        console.print(f"[red]Error:[/red] CSV file not found: {input_csv}")
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
    console.print(f"  Source: {input_csv}")
    console.print(f"  Output: {output_dir}")

    # Import products
    products = import_csv(input_csv)
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


if __name__ == "__main__":
    app()
