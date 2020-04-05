# glow api for Hildebrand Glow
# (c) 2020 Robert Aleck / mnbf9rca
# https://github.com/mnbf9rca/Glowmarkt
#
# issued under MIT License
#

import requests
import json
import time
import logging
from datetime import datetime, timedelta
from enum import Enum
from helpers import getEnvVar, urljoin


class glow:
    def __init__(self,
                 appid: str,
                 username: str,
                 password: str):
        '''Creates a glow class for interacting with the glow API

        Args:
            appid:      App ID issued by glowmarkt. One AppID for all for now.
            username:   username for glowmarkt API
            password:   password for glowmarkt API

        Returns:
            None
        '''
        self._username = username
        self._password = password
        self._appid = appid
        self._api_root = "https://api.glowmarkt.com/"
        self._cached_jwt_expiry = time.time()
        self._cached_jwt_token = self._fetchJWT()

        super().__init__()

    class Aggregations(Enum):
        '''
        Aggregation period parameters.
        Enum returns the string value and query limit (in days)
        according to https://docs.glowmarkt.com/GlowmarktApiDataRetrievalDocumentationIndividualUser.pdf
        '''
        PT1M = {"period": "PT1M", "duration": 2}     # minute level only elec
        PT30M = {"period": "PT30M", "duration": 10}  # 30 minute level
        PT1H = {"period": "PT1H", "duration": 31}    # hour level
        P1D = {"period": "P1D", "duration": 31}      # day level
        P1W = {"period": "P1W", "duration": 42}      # week level, starting Monday
        P1M = {"period": "P1M", "duration": 366}     # month level
        P1Y = {"period": "P1Y", "duration": 366}     # year level

    def _fetchJWT(self) -> str:
        """
        fetches a JWT from the glowmarkt API. If the current token is still valid, returns it. If it's due to expire soon, refreshes it.

        Args:
            None

        Returns:
            JWT:    issued token

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
        '''
        Fetches all of the resources available for this account

        Args:
            None

        Returns:
            response from Glowmarkt
        '''
        headers = {"applicationId": self._appid,
                   "Content-Type": "application/json",
                   "token": self._fetchJWT()}
        response = requests.get(urljoin(self._api_root, "api/v0-1/resource"), headers=headers)
        if not response.ok:
            raise Exception(
                f"Didn't get HTTP 200 (OK) response - status_code from server: {response.status_code}\n{response.text}")
        return response.json()

    def get_data_for_range(self, resource_id: str, start: int, end: int, period: glow.Aggregations) -> list:
        '''
            fetches the data for a given range at a given periodicity. Returns a list of result sets. Automatically pages results.
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
        Returns:
            list[dict] a list of dict results sets returned by the server. Each resultset is a JSON object. Note the list may have 
            one member, however if hte duration exceeds maximum query size, mutliple results are returned in the list.
        '''
        headers = {"applicationId": self._appid,
                   "Content-Type": "application/json",
                   "token": self._fetchJWT()}

        query_url = urljoin(self._api_root, "api/v0-1/resource", resource_id, "readings")

        # quickly check if they've passed an enum - get the value otherwise assume it's a string
        if isinstance(period, self.Aggregations):
            query_page_size = period.value["duration"] * 24*60*60
            period = period.value["period"]
        else:
            # not an enum; take their start + end as valid
            query_page_size = end-start
        logging.info(
            f"inputs - start {start} ({datetime.utcfromtimestamp(start).isoformat()}), end {end} ({datetime.utcfromtimestamp(end).isoformat()}), query_page_size {query_page_size}, period {period}")

        resultset = []
        for page_start in range(start, end, query_page_size):
            params = {
                "to": datetime.utcfromtimestamp(min(page_start + query_page_size, end)).isoformat(),
                "from": datetime.utcfromtimestamp(page_start).isoformat(),
                "period": period,
                "offset": 0,
                "function": "sum"}
            response = requests.get(query_url, headers=headers, params=params)
            if not response.ok:
                raise Exception(
                    f"Didn't get HTTP 200 (OK) response - status_code from server: {response.status_code}\n{response.text}")
            resultset.append(response.json())
        return resultset
