# fortcollinsconnexionmapper

## what is this?
I have been waiting for my home to become available for Connexion, so I created a way to query for the status of all of the homes in a neighborhood.

**Prerequisites**

You will need a Google maps API key.  There is no cost for this as long as you don't go over several thousand lookups in a month.  
https://console.cloud.google.com/apis/library/geocoding-backend.googleapis.com?project=fort-collins-connexion-map

Place the API key in a file named .gmaps_key

## First step
Run the "create_plotly_map.py" file first, to create the csv file for your neighborhood.  This CSV file contains the house address (street number + street name), the service availablity, and the logitude and latitude of the house.

## Second step
Then run the "create_folium_map.py" file to generate the map.

### Some notes
The "create_ploty_map.py" is included.  This makes an offline map, but you will need a Mapbox API key (also free) placed in a file named .mapbox_token.

I could have combined these steps, but I wanted to experiment with different mapping tools, so I thought that this would be easier.
