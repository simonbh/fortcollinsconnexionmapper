#!/usr/bin/python
''' 
This script will create a folium map from your csv file

Simon Branton-Housley
simonbh@gmail.com
'''
# import the library and its Marker clusterization service
from folium.map import Marker
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import plotly.express as px

# Variables
file_name="results_2021-09-21T22:20:53.507792.csv"

df = pd.read_csv(file_name)

# Create a map object and center it to the avarage coordinates to m
m = folium.Map(location=df[["Latitude", "Longitude"]].mean().to_list(), zoom_start=17)

# if the points are too close to each other, cluster them, create a cluster overlay with MarkerCluster, add to m
#marker_cluster = MarkerCluster().add_to(m)

for i,r in df.iterrows():
    location = (r["Latitude"], r["Longitude"])
    if r["Availability"] == 'N':
        folium.Marker(location=location,
                          popup = r["FullAddress"],
                          icon=folium.Icon(prefix='fa',icon="fa-frown-o",color="red")
        ).add_to(m)

    elif r["Availability"] == 'Y':
        folium.Marker(location=location,
                          popup = r["FullAddress"],
                          icon=folium.Icon(prefix='fa',icon="fa-smile-o",color="green")
        ).add_to(m)
    else:
        folium.Marker(location=location,
                          popup = r["FullAddress"],
                          icon=folium.Icon(prefix='fa',icon="fa-question-circle-o",color="purple")
        ).add_to(m)

m.save("folium_map.html")