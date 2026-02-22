"""llmindex CLI — generate LLM-ready index artifacts for your website."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from llmindex.importers.csv_importer import import_csv
from llmindex.importers.json_importer import import_json
from llmindex.importers.shopify_importer import import_shopify_csv
from llmindex.llmindex_cli.config import ConfigError, load_yaml_config
from llmindex.llmindex_cli.generators.feed import write_feed
from llmindex.llmindex_cli.generators.manifest import generate_manifest, write_manifest
from llmindex.llmindex_cli.generators.pages import write_pages
from llmindex.llmindex_cli.models import SiteConfig
from llmindex.llmindex_cli.validators import validate_all

app = typer.Typer(
    name="llmindex",
    help="Generate LLM-ready index artifacts (llmindex.json, /llm pages, feeds) for your website.",
    no_args_is_help=True,
)
console = Console()
verify_app = typer.Typer(help="Generate and check domain verification challenges.")
app.add_typer(verify_app, name="verify")
sign_app = typer.Typer(help="Sign and verify manifest signatures (EdDSA JWS).")
app.add_typer(sign_app, name="sign")


def _default_manifest_path() -> Optional[Path]:
    candidates = [
        Path.cwd() / ".well-known" / "llmindex.json",
        Path.cwd() / "dist" / ".well-known" / "llmindex.json",
        Path.cwd() / "llmindex.json",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _load_manifest(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Manifest not found: {path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in manifest: {e}") from e


def _require_cryptography() -> None:
    try:
        import cryptography  # type: ignore[import-not-found]
    except ModuleNotFoundError as e:
        console.print(
            "[red]Error:[/red] cryptography is required for `llmindex sign`. "
            "Install with: pip install 'llmindex[sign]'"
        )
        raise typer.Exit(1) from e

    _ = cryptography.__version__


def _normalize_base_url(url: str) -> str:
    return url.strip().rstrip("/")


def _challenge_value(url: str) -> str:
    normalized = _normalize_base_url(url)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]
    return f"llmindex-verify={digest}"


def _resolve_site_url(url: Optional[str], manifest: Optional[Path]) -> str:
    if url:
        return url
    if manifest is not None:
        data = _load_manifest(manifest)
        entity = data.get("entity", {})
        canonical = entity.get("canonical_url")
        if isinstance(canonical, str) and canonical.strip():
            return canonical.strip()

    default_manifest = _default_manifest_path()
    if default_manifest is not None:
        data = _load_manifest(default_manifest)
        entity = data.get("entity", {})
        canonical = entity.get("canonical_url")
        if isinstance(canonical, str) and canonical.strip():
            return canonical.strip()

    config_path = Path("llmindex.yaml")
    if config_path.exists():
        try:
            yaml_config = load_yaml_config(config_path)
        except ConfigError:
            yaml_config = None
        if yaml_config and yaml_config.base_url:
            return yaml_config.base_url

    return typer.prompt("base_url (HTTPS)", prompt_suffix=": ")


def _resolve_verify_value(value: Optional[str], url: str, manifest: Optional[Path]) -> str:
    if value:
        return value
    if manifest is not None:
        data = _load_manifest(manifest)
        verify = data.get("verify", {})
        v = verify.get("value")
        if isinstance(v, str) and v.strip():
            return v.strip()

    default_manifest = _default_manifest_path()
    if default_manifest is not None:
        data = _load_manifest(default_manifest)
        verify = data.get("verify", {})
        v = verify.get("value")
        if isinstance(v, str) and v.strip():
            return v.strip()

    return _challenge_value(url)


@app.command()
def status(
    manifest: Optional[Path] = typer.Option(
        None,
        "--manifest",
        help=(
            "Path to llmindex.json. If omitted, looks for .well-known/llmindex.json "
            "or dist/.well-known/llmindex.json in the current directory."
        ),
    ),
) -> None:
    """Show a quick summary of an llmindex manifest."""
    manifest_path = manifest or _default_manifest_path()
    if manifest_path is None:
        console.print("[yellow]No manifest found.[/yellow] Run 'llmindex generate' first.")
        raise typer.Exit(1)

    try:
        data = _load_manifest(manifest_path)
    except (FileNotFoundError, ValueError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e

    entity = data.get("entity", {}) if isinstance(data, dict) else {}
    endpoints = data.get("endpoints", {}) if isinstance(data, dict) else {}
    verify = data.get("verify") if isinstance(data, dict) else None

    site_name = entity.get("name", "—")
    version = data.get("version", "—")
    updated_at = data.get("updated_at", "—")
    endpoints_count = len(endpoints) if isinstance(endpoints, dict) else 0

    verify_status = "Not configured"
    if isinstance(verify, dict) and verify.get("method") and verify.get("value"):
        method = str(verify.get("method"))
        value = str(verify.get("value"))
        verify_status = f"{method} ({value[:40]}{'…' if len(value) > 40 else ''})"

    table = Table(title=f"llmindex status — {manifest_path}")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Site", str(site_name))
    table.add_row("Spec Version", str(version))
    table.add_row("Endpoints", str(endpoints_count))
    table.add_row("Updated At", str(updated_at))
    table.add_row("Verify", verify_status)
    console.print(table)


@verify_app.command("dns")
def verify_dns(
    url: Optional[str] = typer.Option(
        None,
        "--url",
        "-u",
        help=(
            "Site HTTPS URL. If omitted, tries llmindex.json or llmindex.yaml in the "
            "current directory."
        ),
    ),
    manifest: Optional[Path] = typer.Option(
        None,
        "--manifest",
        help="Optional manifest path used to infer canonical_url.",
    ),
) -> None:
    """Print the DNS TXT record required for domain verification."""
    url_value = _resolve_site_url(url, manifest)
    url_value = _normalize_base_url(url_value)
    if not url_value.startswith("https://"):
        console.print(f"[red]Error:[/red] URL must be HTTPS, got: {url_value}")
        raise typer.Exit(1)

    host = urlparse(url_value).hostname
    if not host:
        console.print(f"[red]Error:[/red] Could not parse domain from URL: {url_value}")
        raise typer.Exit(1)

    value = _challenge_value(url_value)
    console.print("[bold]DNS TXT Verification[/bold]")
    console.print(f"  Record name: [bold]_llmindex-challenge.{host}[/bold]")
    console.print(f"  Record value: [bold]{value}[/bold]")
    console.print("\nSet manifest fields: verify.method=dns_txt, verify.value=<record value>")


@verify_app.command("http")
def verify_http(
    url: Optional[str] = typer.Option(
        None,
        "--url",
        "-u",
        help=(
            "Site HTTPS URL. If omitted, tries llmindex.json or llmindex.yaml in the "
            "current directory."
        ),
    ),
    manifest: Optional[Path] = typer.Option(
        None,
        "--manifest",
        help="Optional manifest path used to infer canonical_url.",
    ),
) -> None:
    """Print the HTTP proof file path and content required for domain verification."""
    url_value = _resolve_site_url(url, manifest)
    url_value = _normalize_base_url(url_value)
    if not url_value.startswith("https://"):
        console.print(f"[red]Error:[/red] URL must be HTTPS, got: {url_value}")
        raise typer.Exit(1)

    value = _challenge_value(url_value)
    console.print("[bold]HTTP File Verification[/bold]")
    console.print("  Path: [bold]/.well-known/llmindex-proof.txt[/bold]")
    console.print(f"  Content: [bold]{value}[/bold]")
    console.print("\nSet manifest fields: verify.method=http_file, verify.value=<file content>")


@verify_app.command("check")
def verify_check(
    method: str = typer.Option(
        ...,
        "--method",
        help="Verification method to check: dns or http.",
        case_sensitive=False,
    ),
    url: Optional[str] = typer.Option(
        None,
        "--url",
        "-u",
        help=(
            "Site HTTPS URL. If omitted, tries llmindex.json or llmindex.yaml in the "
            "current directory."
        ),
    ),
    value: Optional[str] = typer.Option(
        None,
        "--value",
        help=(
            "Expected verification value (defaults to manifest verify.value, else "
            "derived from URL)."
        ),
    ),
    manifest: Optional[Path] = typer.Option(
        None,
        "--manifest",
        help="Optional manifest path used to infer canonical_url and verify.value.",
    ),
    timeout: float = typer.Option(5.0, "--timeout", help="Network timeout in seconds."),
) -> None:
    """Check whether DNS/HTTP verification is configured correctly."""
    method_normalized = method.strip().lower()
    if method_normalized not in {"dns", "http"}:
        console.print("[red]Error:[/red] --method must be one of: dns, http")
        raise typer.Exit(1)

    url_value = _resolve_site_url(url, manifest)
    url_value = _normalize_base_url(url_value)
    if not url_value.startswith("https://"):
        console.print(f"[red]Error:[/red] URL must be HTTPS, got: {url_value}")
        raise typer.Exit(1)

    expected_value = _resolve_verify_value(value, url_value, manifest)

    host = urlparse(url_value).hostname
    if not host:
        console.print(f"[red]Error:[/red] Could not parse domain from URL: {url_value}")
        raise typer.Exit(1)

    if method_normalized == "dns":
        try:
            import dns.resolver  # type: ignore[import-not-found]
        except ModuleNotFoundError as e:
            console.print(
                "[red]Error:[/red] dnspython is required for DNS checks. "
                "Install with: pip install 'llmindex[verify]'"
            )
            raise typer.Exit(1) from e

        record_name = f"_llmindex-challenge.{host}"
        try:
            answers = dns.resolver.resolve(record_name, "TXT")
            txt_values = []
            for rdata in answers:
                for s in rdata.strings:
                    txt_values.append(s.decode("utf-8", errors="replace"))
        except Exception as e:
            console.print(f"[red]✗[/red] DNS lookup failed for {record_name}: {e}")
            raise typer.Exit(1) from e

        if expected_value in txt_values:
            console.print(
                f"[green]✓[/green] DNS TXT record contains expected value: {expected_value}"
            )
            raise typer.Exit(0)

        console.print(f"[red]✗[/red] Expected value not found in TXT records for {record_name}")
        for v in txt_values:
            console.print(f"  - {v}")
        raise typer.Exit(1)

    # method_normalized == "http"
    try:
        import httpx  # type: ignore[import-not-found]
    except ModuleNotFoundError as e:
        console.print(
            "[red]Error:[/red] httpx is required for HTTP checks. "
            "Install with: pip install 'llmindex[verify]'"
        )
        raise typer.Exit(1) from e

    proof_url = f"{url_value}/.well-known/llmindex-proof.txt"
    try:
        head = httpx.head(proof_url, follow_redirects=True, timeout=timeout)
    except httpx.HTTPError as e:  # type: ignore[attr-defined]
        console.print(f"[red]✗[/red] HTTP HEAD failed: {e}")
        raise typer.Exit(1) from e

    if head.status_code >= 400:
        console.print(
            f"[red]✗[/red] Proof file not reachable (status {head.status_code}): {proof_url}"
        )
        raise typer.Exit(1)

    try:
        resp = httpx.get(proof_url, follow_redirects=True, timeout=timeout)
        body = resp.text.strip()
    except httpx.HTTPError as e:  # type: ignore[attr-defined]
        console.print(f"[red]✗[/red] HTTP GET failed: {e}")
        raise typer.Exit(1) from e

    if body == expected_value:
        console.print(
            f"[green]✓[/green] Proof file content matches expected value: {expected_value}"
        )
        raise typer.Exit(0)

    console.print(f"[red]✗[/red] Proof file content does not match expected value at: {proof_url}")
    console.print(f"  Expected: {expected_value}")
    console.print(f"  Got: {body}")
    raise typer.Exit(1)


@sign_app.command("keygen")
def sign_keygen(
    output: Path = typer.Option(
        ...,
        "--output",
        "-o",
        help="Output directory for key files (private.pem + public.pem).",
    ),
) -> None:
    """Generate an Ed25519 keypair for signing llmindex manifests."""
    _require_cryptography()
    from llmindex.llmindex_cli.commands.sign import keygen

    try:
        private_path, public_path = keygen(output)
    except (OSError, ValueError, ModuleNotFoundError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e

    console.print("[bold]Generated keys:[/bold]")
    console.print(f"  [green]✓[/green] {private_path}")
    console.print(f"  [green]✓[/green] {public_path}")


@sign_app.command("manifest")
def sign_manifest_cmd(
    manifest: Path = typer.Argument(..., help="Path to llmindex.json manifest file"),
    key: Path = typer.Option(..., "--key", help="Path to Ed25519 private key PEM (private.pem)"),
) -> None:
    """Sign a manifest and write the `sig` field back to disk."""
    _require_cryptography()
    from llmindex.llmindex_cli.commands.sign import sign_manifest

    try:
        sign_manifest(manifest, key)
    except (OSError, ValueError, ModuleNotFoundError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e

    console.print(f"[green]✓[/green] Signed manifest: {manifest}")


@sign_app.command("verify")
def sign_verify_cmd(
    manifest: Path = typer.Argument(..., help="Path to llmindex.json manifest file"),
    key: Path = typer.Option(..., "--key", help="Path to Ed25519 public key PEM (public.pem)"),
) -> None:
    """Verify a signed manifest using an Ed25519 public key."""
    _require_cryptography()
    from llmindex.llmindex_cli.commands.verify_sig import verify_signature

    try:
        ok = verify_signature(manifest, key)
    except (OSError, ValueError, ModuleNotFoundError) as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e

    raise typer.Exit(0 if ok else 1)


@app.command()
def init(
    force: bool = typer.Option(
        False,
        "--force",
        help="Overwrite llmindex.yaml if it already exists (skip confirmation).",
    ),
) -> None:
    """Interactively create an llmindex.yaml config in the current directory."""
    config_path = Path("llmindex.yaml")
    if config_path.exists() and not force:
        overwrite = typer.confirm(f"{config_path} already exists. Overwrite?", default=False)
        if not overwrite:
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit(0)

    site_name = typer.prompt("site_name", prompt_suffix=": ")
    base_url = typer.prompt("base_url (HTTPS)", prompt_suffix=": ")
    language = typer.prompt("language", default="zh-CN", show_default=True, prompt_suffix=": ")
    topics_raw = typer.prompt(
        "topics (comma-separated)", default="general", show_default=True, prompt_suffix=": "
    )
    topics = [t.strip() for t in topics_raw.split(",") if t.strip()] or ["general"]

    try:
        import yaml

        with config_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(
                {
                    "site_name": site_name,
                    "base_url": base_url,
                    "language": language,
                    "topics": topics,
                },
                f,
                allow_unicode=True,
                sort_keys=False,
            )
    except OSError as e:
        console.print(f"[red]Error:[/red] Failed to write {config_path}: {e}")
        raise typer.Exit(1) from e

    console.print(
        Panel.fit(
            f"[bold green]✓ Created {config_path}[/bold green]\n\n"
            f"Next: [bold]llmindex generate --config {config_path}[/bold]",
            title="llmindex init",
            border_style="green",
        )
    )


@app.command()
def generate(
    config_path: Optional[Path] = typer.Option(
        None,
        "--config",
        help="Path to llmindex.yaml config (fields: site_name, base_url, language, topics).",
    ),
    site: Optional[str] = typer.Option(
        None, "--site", "-s", help="Entity/brand name (overrides config.site_name)"
    ),
    url: Optional[str] = typer.Option(
        None, "--url", "-u", help="Canonical HTTPS URL of the site (overrides config.base_url)"
    ),
    input_csv: Optional[Path] = typer.Option(
        None, "--input-csv", "-i", help="Path to products CSV file"
    ),
    input_json: Optional[Path] = typer.Option(
        None, "--input-json", help="Path to products JSON file (array of objects)"
    ),
    input_shopify_csv: Optional[Path] = typer.Option(
        None, "--input-shopify-csv", help="Path to Shopify product export CSV"
    ),
    templates_dir: Optional[Path] = typer.Option(
        None,
        "--templates-dir",
        help=(
            "Directory with Jinja2 templates to override policies/faq/about "
            "(files: policies.md.j2, faq.md.j2, about.md.j2)."
        ),
    ),
    output_dir: Path = typer.Option(
        "dist", "--output-dir", "-o", help="Output directory (default: dist)"
    ),
    language: Optional[str] = typer.Option(
        None, "--language", "-l", help="Primary language (BCP-47) (overrides config.language)"
    ),
    topics: Optional[list[str]] = typer.Option(
        None, "--topic", "-t", help="Category topics (repeatable) (overrides config.topics)"
    ),
    base_url: Optional[str] = typer.Option(
        None, "--base-url", help="Base URL for endpoints (defaults to --url)"
    ),
    currency: str = typer.Option(
        "USD", "--currency", help="Default currency for Shopify imports (default: USD)"
    ),
) -> None:
    """Generate llmindex artifacts (manifest, /llm pages, optional product feed).

    If no product input is provided, the command still succeeds and generates only the
    manifest + pages.
    This is useful for SaaS, blogs, and other non-ecommerce sites.
    """

    yaml_config = None
    if config_path is not None:
        try:
            yaml_config = load_yaml_config(config_path)
        except ConfigError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from e

    site_value = (site or (yaml_config.site_name if yaml_config else None) or "").strip()
    url_value = (url or (yaml_config.base_url if yaml_config else None) or "").strip()
    language_value = (language or (yaml_config.language if yaml_config else None) or "en").strip()
    topics_value = topics or (yaml_config.topics if yaml_config else None) or ["general"]

    if not site_value:
        console.print(
            "[red]Error:[/red] Missing site name. Provide --site or set site_name in --config."
        )
        raise typer.Exit(1)
    if not url_value:
        console.print(
            "[red]Error:[/red] Missing site URL. Provide --url or set base_url in --config."
        )
        raise typer.Exit(1)

    # Allow zero or one input source
    inputs = [input_csv, input_json, input_shopify_csv]
    provided = [x for x in inputs if x is not None]
    if len(provided) > 1:
        console.print("[red]Error:[/red] Provide only one input source")
        raise typer.Exit(1)

    input_path = provided[0] if provided else None
    if input_path is not None and not input_path.exists():
        console.print(f"[red]Error:[/red] Input file not found: {input_path}")
        raise typer.Exit(1)

    if not url_value.startswith("https://"):
        console.print("[red]Error:[/red] --url must be an HTTPS URL")
        raise typer.Exit(1)

    # Build config
    site_config = SiteConfig(
        name=site_value,
        canonical_url=url_value,
        language=language_value,
        topics=topics_value,
        base_url=base_url,
    )

    console.print(f"[bold]Generating llmindex artifacts for {site_value}[/bold]")
    console.print(f"  Source: {input_path or '(none)'}")
    console.print(f"  Output: {output_dir}")

    # Import products from the appropriate source
    if input_path is None:
        products = []
        console.print(
            "  [yellow]![/yellow] No product input provided. Generating manifest + pages only."
        )
    elif input_csv is not None:
        products = import_csv(input_csv)
    elif input_json is not None:
        products = import_json(input_json)
    elif input_shopify_csv is not None:
        products = import_shopify_csv(input_shopify_csv, base_url=url_value, currency=currency)
    else:
        products = []

    console.print(f"  Imported: {len(products)} products")

    if input_path is not None and not products:
        console.print("[yellow]Warning:[/yellow] No products imported. Generating without feed.")

    # Generate manifest
    manifest = generate_manifest(site_config, has_feed=len(products) > 0)
    manifest_path = str(output_dir / ".well-known" / "llmindex.json")
    write_manifest(manifest, manifest_path)
    console.print(f"  [green]✓[/green] {manifest_path}")

    # Generate pages
    try:
        page_paths = write_pages(
            products,
            site_config,
            str(output_dir),
            templates_dir=templates_dir,
        )
    except ModuleNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e
    for p in page_paths:
        console.print(f"  [green]✓[/green] {p}")

    # Generate feed
    if products:
        feed_path = write_feed(products, str(output_dir))
        console.print(f"  [green]✓[/green] {feed_path}")

    console.print(
        f"\n[bold green]Done![/bold green] Generated "
        f"{4 + (1 if products else 0) + 1} files in {output_dir}/"
    )


@app.command()
def watch(
    config_path: Path = typer.Option(
        "llmindex.yaml",
        "--config",
        help="Path to llmindex.yaml config file.",
    ),
    output_dir: Path = typer.Option(
        "dist", "--output-dir", "-o", help="Output directory (default: dist)"
    ),
    templates_dir: Optional[Path] = typer.Option(
        None,
        "--templates-dir",
        help="Directory with Jinja2 templates (policies.md.j2, faq.md.j2, about.md.j2).",
    ),
    currency: str = typer.Option(
        "USD", "--currency", help="Default currency for Shopify imports (default: USD)"
    ),
) -> None:
    """Watch source files and rebuild artifacts on change.

    Monitors llmindex.yaml and product source files (CSV/JSON) for changes,
    then automatically regenerates manifest, pages, and feed.

    Requires the [watch] extra: pip install 'llmindex[watch]'
    """
    if not config_path.exists():
        console.print(f"[red]Error:[/red] Config file not found: {config_path}")
        raise typer.Exit(1)

    try:
        from llmindex.llmindex_cli.commands.watch import run_watch
    except ModuleNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e

    try:
        run_watch(config_path, output_dir, templates_dir=templates_dir, currency=currency)
    except ModuleNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e
    except KeyboardInterrupt:
        console.print("\n[bold]Watch stopped.[/bold]")


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
    check_urls: bool = typer.Option(
        False,
        "--check-urls",
        help=(
            "Check that manifest endpoint URLs are reachable via HTTP HEAD (requires httpx extra)."
        ),
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

    if check_urls:
        try:
            import httpx  # type: ignore[import-not-found]
        except ModuleNotFoundError as e:
            console.print(
                "[red]Error:[/red] httpx is required for --check-urls. "
                "Install with: pip install 'llmindex[verify]'"
            )
            raise typer.Exit(1) from e

        try:
            data = _load_manifest(manifest)
        except (FileNotFoundError, ValueError) as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1) from e

        endpoints = data.get("endpoints", {}) if isinstance(data, dict) else {}
        table = Table(title="Endpoint URL Reachability")
        table.add_column("Endpoint", style="bold")
        table.add_column("Status")
        table.add_column("HTTP")
        table.add_column("URL")

        if not isinstance(endpoints, dict) or not endpoints:
            table.add_row("—", "[yellow]No endpoints found[/yellow]", "—", "—")
        else:
            client = httpx.Client(follow_redirects=True, timeout=5.0)
            try:
                for name, endpoint_url in endpoints.items():
                    if not isinstance(endpoint_url, str):
                        table.add_row(
                            str(name),
                            "[red]unreachable[/red]",
                            "—",
                            str(endpoint_url),
                        )
                        continue

                    try:
                        resp = client.head(endpoint_url)
                        ok = resp.status_code < 400
                        table.add_row(
                            str(name),
                            "[green]reachable[/green]" if ok else "[red]unreachable[/red]",
                            str(resp.status_code),
                            endpoint_url,
                        )
                    except httpx.HTTPError as ex:  # type: ignore[attr-defined]
                        table.add_row(
                            str(name),
                            "[red]unreachable[/red]",
                            "—",
                            f"{endpoint_url} ({ex})",
                        )
            finally:
                client.close()

        console.print(table)

    if result.valid:
        console.print("[bold green]Valid![/bold green] Manifest passes llmindex v0.1 schema.")
    else:
        console.print(f"\n[bold red]Invalid.[/bold red] {len(result.errors)} error(s) found.")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
