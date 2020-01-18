import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv


def urljoin(*args):
    """
    Joins given arguments into an url. Trailing but not leading slashes are
    stripped for each argument.
    """

    return "/".join(map(lambda x: str(x).rstrip('/'), args))


def getEnvVar(var_name):
    """
    fetches an environment variable or raises an exception if not found
    """
    val = os.getenv(var_name)
    if not val:
        raise Exception(f"can't find envvar {var_name}")
    return val


def fetchJWT(username, password, appid, base_url):
    """
    fetches a JWT from the glowmarkt API

    Requires:
        username: at glowmarkt
        password: at glowmarkt
        appid: from dev documentation
        base_url: of the API
    
    returns:
        JWT - issued token
        expiry - unix timestamp of the token's expiry
    """
    credentials = {"username": username, "password": password}
    headers = {"applicationId": appid,
               "Content-Type": "application/json"}
    response = requests.post(urljoin(base_url, "auth"), data=json.dumps(credentials), headers=headers)
    if not response.ok:
        raise Exception(
            f"Didn't get HTTP 200 (OK) response - status_code from server: {response.status_code}\n{response.text}")
    return response.json()["token"], response.json()["exp"]


def get_resources(jwt, appid, base_url):
    headers = {"applicationId": appid,
               "Content-Type": "application/json",
               "token": jwt}
    response = requests.get(urljoin(base_url, "resource"), headers=headers)
    if not response.ok:
        raise Exception(
            f"Didn't get HTTP 200 (OK) response - status_code from server: {response.status_code}\n{response.text}")
    return response.json()


def get_data_for_range(jwt, appid, uri, resource_id, start, end, period):
    headers = {"applicationId": appid,
               "Content-Type": "application/json",
               "token": jwt}


    query_url = urljoin(uri, "resource", resource_id, "readings")

    start_time = datetime.utcfromtimestamp(start)
    end_time = datetime.utcfromtimestamp(end)

    params = {
              "to": end_time.isoformat(),
              "from": start_time.isoformat(),
              "period": period,
              "function": "sum"}
    response=requests.get(query_url, headers=headers, params=params)
    if not response.ok:
        raise Exception(
            f"Didn't get HTTP 200 (OK) response - status_code from server: {response.status_code}\n{response.text}")
    return response.json()

    # get config
load_dotenv()
gm_username = getEnvVar("GM_USERNAME")
gm_password = getEnvVar("GM_PASSWORD")
gm_appid = getEnvVar("GM_APPID")
api_root = "https://api.glowmarkt.com/api/v0-1/"

def fetch_data_for_first_time():
    jwt, expiry = fetchJWT(gm_username, gm_password, gm_appid, api_root)
    resources = get_resources(jwt, gm_appid, api_root)
    # need to iterate through the data types in the response
    # then work backwards at highest granularity until there are no more responses

    print(get_data_for_range(jwt, gm_appid, api_root, "1dd27b2f-46eb-4cd0-8125-ec104393cc99",
                    1579261478, 1579361478, "PT1M"))
