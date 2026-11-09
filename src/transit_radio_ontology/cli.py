"""CLI: ``transit-radio-ontology`` subcommands.

Commands
--------
    validate FILE   Validate a scenario (entities + events) against the
                    bundled JSON schemas.
    inspect  FILE   Print entity counts and event counts grouped by type.
    schema   NAME   Print one bundled schema (e.g. "Vehicle").
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import typer

from .graph import Scenario
from .schemas import list_schemas, load_schema

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Transit Radio Ontology CLI.",
)


@app.command()
def validate(
    file: Path = typer.Argument(..., exists=True, readable=True, help="Scenario JSON file."),
    strict_refs: bool = typer.Option(
        False,
        "--strict-refs",
        help="Treat unresolved id references as errors.",
    ),
) -> None:
    """Validate a scenario file against the bundled JSON schemas."""
    try:
        scenario = Scenario.from_file(file)
    except Exception as exc:
        typer.echo(f"error: failed to parse {file}: {exc}", err=True)
        raise typer.Exit(2)

    schema_errors, ref_errors = scenario.validate_all(strict_refs=strict_refs)

    typer.echo(
        f"entities: {len(scenario.entities)}  events: {len(scenario.events)}"
    )

    if not schema_errors and not ref_errors:
        typer.echo("OK")
        return

    for e in schema_errors:
        typer.echo(f"schema: {e}", err=True)
    for e in ref_errors:
        typer.echo(f"refs:   {e}", err=True)
    raise typer.Exit(1)


@app.command()
def inspect(
    file: Path = typer.Argument(..., exists=True, readable=True),
) -> None:
    """Print entity counts and event counts grouped by type."""
    scenario = Scenario.from_file(file)
    typer.echo(f"source: {scenario.source}")
    typer.echo(f"entities: {len(scenario.entities)}")
    entity_types = Counter(type(e).__name__ for e in scenario.entities.values())
    for name, count in sorted(entity_types.items()):
        typer.echo(f"  {name}: {count}")
    typer.echo(f"events: {len(scenario.events)}")
    event_types = Counter(type(e).__name__ for e in scenario.events)
    for name, count in sorted(event_types.items()):
        typer.echo(f"  {name}: {count}")


@app.command()
def schema(
    name: str = typer.Argument(..., help="Schema kind, e.g. 'Vehicle' or 'PTTEvent'."),
) -> None:
    """Print the bundled JSON schema for ``name`` to stdout."""
    try:
        s = load_schema(name)
    except KeyError:
        known = ", ".join(sorted(list_schemas().keys()))
        typer.echo(f"error: unknown schema {name!r}. Known: {known}", err=True)
        raise typer.Exit(2)
    json.dump(s, sys.stdout, indent=2, sort_keys=False)
    sys.stdout.write("\n")


@app.command("list-schemas")
def list_schemas_cmd() -> None:
    """List every bundled schema name."""
    for name in sorted(list_schemas().keys()):
        typer.echo(name)


if __name__ == "__main__":
    app()
