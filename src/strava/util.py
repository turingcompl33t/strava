"""
Utilities.
"""

from strava.client import Activity


def aggregate_hr(activities: list[Activity]) -> dict[str, float]:
    """
    Aggregate heartrate data by zone.
    :param activities: The enriched activities
    :return: Aggregated heartrate data; zone -> minutes in zone
    """
    # collect all heartrate data
    data = [hr for a in activities for hr in a.heartrate_data]
    # group by zone and aggregate
    agg = {k: 0.0 for k in set([hr.id for hr in data])}
    for hr in data:
        agg[hr.id] += hr.time.seconds / 60
    return agg


def total_duration(activities: list[Activity]) -> float:
    """
    Aggregate total activity duration.
    :param The activities
    :return: Total training duration, in hours
    """
    return sum(a.duration.seconds for a in activities) / (60 * 60)
