import os
from pprint import pprint
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS


url    = "https://influx.tyjch.dev"
token  = "kUNmtpW-LSDs3dTAznFaZJ5a5qWv7TbYch3O5wzflprsl0L3sGMZ_ZQ6ADQ5BuvkzLNl0sFJAD8LDeIUsrwpBw=="
org    = "AspenCircle"
bucket = "thermometer"


client = influxdb_client.InfluxDBClient(
   url   = url,
   token = token,
   org   = org
)

api = client.write_api(write_options=SYNCHRONOUS)

p = influxdb_client.Point("my_measurement").tag("location", "Prague").field("temperature", 25.3)
api.write(bucket=bucket, org=org, record=p)
