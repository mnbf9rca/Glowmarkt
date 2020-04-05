# glow api for Hildebrand Glow
# (c) 2020 Robert Aleck / mnbf9rca
# https://github.com/mnbf9rca/Glowmarkt
#
# issued under MIT License
#

from enum import Enum
import requests
import json
import time
from datetime import datetime, timedelta
from helpers import getEnvVar, urljoin


class glow:
    class Aggregations(Enum):
        PT1M = "PT1M"    # minute level, only elec
        PT30M = "PT30M"  # 30 minute level
        PT1H = "PT1H"    # hour level
        P1D = "P1D"      # day level
        P1W = "P1W"      # week level, starting Monday
        P1M = "P1M"      # month level
        P1Y = "P1Y"      # year level

    def __init__(self,
                 appid,
                 username,
                 password):
        '''
        Creates a glow class for interacting with the glow API

        Args:
            appod:      App ID issued by glowmarkt. One AppID for all for now.
            username:   username for glowmarkt API
            password:   password for glowmarkt API
        '''
        self._username = username
        self._password = password
        self._appid = appid
        self._api_root = "https://api.glowmarkt.com/"
        self._cached_jwt_expiry = time.time()
        self._cached_jwt_token = self._fetchJWT()
        super().__init__()

    def _fetchJWT(self) -> str:
        """
        fetches a JWT from the glowmarkt API. If the current token is still valid, returns it. If it's due to expire soon, refreshes it.

        returns:
            JWT - issued token
            expiry - unix timestamp of the token's expiry
        """
        if self._cached_jwt_expiry <= time.time():
            credentials = {"username": self._username, "password": self._password}
            headers = {"applicationId": self._appid,
                       "Content-Type": "application/json"}
            response = requests.post(urljoin(self._api_root, "api/v0-1/auth"),
                                     data=json.dumps(credentials), headers=headers)
            if not response.ok:
                raise Exception(
                    f"Didn't get HTTP 200 (OK) response - status_code from server: {response.status_code}\n{response.text}")
            self._cached_jwt_token = response.json()["token"]
            self._cached_jwt_expiry = response.json()["exp"]
        return self._cached_jwt_token

    def get_resources(self) -> dict:
        headers = {"applicationId": self._appid,
                   "Content-Type": "application/json",
                   "token": self._fetchJWT()}
        response = requests.get(urljoin(self._api_root, "api/v0-1/resource"), headers=headers)
        if not response.ok:
            raise Exception(
                f"Didn't get HTTP 200 (OK) response - status_code from server: {response.status_code}\n{response.text}")
        return response.json()

    def get_data_for_range(self, resource_id: str, start: int, end: int, period: Aggregations) -> dict:
        '''
        Desc:
            fetches the data for a given range at a given periodicity
        Args:
            resource_id:    a valid resourceId for this account
            start:          earliest datetime to receive for, in UTC. Expects unix(posix) timestamp
            end:            latest datetime to receive for, in UTC. Expects unix(posix) timestamp
            Period:         The aggregation level in which the data is to be returned (ISO 8601)
                                PT1M (minute level, only elec)
                                PT30M (30 minute level)
                                PT1H (hour level)
                                P1D (day level)
                                P1W (week level, starting Monday)
                                P1M (month level)
                                P1Y (year level)
        '''
        headers = {"applicationId": self._appid,
                   "Content-Type": "application/json",
                   "token": self._fetchJWT()}

        query_url = urljoin(self._api_root, "api/v0-1/resource", resource_id, "readings")

        start_time = datetime.utcfromtimestamp(start)
        end_time = datetime.utcfromtimestamp(end)

        # quickly check if they've passed an enum - get the value otherwise assume it's a string
        period = period.value if isinstance(period, self.Aggregations) else period

        params = {
            "to": end_time.isoformat(),
            "from": start_time.isoformat(),
            "period": period,
            "offset": 0,
            "function": "sum"}
        print("params", params)
        response = requests.get(query_url, headers=headers, params=params)
        if not response.ok:
            raise Exception(
                f"Didn't get HTTP 200 (OK) response - status_code from server: {response.status_code}\n{response.text}")
        return response.json()
