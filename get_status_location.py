#!/usr/bin/python
''' 
This script will pull all of the address for a neighborhood and then
check on the the Fort Collins Connexion installion readyness status.

Simon Branton-Housley
simonbh@gmail.com
'''
import requests
import json
import urllib.parse
import time
import googlemaps
import csv
import datetime

from requests.models import encode_multipart_formdata

# Variables
fCGovLookupAddress='https://www.fcgov.com/connexion/address-service.php?address='
LarimerCountyNeighboorhoodLookupAddress='https://apps.larimer.org/api/assessor/property/?prop=property&parcel=undefined&scheduleNumber=undefined&serialIdentification=undefined&name=undefined&fromAddrNum=undefined&toAddrNum=undefined&address=undefined&city=Any&subdivisionNumber=undefined&sales=any&subdivisionName='
# Your neighboorhoor name needs to be URL encoded, example below
#NeighboorhoodName='GOLDEN%20MEADOWS'
NeighboorhoodName=''
headers={
        "Host": "www.fcgov.com", \
        "Sec-Ch-Ua": '\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"93\"', \
        "Accept": "application/json, text/javascript, */* q=0.01", \
        "X-Requested-With": "XMLHttpRequest", \
        "Sec-Ch-Ua-Mobile": "?0", \
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36", \
        "Sec-Fetch-Site": "same-origin", \
        "Sec-Fetch-Mode": "cors", \
        "Sec-Fetch-Dest": "empty", \
        "Referer": "https://www.fcgov.com/connexion/", \
        "Accept-Encoding": "gzip, deflate", \
        "Accept-Language": "en-US,en;q=0.9"
        }
gmapsKey = open(".gmaps_key").read()
gmaps = googlemaps.Client(key=gmapsKey)
TodayDateTime=datetime.datetime.now().isoformat()

# Initalize dictionary to store results
ResultsDict = {}

# Debug values - Normally not used
#breaker = 0
#breakValue = 6

r = requests.get(LarimerCountyNeighboorhoodLookupAddress + NeighboorhoodName)
neighborhoodRecords=json.loads(r.text)

# Prepare CSV file to store results for mapping
filename="results_%s.csv" % TodayDateTime
fieldnames = ['FullAddress','StreetNumber','StreetName','Availability','Longitude','Latitude']
with open(filename, 'w', newline='') as csvfile:
    listWriter = csv.DictWriter(csvfile,fieldnames=fieldnames)
    listWriter.writeheader()

    for x in range(len(neighborhoodRecords["records"])):
        raw_address=neighborhoodRecords["records"][x]["locationaddress"]
        if not raw_address:
            print()
        else:
            # the address that is submitted to the API must be URL encoded
            formatted_address=urllib.parse.quote(raw_address)
            
            url = 'https://www.fcgov.com/connexion/address-service.php?address=%s' % formatted_address
            # The fcgov endpoint will not return values if you don't send headers.  I didn't investigate to determine which headers matter and 
            # which do not.
            r = requests.get(url, headers=headers)
    
            # As to not hammer the API endpoint
            time.sleep(1)
            raw_response=r.text
            #print(raw_address)
            # The response is a JSON object.  We must load that for further processing
            json_response=json.loads(raw_response)
            # I want to print the final results that are sorted by street name versus house number, 
            # so I am splitting the raw_address into 2 parts, and will store the two parts in the
            # nested dictionary for later use
            SplitAddress = raw_address.split(' ', 1)
            if "In Construction" in json_response["service_status"]:            
                ResultsDict[raw_address]=dict(
                                            StreetNumber=SplitAddress[0], 
                                            StreetName=SplitAddress[1], 
                                            Status='In Construction'
                                            )
                geocode_result = gmaps.geocode(json_response["address"])
    
                listWriter.writerow({
                    'FullAddress': raw_address,
                    'StreetNumber': SplitAddress[0], 
                    'StreetName': SplitAddress[1], 
                    'Availability': 'N',
                    'Longitude': geocode_result[0]['geometry']['location']['lng'],
                    'Latitude': geocode_result[0]['geometry']['location']['lat']
                })
    
                ## DEBUGGING            
                # breaker+=1
                # if breaker == breakValue:
                #     break
            
            elif "Available" in json_response["service_status"]:
                ResultsDict[raw_address]=dict(
                                            StreetNumber=SplitAddress[0], 
                                            StreetName=SplitAddress[1], 
                                            Status='Available'
                                        )
                geocode_result = gmaps.geocode(json_response["address"])
    
                listWriter.writerow({
                    'FullAddress': raw_address,
                    'StreetNumber': SplitAddress[0], 
                    'StreetName': SplitAddress[1], 
                    'Availability': 'Y',
                    'Longitude': geocode_result[0]['geometry']['location']['lng'],
                    'Latitude': geocode_result[0]['geometry']['location']['lat']
                })
            else:
                print(raw_address + " Unknown response")
                print(json_response["service_status"])
                ResultsDict[raw_address]=dict(
                                            StreetNumber=SplitAddress[0], 
                                            StreetName=SplitAddress[1], 
                                            Status='Unknown'
                                            )
                geocode_result = gmaps.geocode(json_response["address"])
    
                listWriter.writerow({
                    'FullAddress': raw_address,
                    'StreetNumber': SplitAddress[0], 
                    'StreetName': SplitAddress[1], 
                    'Availability': 'X',
                    'Longitude': geocode_result[0]['geometry']['location']['lng'],
                    'Latitude': geocode_result[0]['geometry']['location']['lat']
                })

# I want to sort the final dictionary based on the street name so that it is easier to view the results
SortedResultsDict = dict(sorted(ResultsDict.items(), key = lambda x: x[1]['StreetName']))
# Print the results.  Since SortedResultsDict is a nested dictionary, I need to iterate through the 
# dictionary and print just the values of the nested dictionary
for key in SortedResultsDict.keys():
    result=" ".join(str(value) for key, value in SortedResultsDict[key].items())
    print(result)
