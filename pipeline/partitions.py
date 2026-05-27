import dagster as dg

weekly_partitions = dg.WeeklyPartitionsDefinition(start_date="2020-12-24")

files_partitions_def = dg.DynamicPartitionsDefinition(name="files")
