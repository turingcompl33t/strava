"""
A simple weekly aggregation.
"""

import sys
from datetime import datetime

import pytz

import strava.util as util
from strava.client import Strava


def main() -> int:
    client = Strava.from_env()

    # get the week start here and run client.week_beginning()
    begin = pytz.timezone("America/New_York").localize(
        datetime(year=2025, month=12, day=29, hour=4)
    )
    activities = client.week_beginning(begin)

    # alternatively, if  this is run at a regular time that captures the
    # desired week, we can get activities easily with:
    # activities = client.last_week()

    print(f"{len(activities)} activities")

    training_time = util.total_duration(activities)
    print("total training:")
    print(f"  {training_time} hours")

    hr_data = util.aggregate_hr(activities)
    print("heartrate data:")
    for k, v in sorted(
        [(zone, duration) for zone, duration in hr_data.items()]
    ):
        print(f"  {k} {v:.2f} minutes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
