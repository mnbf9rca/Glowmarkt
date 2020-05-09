# very basic glowmarkt API wrapper for python

implements https://docs.glowmarkt.com/GlowmarktApiDataRetrievalDocumentationIndividualUser.pdf

## Installation

requires python 3.6+, requests, python-dotenv
store credentials in .env file (use `.env.template` as a template) or use env

## usage

main.py shows how to call it to retrieve your data:

1. create new glow() object with credentials (it'll connect to validate them)
1. retrieve available resource IDs with `get_resources`
1. get data for a resource using `get_data_for_range`

the glow.Aggregations enum gives available periods to query for