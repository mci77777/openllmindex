"""CLI watch mode — monitor source files and rebuild artifacts on change."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from rich.console import Console

from llmindex.importers.csv_importer import import_csv
from llmindex.importers.json_importer import import_json
from llmindex.importers.shopify_importer import import_shopify_csv
from llmindex.llmindex_cli.config import ConfigError, load_yaml_config
from llmindex.llmindex_cli.generators.feed import write_feed
from llmindex.llmindex_cli.generators.manifest import generate_manifest, write_manifest
from llmindex.llmindex_cli.generators.pages import write_pages
from llmindex.llmindex_cli.models import SiteConfig

console = Console()


def _resolve_input_source(yaml_path: Path) -> tuple[Optional[Path], str]:
    """Resolve the product input file and its type from llmindex.yaml directory.

    Looks for common source files relative to the config file's parent dir.
    Returns (path, type) where type is 'csv' | 'json' | 'shopify_csv' | 'none'.
    """
    config_dir = yaml_path.parent

    # Check for explicit source patterns
    candidates = [
        (config_dir / "products.csv", "csv"),
        (config_dir / "products.json", "json"),
        (config_dir / "shopify_products.csv", "shopify_csv"),
        (config_dir / "data" / "products.csv", "csv"),
        (config_dir / "data" / "products.json", "json"),
    ]
    for path, source_type in candidates:
        if path.exists():
            return path, source_type

    return None, "none"


def _import_products(
    input_path: Optional[Path], source_type: str, base_url: str, currency: str = "USD"
) -> list:
    """Import products from the given source."""
    if input_path is None or source_type == "none":
        return []
    if source_type == "csv":
        return import_csv(input_path)
    if source_type == "json":
        return import_json(input_path)
    if source_type == "shopify_csv":
        return import_shopify_csv(input_path, base_url=base_url, currency=currency)
    return []


def build_artifacts(
    config_path: Path,
    output_dir: Path,
    input_csv: Optional[Path] = None,
    input_json: Optional[Path] = None,
    input_shopify_csv: Optional[Path] = None,
    templates_dir: Optional[Path] = None,
    currency: str = "USD",
) -> list[str]:
    """Build all llmindex artifacts and return list of written file paths.

    This is the shared build logic used by both `generate` and `watch`.
    """
    try:
        yaml_config = load_yaml_config(config_path)
    except ConfigError as e:
        raise ConfigError(f"Config error: {e}") from e

    site_value = (yaml_config.site_name or "").strip()
    url_value = (yaml_config.base_url or "").strip()
    language_value = (yaml_config.language or "en").strip()
    topics_value = yaml_config.topics or ["general"]

    if not site_value:
        raise ConfigError("Missing site_name in config")
    if not url_value:
        raise ConfigError("Missing base_url in config")

    # Determine input source
    if input_csv:
        input_path, source_type = input_csv, "csv"
    elif input_json:
        input_path, source_type = input_json, "json"
    elif input_shopify_csv:
        input_path, source_type = input_shopify_csv, "shopify_csv"
    else:
        input_path, source_type = _resolve_input_source(config_path)

    site_config = SiteConfig(
        name=site_value,
        canonical_url=url_value,
        language=language_value,
        topics=topics_value,
    )

    products = _import_products(input_path, source_type, url_value, currency)

    written: list[str] = []

    # Manifest
    manifest = generate_manifest(site_config, has_feed=len(products) > 0)
    manifest_path = str(output_dir / ".well-known" / "llmindex.json")
    write_manifest(manifest, manifest_path)
    written.append(manifest_path)

    # Pages
    page_paths = write_pages(products, site_config, str(output_dir), templates_dir=templates_dir)
    written.extend(page_paths)

    # Feed
    if products:
        feed_path = write_feed(products, str(output_dir))
        written.append(feed_path)

    return written


def collect_watch_paths(config_path: Path) -> list[Path]:
    """Collect all file paths that should be watched for changes.

    Watches:
    - The config file itself (llmindex.yaml)
    - Product source files (products.csv, products.json, etc.)
    - Template files (*.j2) if templates_dir is set
    """
    paths: list[Path] = [config_path.resolve()]

    input_path, _ = _resolve_input_source(config_path)
    if input_path is not None:
        paths.append(input_path.resolve())

    # Watch template files in the config directory
    config_dir = config_path.parent
    for pattern in ("*.j2", "templates/*.j2"):
        for p in config_dir.glob(pattern):
            paths.append(p.resolve())

    return paths


def run_watch(
    config_path: Path,
    output_dir: Path,
    templates_dir: Optional[Path] = None,
    currency: str = "USD",
) -> None:
    """Start the file watcher loop. Blocks until interrupted."""
    try:
        from watchfiles import watch  # type: ignore[import-not-found]
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "watchfiles is required for `llmindex watch`. "
            "Install with: pip install 'llmindex[watch]'"
        ) from e

    watch_paths = collect_watch_paths(config_path)

    # Determine directories to watch (watchfiles watches directories)
    watch_dirs: set[Path] = set()
    for p in watch_paths:
        watch_dirs.add(p.parent if p.is_file() else p)

    console.print("[bold]llmindex watch[/bold] — monitoring for changes")
    console.print(f"  Config: {config_path}")
    console.print(f"  Output: {output_dir}")
    console.print(f"  Watching: {len(watch_paths)} path(s)")
    for p in watch_paths:
        console.print(f"    - {p}")

    # Initial build
    console.print("\n[bold]Initial build...[/bold]")
    try:
        written = build_artifacts(
            config_path, output_dir, templates_dir=templates_dir, currency=currency
        )
        for f in written:
            console.print(f"  [green]✓[/green] {f}")
        console.print(f"[green]Built {len(written)} files.[/green]")
    except Exception as e:
        console.print(f"[red]Build failed:[/red] {e}")

    console.print("\n[dim]Watching for changes... (Ctrl+C to stop)[/dim]\n")

    # Filter function: only trigger on watched files
    watched_suffixes = {".yaml", ".yml", ".csv", ".json", ".j2"}

    def _should_trigger(changed_path: Path) -> bool:
        resolved = changed_path.resolve()
        # Exact match
        if resolved in {p.resolve() for p in watch_paths}:
            return True
        # Suffix match for auto-discovered files
        return resolved.suffix in watched_suffixes

    for changes in watch(*watch_dirs):
        # changes is a set of (change_type, path) tuples
        relevant = [(ct, p) for ct, p in changes if _should_trigger(Path(p))]
        if not relevant:
            continue

        for change_type, path in relevant:
            console.print(f"  [yellow]→[/yellow] {change_type.name}: {path}")

        console.print("[bold]Rebuilding...[/bold]")
        try:
            written = build_artifacts(
                config_path, output_dir, templates_dir=templates_dir, currency=currency
            )
            for f in written:
                console.print(f"  [green]✓[/green] {f}")
            console.print(f"[green]Rebuilt {len(written)} files.[/green]\n")
        except Exception as e:
            console.print(f"[red]Rebuild failed:[/red] {e}\n")
