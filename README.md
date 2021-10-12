# fortcollinsconnexionmapper

## what is this?
I have been waiting for my home to become available for Connexion, so I created a way to query for the status of all of the homes in a subdivision.

**Prerequisites**

Your subdivision name.  Enter an address here and click on the property to show the proper subdivision name.
https://www.larimer.org/assessor/search#/property/

You will need a Google maps API key.  There is no cost for this as long as you don't go over several thousand lookups in a month.  
https://console.cloud.google.com/apis/library/geocoding-backend.googleapis.com?project=fort-collins-connexion-map

Place the API key in a file named .gmaps_key

Make sure to install the dependencies that are defined in the requirements.txt file

Run create_map.py