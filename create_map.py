#!/usr/bin/python
''' 
This script will create an interactive map to determine your subdivision's availablity for
Fort Collins Connexion

Simon Branton-Housley
simonbh@gmail.com
'''
# import the library and its Marker clusterization service
import requests
import urllib.parse
import time
import json
import googlemaps
import folium
import plotly.express as px
import sqlite3
from sqlite3 import Error
from folium.map import Marker
from folium.plugins import MarkerCluster
from requests.models import encode_multipart_formdata
from halo import Halo

# Variables
db_file="address_data.db"
fCGovLookupAddress='https://www.fcgov.com/connexion/address-service.php?address='
LarimerCountyPropertyLookupURI='https://apps.larimer.org/api/assessor/property/?prop=property&parcel=undefined&scheduleNumber=undefined&serialIdentification=undefined&name=undefined&fromAddrNum=undefined&toAddrNum=undefined&address=undefined&city=Any&subdivisionNumber=undefined&sales=any&subdivisionName='
# Determine your subdivision name from here:
# https://www.larimer.org/assessor/search#/property/
SubdivisionName='GOLDEN MEADOWS'
#SubdivisionName='SOUTHMOOR VILLAGE EAST'
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

def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        #print(sqlite3.version)
    except Error as e:
        print(e)
    
    return conn

def create_tables(conn):
    #FullAddress,StreetNumber,StreetName,Availability,Longitude,Latitude
    sql_create_address_table = """ CREATE TABLE IF NOT EXISTS addresses (
                                        id INTEGER PRIMARY KEY,
                                        FullAddress TEXT NOT NULL,
                                        StreetNumber INTEGER,
                                        StreetName text,
                                        Availability INTEGER,
                                        Longitude REAL,
                                        Latitude REAL
                                    ); """
    try:
        cur = conn.cursor()
        cur.execute(sql_create_address_table)
    except Error as e:
        print(e)

@Halo(text='Obtaining addresses from subdivision name', spinner='dots')
def obtain_addresses_from_subdivision_name(conn):
    ''' 
    Get the subdivision addresses if addresses table is empty
    '''
    try:
        cur = conn.cursor()
        cur.execute(''' SELECT Count(*) FROM addresses ''')
        has_data = cur.fetchall()
    except Error as e:
        print(e)

    if has_data[0][0] == 0:
        r = requests.get(LarimerCountyPropertyLookupURI + urllib.parse.quote(SubdivisionName))
        subdivisionRecords=json.loads(r.text)

        for x in range(len(subdivisionRecords["records"])):
            raw_address=subdivisionRecords["records"][x]["locationaddress"]
            if not raw_address:
                print()
            else:
                # I want to print the final results that are sorted by street name versus house number, 
                # so I am splitting the raw_address into 2 parts, and will store the two parts in the
                # nested dictionary for later use
                SplitAddress = raw_address.split(' ', 1)
                conn.execute('''INSERT INTO addresses (FullAddress, StreetNumber, StreetName, Availability) VALUES (?, ?, ?, 0) ''', (raw_address, SplitAddress[0], SplitAddress[1]) )
                conn.commit()

@Halo(text='Performing geoloacation on addresses', spinner='dots')
def geolocate_data(conn):
    '''
    If the address does not have a value for Longitude and/or Latitude, use Google's API to obtain this data and insert into the DB
    '''
    try:
        cur = conn.cursor()
        cur.execute(''' SELECT * from addresses WHERE Longitude is NULL or Latitude is NULL; ''')
        items = cur.fetchall()
        for item in items:
            full_address = item[1]
            geocode_result = gmaps.geocode( full_address + ", Fort Collins, CO" )
            
            lng = geocode_result[0]['geometry']['location']['lng']
            lat = geocode_result[0]['geometry']['location']['lat']
            
            cur.execute(''' UPDATE addresses SET Longitude = ?, Latitude = ? WHERE FullAddress = ?; ''', ( lng, lat, full_address ) )
            conn.commit()
    except sqlite3.Error as error:
        print("Failed to read data from sqlite table", error)

