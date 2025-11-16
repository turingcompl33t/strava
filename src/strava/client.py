from __future__ import annotations

import os
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

import dateutil
import humanize
import requests
from pydantic import BaseModel


class ActivityType(StrEnum):
    RUN = "run"
    WORKOUT = "workout"

    @staticmethod
    def parse(string: str) -> ActivityType:
        """Parse from a string."""
        match string.lower():
            case "run":
                return ActivityType.RUN
            case "workout":
                return ActivityType.WORKOUT
            case _:
                raise ValueError(f"unknown activity type '{string}'")


class Heartrate(BaseModel):
    # a useful identifier for the zone
    id: str = ""
    # the minium value (BPM)
    min: int
    # the maximum value (BPM)
    max: int
    # the time in this zone
    time: timedelta

    def __str__(self) -> str:
        if self.min == 0:
            return f"< {self.max} {humanize.naturaldelta(self.time)}"
        elif self.max == -1:
            return f"> {self.min} {humanize.naturaldelta(self.time)}"
        else:
            return f"{self.min}-{self.max} {humanize.naturaldelta(self.time)}"


class Activity(BaseModel):
    """A Strava activity."""

    # unique identifier
    id: int

    # the name of the activity
    name: str

    # the type of the activity
    type: ActivityType

    # the start date for the activity
    start_datetime: datetime

    # elapsed time of the activity
    duration: timedelta

    # a flag indicating this activity has heartrate data
    has_heartrate: bool
    # the heartrate data for this activity
    heartrate_data: list[Heartrate] = []

    @staticmethod
    def parse(data: dict[str, Any]) -> Activity:
        return Activity(
            id=data["id"],
            name=data["name"],
            type=ActivityType.parse(data["type"]),
            start_datetime=dateutil.parser.parse(data["start_date_local"]),
            duration=timedelta(seconds=data["elapsed_time"]),
            has_heartrate=data["has_heartrate"],
        )


class DistributionBucket(BaseModel):
    """A Strava zone distribution bucket."""

    # zone minimum
    min: float
    # zone maximum
    max: float
    # zone time
    time: float


class ZoneData(BaseModel):
    """Strava zone data."""

    # the type of the zone data
    type: str
    # the distribution buckets for the zone data
    distribution_buckets: list[DistributionBucket]


class Strava:
    """A Strava API client."""

    def __init__(self, *, access_token: str) -> None:
        self.access_token = access_token

    def _header(self) -> dict[str, str]:
        """Get the header for making requests."""
        return {"Authorization": "Bearer " + self.access_token}

    @staticmethod
    def from_env() -> Strava:
        client_id, client_secret, refresh_token = _read_env()
        return Strava.from_auth(client_id, client_secret, refresh_token)

    @staticmethod
    def from_auth(
        client_id: str, client_secret: str, refresh_token: str
    ) -> Strava:
        """Construct a Strava instance from persistent client authentication details."""
        payload = {
            "client_id": f"{client_id}",
            "client_secret": f"{client_secret}",
            "refresh_token": f"{refresh_token}",
            "grant_type": "refresh_token",
            "f": "json",
        }
        token_object = requests.post(
            "https://www.strava.com/oauth/token", data=payload
        )
        access_token = token_object.json()["access_token"]
        return Strava(access_token=access_token)

    def last_week(
        self, per_page: int = 16, enrich_heartrate: bool = True
    ) -> list[Activity]:
        """
        Fetch activities for the last week.
        :param per_page: The number of results to include per page
        :param enrich_heartrate: Whether or not to enrich with heartrate data, if available
        :return: The activities
        """
        end = datetime.now()
        beg = datetime.now() - timedelta(days=7)
        return self.activities(beg, end, per_page, enrich_heartrate)

    def activities(
        self,
        begin: datetime,
        end: datetime,
        per_page: int = 16,
        enrich_heartrate: bool = True,
    ) -> list[Activity]:
        """
        Fetch activities within a date range. This function handles pagination if the
        range includes more activities than will fit in a single page.

        :param begin: The start of the range
        :param end: The end of the range
        :param per_page: The number of results to include per page
        :param enrich_heartrate: Whether or not to enrich with heartrate data, if available
        :return: The activities
        """
        # the complete set of activities we query
        activities: list[Activity] = []

        page = 1
        while True:
            next_page = self._fetch_activites_page(begin, end, page, per_page)
            activities.extend(next_page)

            # determine if we have fetched all activities in range
            if len(next_page) < per_page:
                break

            page += 1

        if enrich_heartrate:
            activities = [
                (
                    self._enrich_activity_with_heartrate(a)
                    if a.has_heartrate
                    else a
                )
                for a in activities
            ]

        # sort in ascending chronological order
        return sorted(activities, key=lambda a: a.start_datetime)

    def _fetch_activites_page(
        self, begin: datetime, end: datetime, page: int, per_page: int
    ) -> list[Activity]:
        """
        Fetch a single page of activities.
        :param begin: The start of the range
        :param end: The end of the range
        :param per_page: The number of results to include per page
        """
        response = requests.get(
            "https://www.strava.com/api/v3/activities",
            headers=self._header(),
            params={
                "per_page": f"{per_page}",
                "page": f"{page}",
                "after": f"{begin.timestamp()}",
                "before": f"{end.timestamp()}",
            },
        ).json()
        return [Activity.parse(element) for element in response]

    def _enrich_activity_with_heartrate(self, activity: Activity) -> Activity:
        """
        Enrich an activity with zones data.
        :param activity: The input activity
        :return: The enriched activity
        """
        if not activity.has_heartrate:
            raise ValueError("activity does not provide heartrate data")

        # request zone data for the activity
        response = requests.get(
            f"https://www.strava.com/api/v3/activities/{activity.id}/zones",
            headers=self._header(),
        ).json()

        # parse and validate the response
        parsed = [ZoneData.model_validate(item) for item in response]

        # convert zones
        for data in parsed:
            match data.type:
                case "heartrate":
                    raw = [
                        Heartrate(
                            min=int(item.min),
                            max=int(item.max),
                            time=timedelta(seconds=item.time),
                        )
                        for item in data.distribution_buckets
                    ]
                    # sort in ascending order of heartrate
                    activity.heartrate_data = sorted(raw, key=lambda h: h.min)
                    # add identifiers
                    for i, hr in enumerate(activity.heartrate_data):
                        hr.id = f"z{i + 1}"
                case _:
                    continue

        return activity


def _read_env() -> tuple[str, str, str]:
    """Read required environment variables."""
    return (
        os.getenv("CLIENT_ID", ""),
        os.getenv("CLIENT_SECRET", ""),
        os.getenv("REFRESH_TOKEN", ""),
    )
