#!/usr/bin/python
''' 
This script will create a folium map from your csv file

Simon Branton-Housley
simonbh@gmail.com
'''
# import the library and its Marker clusterization service
import requests
import urllib.parse
import time
import json
import datetime
import googlemaps
import pandas as pd
import folium
import plotly.express as px
import sqlite3
from sqlite3 import Error
from folium.map import Marker
from folium.plugins import MarkerCluster
from requests.models import encode_multipart_formdata

# Variables
db_file="address_data.db"
fCGovLookupAddress='https://www.fcgov.com/connexion/address-service.php?address='
LarimerCountyNeighboorhoodLookupAddress='https://apps.larimer.org/api/assessor/property/?prop=property&parcel=undefined&scheduleNumber=undefined&serialIdentification=undefined&name=undefined&fromAddrNum=undefined&toAddrNum=undefined&address=undefined&city=Any&subdivisionNumber=undefined&sales=any&subdivisionName='
# Your neighboorhoor name needs to be URL encoded, example below
#NeighboorhoodName='GOLDEN%20MEADOWS'
NeighboorhoodName='GOLDEN%20MEADOWS'
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


def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        #print(sqlite3.version)
    except Error as e:
        print(e)
    #finally:
    #    if conn:
    #        conn.close()

    return conn

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def obtain_addresses_from_neighborhood_name(conn):
    ''' 
    Get the neighborhood addresses if addresses table is empty
    '''
    try:
        cur = conn.cursor()
        cur.execute(''' SELECT Count(*) FROM addresses ''')
        has_data = cur.fetchall()
    except Error as e:
        print(e)

    if [has_data[0][0] == 0]:
        r = requests.get(LarimerCountyNeighboorhoodLookupAddress + NeighboorhoodName)
        neighborhoodRecords=json.loads(r.text)

        for x in range(len(neighborhoodRecords["records"])):
            raw_address=neighborhoodRecords["records"][x]["locationaddress"]
            if not raw_address:
                print()
            else:
                # I want to print the final results that are sorted by street name versus house number, 
                # so I am splitting the raw_address into 2 parts, and will store the two parts in the
                # nested dictionary for later use
                SplitAddress = raw_address.split(' ', 1)
                conn.execute('''INSERT INTO addresses (FullAddress, StreetNumber, StreetName, Availability) VALUES (?, ?, ?, 0) ''', (raw_address, SplitAddress[0], SplitAddress[1]) )
                conn.commit()
        for row in conn.execute(''' SELECT rowid, * FROM addresses '''):
            print(row)


def populate_addresses(conn, address):
    # Fetch the data
    obtain_data()

    """
    Insert into the addresses table
    """
    cur = conn.cursor()
    cur.execute(''' INSERT INTO addresses VALUES(?,?,?,?,?,?,?) ''', address)
    conn.commit()
        
    # # Insert data
    # with conn:
    #     # create a new project
    #     project = ('Cool App with SQLite & Python', '2015-01-01', '2015-01-30');
    #     project_id = create_project(conn, project)

    #     # tasks
    #     task_1 = ('Analyze the requirements of the app', 1, 1, project_id, '2015-01-01', '2015-01-02')
    #     task_2 = ('Confirm with user about the top requirements', 1, 1, project_id, '2015-01-03', '2015-01-05')

    #     # create tasks
    #     create_task(conn, task_1)
    #     create_task(conn, task_2)

    return cur.lastrowid

def average_long_lat(conn):
    cur = conn.cursor()
    
    cur.execute(''' SELECT avg(Longitude) FROM addresses; ''')
    avgLong = cur.fetchall()

    cur.execute(''' SELECT avg(Latitude) FROM addresses; ''')
    avgLat = cur.fetchall()
    
    return avgLong, avgLat


def geolocate_data(conn):
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
                results_dict[raw_address]=dict(
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
                results_dict[raw_address]=dict(
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
                results_dict[raw_address]=dict(
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



def create_map(conn):
    avgLong,avgLat = average_long_lat()

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
            if Availability == 1:
                folium.Marker(location=location,
                            popup = full_address,
                            icon=folium.Icon(prefix='fa',icon="fa-smile-o",color="green")
                ).add_to(my_map)
            else:
                folium.Marker(location=location,
                            popup = full_address,
                            icon=folium.Icon(prefix='fa',icon="fa-question-circle-o",color="purple")
                ).add_to(my_map)
            
        cur.close()
        my_map.save("folium_map.html")

    except sqlite3.Error as error:
        print("Failed to read data from sqlite table", error)
    finally:
        if (conn):
            conn.close()
            print("The SQLite connection is closed")
    return my_map

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

    # create tables
    if conn is not None:
        create_table(conn, sql_create_address_table)
    else:
        print("Error! cannot create the database connection.")


def main():
    conn = create_connection(db_file)
    create_tables(conn)
    obtain_addresses_from_neighborhood_name(conn)
    #populate_addresses(conn)
    #obtain_data()
    #create_map(conn)
    conn.close

if __name__ == '__main__':
    main()