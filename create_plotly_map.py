#!/usr/bin/python

# Starting Plotly process
import plotly
import plotly.express as px
import pandas as pd

# Variables
file_name="results_2021-09-21T22:20:53.507792.csv"
## You need a mapbox API token
mapbox_access_token = open(".mapbox_token").read()

df = pd.read_csv(file_name)
df["FullAddress"] = df["FullAddress"].astype(str)
df["Latitude"] = df["Latitude"].astype(float)
df["Longitude"] = df["Longitude"].astype(float)

#df1 = df[['FullAddress', 'Latitude', 'Longitude']].copy()

fig = px.scatter_mapbox(df, hover_name='FullAddress',
                            lat='Latitude',
                            lon='Longitude',
                            zoom=16
                        )
#fig.update_layout(mapbox_style="dark")
fig.update_layout(mapbox_style="open-street-map")

#fig.show()
plotly.offline.plot(fig, filename=r'plotly_map.html')