"""
A simple weekly aggregation.
"""

import sys

import strava.util as util
from strava.client import Strava


def main() -> int:
    client = Strava.from_env()

    # if the script isn't run at the expected day / time, can manually
    # get the week start here and run client.week_beginning()
    # begin = pytz.timezone("America/New_York").localize(datetime(year=2025, month=12, day=22, hour=4))
    # activities = client.week_beginning(begin)

    activities = client.last_week()
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
