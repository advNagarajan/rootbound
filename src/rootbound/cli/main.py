import json
from pathlib import Path
from typing import Optional
import typer
from rich import print
from rich.console import Console

from rootbound.core.engine import RootboundEngine
from rootbound.core.explainer import explain_package

app = typer.Typer(help="Rootbound — Entrypoint-Driven Dependency Graph & Architecture Linter")
console = Console(width=2000)

@app.command(name="scan")
def scan(
    path: str = typer.Argument(..., help="Path to execution entrypoint file or directory"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Write packages list to requirements.txt-like file"),
    show_chains: bool = typer.Option(False, "--show-chains", help="Show exact import trace chains"),
    json_output: bool = typer.Option(False, "--json", help="Output results in JSON format"),
):
    """Scan an entrypoint file or directory to list out unique external dependencies."""
    target = Path(path)
    if not target.exists():
        console.print(f"[red]Error: Path '{path}' does not exist.[/red]")
        raise typer.Exit(code=1)

    is_dir = target.is_dir()
    engine = RootboundEngine(str(target), is_directory=is_dir)
    result = engine.execute_scan()

    if json_output:
        # Construct plain serializable mapping for chains
        output_data = {
            "entrypoint": result.entrypoint,
            "packages": sorted(list(result.top_level_packages)),
            "chains": result.import_chains
        }
        print(json.dumps(output_data, indent=2))
        return

    if not result.top_level_packages:
        console.print("[green]No external dependencies found.[/green]")
        return

    console.print(f"[bold green]Discovered packages ({len(result.top_level_packages)}):[/bold green]")
    for pkg in sorted(result.top_level_packages):
        if show_chains:
            console.print(f"📦 [cyan]{pkg}[/cyan]")
            for chain in result.import_chains.get(pkg, []):
                console.print("  " + " -> ".join(chain))
        else:
            console.print(f"  - {pkg}")

    if output:
        output_path = Path(output)
        with open(output_path, "w", encoding="utf-8") as f:
            for pkg in sorted(result.top_level_packages):
                f.write(f"{pkg}\n")
        console.print(f"\n[green]Wrote requirements to '{output_path}'[/green]")

@app.command(name="explain")
def explain(
    package: str = typer.Argument(..., help="Package name to explain"),
    path: str = typer.Argument(..., help="Path to entrypoint file or directory"),
    json_output: bool = typer.Option(False, "--json", help="Output results in JSON format"),
):
    """Explain how a package is pulled in by tracing import paths back to the entrypoint."""
    target = Path(path)
    if not target.exists():
        console.print(f"[red]Error: Path '{path}' does not exist.[/red]")
        raise typer.Exit(code=1)

    result = explain_package(package, str(target), is_directory=target.is_dir())

    if json_output:
        print(json.dumps({
            "package": result.package,
            "entrypoint": result.entrypoint,
            "reachable": result.reachable,
            "chains": result.chains
        }, indent=2))
        return

    if not result.reachable:
        console.print(f"✅ [bold green]{result.package}[/bold green] is not reachable from {path}")
        return

    console.print(f"📦 [bold cyan]{result.package}[/bold cyan] reachable via:\n")
    for chain in result.chains:
        # Format chain neatly
        console.print(f"  {chain[0]}")
        for step in chain[1:]:
            console.print(f"   → {step}")
        console.print("")

if __name__ == "__main__":
    app()
