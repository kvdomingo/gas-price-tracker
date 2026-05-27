from dagster_dbt import DbtProject

from common.settings import settings

DBT_PROJECT_DIR = settings.BASE_DIR / "pipeline/dbt"

dbt_project = DbtProject(project_dir=DBT_PROJECT_DIR)
dbt_project.prepare_if_dev()
