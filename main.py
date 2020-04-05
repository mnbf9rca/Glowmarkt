from glow import glow
from helpers import getEnvVar
from dotenv import load_dotenv
import time


# get config
load_dotenv()
gm_username = getEnvVar("GM_USERNAME")
gm_password = getEnvVar("GM_PASSWORD")
gm_appid = getEnvVar("GM_APPID")


g = glow(appid=gm_appid, username=gm_username, password=gm_password)

resources = g.get_resources()
for r in resources:
    resourceID = r['resourceId']
    print(resourceID)
    seconds_in_one_day = 60*60*24
    
    result = g.get_data_for_range(resource_id=resourceID,start=(int)(time.time()-(10*seconds_in_one_day)), end=(int)(time.time()),period=glow.Aggregations.PT30M)
    print(type(result))
    print(result)

# need to iterate through the data types in the response
# then work backwards at highest granularity until there are no more responses

# print(get_data_for_range(jwt, gm_appid, api_root, "1dd27b2f-46eb-4cd0-8125-ec104393cc99",
#                            1579261478, 1579361478, "PT1M"))
