import influxdb_client
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()

token = os.getenv("INFLUXDB_TOCKEN")
org = "urban-air-lab"
url = "https://influx.urbanairlab.hn"

query = '''
from(bucket: "ual-minute-calibration")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "calibration_data")
  |> filter(fn: (r) => r.topic == "sensors/calibration/ual-3")
  |> filter(fn: (r) => r._field == "RAW_OPC_Temperature")
  |> pivot(
      rowKey: ["_time"],
      columnKey: ["_field"],
      valueColumn: "_value"
  )
'''

with influxdb_client.InfluxDBClient(url=url, token=token, org=org) as client:
    query_api = client.query_api()
    data_frame = query_api.query_data_frame(query, org=org)

    if isinstance(data_frame, list):
        data_frame = (
            pd.concat(
                [frame for frame in data_frame if not frame.empty],
                ignore_index=True,
            )
            if any(not frame.empty for frame in data_frame)
            else pd.DataFrame()
        )

    if not data_frame.empty:
        data_frame = data_frame.rename(
            columns={"_time": "time", "RAW_OPC_Temperature": "temperature"}
        )

        if "temperature" in data_frame.columns:
            data_frame["temperature"] = pd.to_numeric(
                data_frame["temperature"], errors="coerce"
            )

        if "time" in data_frame.columns:
            data_frame["time"] = pd.to_datetime(
                data_frame["time"], errors="coerce", utc=True
            )
            data_frame = data_frame.sort_values("time").reset_index(drop=True)

    print(data_frame)