@Halo(text='Performing service availability check', spinner='dots')
def check_address_availability(conn):
    '''
    This checks the address against the fcgov API to determine availablity
    In progress
    '''
    try:
        cur = conn.cursor()
        cur.execute(''' SELECT * from addresses; ''')
        items = cur.fetchall()
        
        for item in items:
            full_address = item[1]
            
            if not full_address:
                print()
            else:
                # the address that is submitted to the API must be URL encoded
                formatted_address=urllib.parse.quote(full_address)
                
                url = 'https://www.fcgov.com/connexion/address-service.php?address=%s' % formatted_address
                # The fcgov endpoint will not return values if you don't send headers.  I didn't investigate to determine which headers matter and 
                # which do not.
                r = requests.get(url, headers=headers)

                # As to not hammer the API endpoint
                #time.sleep(1)
                raw_response=r.text
                # The response is a JSON object.  We must load that for further processing
                json_response=json.loads(raw_response)
                # If the length of the json reponse is 1, then there was an error.
                if len(json_response) == 1:
                    print( "\n" + full_address + " not found\n" )
                else:
                    service_status = json_response["service_status"]

                    if "In Construction" in service_status:
                        insert_string = 'UPDATE addresses SET Availability = 0 WHERE FullAddress = "{}";'.format( full_address )
                        cur.execute( insert_string )
                        conn.commit()
                        
                    elif "Available" in service_status:
                        insert_string = 'UPDATE addresses SET Availability = 1 WHERE FullAddress = "{}";'.format( full_address )
                        cur.execute( insert_string )
                        conn.commit()
                        
                    elif "Planning" in service_status:
                        insert_string = 'UPDATE addresses SET Availability = 2 WHERE FullAddress = "{}";'.format( full_address )
                        cur.execute( insert_string )
                        conn.commit()
                        
                    else:
                        print(formatted_address + " Unknown response")
                        print(service_status)
           
        cur.close()
    except sqlite3.Error as error:
        print("Failed to update Availability in address table \n", error)    

def average_long_lat(conn):
    cur = conn.cursor()
    
    cur.execute(''' SELECT avg(Longitude) FROM addresses; ''')
    avgLong = cur.fetchall()

    cur.execute(''' SELECT avg(Latitude) FROM addresses; ''')
    avgLat = cur.fetchall()
        
    return avgLong, avgLat

@Halo(text='Creating map', spinner='dots')
def create_map(conn):
    avgLong,avgLat = average_long_lat(conn)

    avgLong = avgLong[0][0]
    avgLat = avgLat[0][0]

    # Create a map object and center it to the avarage coordinates to m
    my_map = folium.Map(location=(avgLat,avgLong), zoom_start=17)

    try:
        cur = conn.cursor()
        cur.execute(''' SELECT FullAddress, Availability, Latitude, Longitude FROM addresses; ''')
        
        items = cur.fetchall()
        for item in items:
            full_address = item[0]
            Availability = item[1]
            latitude = item[2]
            longitude = item[3] 
            location = (latitude, longitude)
            if Availability == 0:
                folium.Marker(location=location,
                            popup = full_address,
                            icon=folium.Icon(prefix='fa',icon="fa-frown-o",color="red")
                ).add_to(my_map)
            elif Availability == 1:
                folium.Marker(location=location,
                            popup = full_address,
                            icon=folium.Icon(prefix='fa',icon="fa-smile-o",color="green")
                ).add_to(my_map)
            elif Availability == 2:
                folium.Marker(location=location,
                            popup = full_address,
                            icon=folium.Icon(prefix='fa',icon="fa-smile-o",color="yellow")
                ).add_to(my_map)
            else:
                folium.Marker(location=location,
                            popup = full_address,
                            icon=folium.Icon(prefix='fa',icon="fa-question-circle-o",color="purple")
                ).add_to(my_map)
            
        cur.close()
        my_map.save("map.html")

    except sqlite3.Error as error:
        print("Failed to read data from sqlite table", error)

    return my_map

def main():
    conn = create_connection(db_file)
    create_tables(conn)
    obtain_addresses_from_subdivision_name(conn)
    geolocate_data(conn)
    check_address_availability(conn)
    create_map(conn)
    conn.close

if __name__ == '__main__':
    main()