# -*- coding: utf-8 -*-

"""
Avoid timestamp issues!

    1. sort the dateframe by timestamp
    2. convert negative timestamps in Windows (dates before 1970-01-01)
    
"""

import pandas as pd
from datetime import datetime
from historian_data_compression import point_generator, swinging_door_compression

df = pd.read_csv(r"https://datahub.io/core/global-temp/r/monthly.csv")
df = pd.pivot(df, index=["Date"], columns=["Source"], values=["Mean"])
df = df.reset_index(drop=False)
df.columns = [c[1] if c[0] == "Mean" else "Date" for c in df.columns ]
df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d %H:%M:%S")
cols_float = [c for c in df.columns if df[c].dtype == "float"]
df = df.sort_values("Date")
days = (datetime(1970, 1, 1) - df.loc[0, "Date"]).total_seconds() / (60 * 60 * 24)
if days > 0:
    days =  int(days) + 100
else:
    days = 0
df["Date"] = df["Date"] + pd.Timedelta(days=days)

ix = pd.date_range(start=df["Date"].min(), end=df["Date"].max(), freq='D')
df1 = df.set_index('Date')
df1 = df1.reindex(ix).reset_index(drop=False)
df1.columns = ["Date"] + cols_float


tol = pd.Timedelta("0.5 days")
    
for col in cols_float:
    max = df[col].max()
    min = df[col].min()
    swdc_deadband_perc = 5                                                                          # typically 1.0 %
    swdc_deviation = swdc_deadband_perc / 100 * (max - min) / 2     
    swdc_timeout = 0                                                                                # seconds, but 0 eauals 'no timeout'
    
    df_swdc = pd.DataFrame(
        tuple(
            {
                "Date": datetime.fromtimestamp(ts),
                col: value
            }
            for ts, value in swinging_door_compression(
                point_generator(df[["Date", col]]), deviation=swdc_deviation, timeout=swdc_timeout
            )
        )
    )
    df1 = pd.merge_asof(df1, df_swdc, on="Date", direction="nearest", tolerance=tol, suffixes=["", "_compressed"])
if days > 0:
    df1["Date"] = df1["Date"] - pd.Timedelta(days=days)

df_swdc = df1.dropna(thresh=2).reset_index(drop=True)

df_swdc.plot(x="Date", y="GISTEMP")
df_swdc.plot(x="Date", y="GISTEMP_compressed")

print(
      "Size after swinging door compression:           "
      f'{df_swdc["GISTEMP_compressed"].count() / df_swdc["GISTEMP"].count():>10.1%}'
)