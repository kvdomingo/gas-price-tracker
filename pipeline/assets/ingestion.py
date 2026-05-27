import dagster as dg

from pipeline.partitions import weekly_partitions


@dg.asset(partitions_def=weekly_partitions)
async def fuel_prices__raw():
    pass
