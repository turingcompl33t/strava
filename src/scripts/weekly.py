"""
A simple weekly aggregation.
"""

import argparse
import sys
from datetime import datetime

import humanize
import pytz

import strava.util as util
from strava.client import Strava


def _parse_arguments() -> tuple[int, int, int]:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--year", "-y", type=int, required=True, help="The year"
    )
    parser.add_argument(
        "--month", "-m", type=int, required=True, help="The month"
    )
    parser.add_argument("--day", "-d", type=int, required=True, help="The day")
    args = parser.parse_args()
    return args.year, args.month, args.day


def main() -> int:
    year, month, day = _parse_arguments()

    client = Strava.from_env()

    # get the week start here and run client.week_beginning()
    begin = pytz.timezone("America/New_York").localize(
        datetime(year=year, month=month, day=day, hour=4)
    )
    print(
        f"querying activities for week beginning {humanize.naturaldate(begin)}"
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
