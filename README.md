# Historian Data Compression

Historian Data Compression is a Python library used to compress historian data, using the deadband and/or swinging door algorithm.
Historian data are typically 2 dataframe columns, one with a timestamp and one with a logged value.

## Project description

Based on the [swinging door library](https://pypi.org/project/swinging-door/) of [Aleksandr F. Mikhaylov (ChelAxe)](mailto:chelaxe@gmail.com).
The default for the extra timeout parameter is 0, which actually means 'no timeout'.

The swinging door algorithm is clearly explained in this [presentation](https://slideplayer.com/slide/3884/),
this [animation](https://www.youtube.com/watch?v=fdH7dYTN7gM) ('exception' == 'deadband compression' & 'compression' == 'swinging door compression'),
and in this [file](https://spiral.imperial.ac.uk/bitstream/10044/1/14604/2/ThornhillEtAlCompressionJPC2004.pdf).

## Installation

Use the package manager [pip](https://pypi.org/project/historian-data-compression/) to install historian_data_compression.

```bash
pip install historian_data_compression
```

## Usage

To avoid timestamp issues:

   1.  sort the dateframe by timestamp,
   2.  and convert negative timestamps (in Windows, dates before 1970-01-01) by adding a number of seconds before the compression, and deducting again afterwards.

## Simple demo (dataframe with 1 significant value column)

``` {.python}
import pandas as pd
from datetime import datetime, timedelta
from historian_data_compression import point_generator, dead_band_compression, swinging_door_compression

df = pd.read_csv(r"https://datahub.io/core/natural-gas/r/daily.csv")
df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d %H:%M:%S")

df = df.sort_values("Date")
first_ts = df["Date"].min().timestamp()
if first_ts < 0:
    df["Date"] = df["Date"] + timedelta(seconds=int(first_ts))

max = df["Price"].max()
min = df["Price"].min()
dbc_deadband_perc = 0.5                                                                             # typically 0.5 %
dbc_deviation = dbc_deadband_perc / 100 * (max - min) / 2                                           # deviation = deadband / 2
dbc_timeout = 0                                                                                     # seconds, but 0 eauals 'no timeout'
swdc_deadband_perc = 1                                                                              # typically 1.0 %
swdc_deviation = swdc_deadband_perc / 100  * (max - min) / 2     
swdc_timeout = 0                                                                                    # seconds, but 0 eauals 'no timeout'

df_dbc = pd.DataFrame(
    tuple(
        {
            "Date": datetime.fromtimestamp(ts),
            "Price": value
        }
        for ts, value in dead_band_compression(
            point_generator(df[["Date", "Price"]]), deviation=dbc_deviation, timeout=dbc_timeout
        )
    )
)
df_dbc_swdc = pd.DataFrame(
    tuple(
        {
            "Date": datetime.fromtimestamp(ts),
            "Price": value
        }
        for ts, value in swinging_door_compression(
            point_generator(df_dbc), deviation=swdc_deviation, timeout=swdc_timeout
        )
    )
)
if first_ts < 0:
    df_dbc["Date"] = df_dbc["Date"] - timedelta(seconds=int(first_ts))
    df_dbc_swdc["Date"] = df_dbc_swdc["Date"] - timedelta(seconds=int(first_ts))
print(
      "Size after 1st stage compression (deadband only):           "
      f"{len(df_dbc) / len(df):>10.1%}"
)
print(
      "Size after 2nd stage compression (deadband + swinging door):"
      f"{len(df_dbc_swdc) / len(df):>10.1%}"
)

# returns:

Size after 1st stage compression (deadband only):                84.7%
Size after 2nd stage compression (deadband + swinging door):     26.8%

```

## Example with dataframe with multiple significant value columns

``` {.python}

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

# returns:

Size after swinging door compression:                39.9%

```

## License
[MIT](https://choosealicense.com/licenses/mit/)