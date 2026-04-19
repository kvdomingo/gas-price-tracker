from dagster import ScheduleDefinition


weekly_ingestion_schedule = ScheduleDefinition(
    job_name="ingestion_job",
    cron_schedule="0 8 * * 5",  # Fridays at 08:00 (aligned with DOE publication cadence)
    execution_timezone="Asia/Manila",
)
