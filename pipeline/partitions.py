import dagster as dg

weekly_partitions = dg.WeeklyPartitionsDefinition(start_date="2020-12-24")
