import subprocess

from dagster import AssetExecutionContext, asset

from .dbt_assets import gas_price_tracker_dbt_assets


@asset(deps=[gas_price_tracker_dbt_assets], group_name="codegen")
def sqlalchemy_models(context: AssetExecutionContext) -> None:
    """Regenerate storage/models.py from the live database schema after dbt run."""
    import os

    database_url = os.environ["DATABASE_URL"]
    output_path = "storage/models.py"

    result = subprocess.run(
        [
            "sqlacodegen",
            "--generator",
            "declarative",
            database_url,
            "--outfile",
            output_path,
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(f"sqlacodegen failed:\n{result.stderr}")

    context.log.info(f"Generated SQLAlchemy models at {output_path}")
