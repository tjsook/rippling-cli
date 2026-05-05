import json
from http import HTTPStatus

import click

from rippling_cli.constants import RIPPLING_API
from rippling_cli.core.api_client import APIClient
from rippling_cli.utils.login_utils import ensure_logged_in


@click.group()
@click.pass_context
def api(ctx: click.Context):
    """
    Make authenticated GET and PUT requests to the Rippling API.

    Use 'rippling login' first to authenticate, then use the subcommands
    to interact directly with Rippling API endpoints.
    """
    ensure_logged_in(ctx)


@api.command()
@click.argument("endpoint")
@click.option(
    "--params",
    "-p",
    multiple=True,
    metavar="KEY=VALUE",
    help="Query parameters in KEY=VALUE format. Can be specified multiple times.",
)
@click.pass_context
def get(ctx: click.Context, endpoint: str, params: tuple):
    """
    Send a GET request to ENDPOINT and display the response.

    ENDPOINT is the API path relative to https://app.rippling.com/api,
    for example: /auth_ext/get_account_info_v2/

    Examples:

    \b
        rippling api get /auth_ext/get_account_info_v2/
        rippling api get /apps/api/apps/ --params page=1 --params page_size=10
    """
    oauth_token = ctx.obj.oauth_token
    api_client = APIClient(
        base_url=RIPPLING_API,
        headers={"Authorization": f"Bearer {oauth_token}"},
    )

    query_params = {}
    for param in params:
        if "=" not in param:
            raise click.BadParameter(
                f"Invalid format '{param}'. Expected KEY=VALUE.", param_hint="--params"
            )
        key, _, value = param.partition("=")
        query_params[key] = value

    response = api_client.get(endpoint, params=query_params if query_params else None)

    if response.status_code == HTTPStatus.NO_CONTENT:
        click.echo("(no content)")
        return

    try:
        click.echo(json.dumps(response.json(), indent=2))
    except ValueError:
        click.echo(response.text)

    if response.status_code not in (HTTPStatus.OK, HTTPStatus.CREATED, HTTPStatus.ACCEPTED):
        raise SystemExit(1)


@api.command()
@click.argument("endpoint")
@click.option(
    "--data",
    "-d",
    default=None,
    help="JSON payload as a string.",
)
@click.option(
    "--file",
    "-f",
    "file_path",
    default=None,
    type=click.Path(exists=True, readable=True),
    help="Path to a JSON file containing the request payload.",
)
@click.pass_context
def put(ctx: click.Context, endpoint: str, data: str, file_path: str):
    """
    Send a PUT request to ENDPOINT and display the response.

    ENDPOINT is the API path relative to https://app.rippling.com/api.
    Provide a JSON payload via --data (inline string) or --file (path to a JSON file).

    Examples:

    \b
        rippling api put /apps/api/apps/123/ --data '{"displayName": "My App"}'
        rippling api put /apps/api/apps/123/ --file ./update.json
    """
    if data and file_path:
        raise click.UsageError("Provide either --data or --file, not both.")

    payload = None
    if file_path:
        with open(file_path, "r") as fh:
            try:
                payload = json.load(fh)
            except json.JSONDecodeError as exc:
                raise click.BadParameter(f"Invalid JSON in file: {exc}", param_hint="--file")
    elif data:
        try:
            payload = json.loads(data)
        except json.JSONDecodeError as exc:
            raise click.BadParameter(f"Invalid JSON string: {exc}", param_hint="--data")

    oauth_token = ctx.obj.oauth_token
    api_client = APIClient(
        base_url=RIPPLING_API,
        headers={"Authorization": f"Bearer {oauth_token}"},
    )

    response = api_client.make_request("PUT", endpoint, json=payload)

    if response.status_code == HTTPStatus.NO_CONTENT:
        click.echo("(no content)")
        return

    try:
        click.echo(json.dumps(response.json(), indent=2))
    except ValueError:
        click.echo(response.text)

    if response.status_code not in (HTTPStatus.OK, HTTPStatus.CREATED, HTTPStatus.ACCEPTED, HTTPStatus.NO_CONTENT):
        raise SystemExit(1)
