import typer
from rich import print

from merchants.integrations import _provider_list

cli = typer.Typer(help="Merchants CLI operations")


@cli.command("list-providers")
def list_providers():
    """Show available providers"""
    print(_provider_list)
    typer.Exit()


@cli.command("make-provider-config")
def make_provider_config(provider_slug: str):
    """Prints the necessary config for the given provider"""
    pass


if __name__ == "__main__":
    cli()
