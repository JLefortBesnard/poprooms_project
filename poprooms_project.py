import urllib.request
from bs4 import BeautifulSoup
from math import asin, cos, sqrt, pi
import re
import time
import pandas as pd
import numpy as np

# Extract url that links to the personal webpage of each flat and return them as a list
def extract_link_each_flat(url):
    with urllib.request.urlopen(url) as url:
        html = url.read()
    soup = BeautifulSoup(html,"html.parser")
    # Extract url child from each appartment (link to Location)
    list_urls = []
    urls = soup.findAll("h3")
    for ind, url in enumerate(urls):
        for part in url.find_all('a'): 
            flat_url = "https:" + part.get('href')
            list_urls.append(flat_url)
    return list_urls


# Extract info of each flat and store info in dictionnary, return the dictionnary
def store_info(list_urls):
    dic_info = {}
    for url_str in list_urls:
        # load page info of a specific appartment
        with urllib.request.urlopen(url_str) as url:
            html = url.read()
        soup = BeautifulSoup(html,"html.parser")
        # Extract price, map_url and id
        price = soup.findAll("div", { "class":"price" })
        map_url = "https://rent.591.com.tw/" + soup.findAll("div", { "id":"mapRound" })[0].findAll('iframe')[0].get('src')
        id = url_str[-12:-5]
        price = price[0].text.split("\n")[1]   
        dic_info[id] = price, map_url
    return dic_info


# Extract lattitude and longitude from the map, return the updated dictionnary
def extract_gps_info(dic_info):
    for id in dic_info:
        price = dic_info[id][0]
        map_url = dic_info[id][1]
        with urllib.request.urlopen(map_url) as url:
            html = url.read()
        soup = BeautifulSoup(html,"html.parser")
        # Extract GPS position of the flat
        gmap_url = "https:" + soup.findAll("div", {"class":"propMapBarMap"})[0].findAll("iframe")[0].get('src') 
        GPS = gmap_url[-40:-18]
        # extract lattitude and longitude
        flat_lat = GPS.split(',')[0]
        flat_lon = GPS.split(',')[1]
        try:
            flat_lat = float(flat_lat)
            flat_lon = float(flat_lon)
        except:
            try:
                flat_lat = float(flat_lat[2:])
                flat_lon = float(flat_lon)
            except:
                try:
                    flat_lat = float(flat_lat[3:]) 
                    flat_lon = float(flat_lon)
                except:
                    print("Problem with", flat_lat)
        dic_info[id] = price, {"lon":flat_lon, "lat":flat_lat}
    return dic_info


# Return distance from 2 locations (default: distance from City center GPS: lat=25.049988, lon=121.524743)
def distance(lat1, lon1, lat2=25.049988, lon2=121.524743):
    p = pi/180 
    a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p) * cos(lat2*p) * (1-cos((lon2-lon1)*p))/2
    return 12742 * asin(sqrt(a)) 


def get_stations_coordinates():
    tfile = open("MRT_gps.txt", "r")
    lines = tfile.readlines()
    stations = {}
    for line in lines:
        if len(line)<10:
            break
        num = line.split(" ")[0]
        name = line.split(" ")[1].split("\"")[1]
        lon = line.split(" ")[2][5:]
        lat = line.split(" ")[3][:-2]
        stations[num] = name, {"lat": lat, "lon":lon}
    return stations



# Compute distance from a specific location, 
# return station name + distance in km
def closest_MRT(lat, lon):
    stations = get_stations_coordinates()
    closest_dist = 100
    closest_MRT = 'undefined'
    name = 'undefined'
    for id in stations:
        lat_mrt = float(stations[id][1]['lat'])
        lon_mrt = float(stations[id][1]['lon'])
        dist = distance(lat, lon, lat_mrt, lon_mrt)
        if closest_dist > dist:
           closest_dist = dist
           closest_MRT = id
           name = stations[id][0]
    return closest_dist, closest_MRT, name


# Add distance from center and from closest MRT into the dictionnary
def save_distances(dic_info): 
    # dic must be format id :(price, GPS)
    # return dic format id:(price, ps, dist_from_center, closest_mrt)
    for id in dic_info:
        flat_lat = float(dic_info[id][1]["lat"])
        flat_lon = float(dic_info[id][1]["lon"])
        closest = closest_MRT(flat_lat, flat_lon)
        dist_from_center = distance(flat_lat, flat_lon)
        price = dic_info[id][0]
        GPS = dic_info[id][1]
        dic_info[id] = price, GPS, dist_from_center, closest
    return dic_info

# compute a metric between distance center and distance MRT
def metric_distance(dist_cent, dist_mrt):
    if dist_mrt < 1:
        dist_mrt = 1
    if dist_cent < 5:
        dist_cent = 5
    metric = 1/dist_mrt*45 + 5/dist_cent*55 
    return metric

# Gather info into dataframe and sort it by metric and price
def dataframe_results(dic_info, df2=None, add=0):
    # store info into dataframe
    df = pd.DataFrame(dic_info.values(), dic_info.keys(), ['Price', 'GPS coord','dist_from_center', 'dist_from_MRT']) 
    # compute and add the metric to the df
    df["metric"] = 0
    for id in df.index:
        metric_i = metric_distance(df.loc[id]["dist_from_center"], df.loc[id]["dist_from_MRT"][0])
        df.loc[id, "metric"] = metric_i
        df.loc[id, "Price"] = np.int(df.loc[id, "Price"][:-5].replace(",",""))
    if add == 1:
        df_combined = pd.concat([df, df2])
        df = df_combined
    # Sort df by metric and then price and return it
    return df.sort_values(["metric", "Price"], ascending=[False, True])



# Run the whole script for the below URLs
urls = ["https://rent.591.com.tw/?kind=0&region=1&pattern=5&order=money&orderType=asc",
"https://rent.591.com.tw/?kind=0&region=1&pattern=5",
"https://rent.591.com.tw/?kind=0&region=1&pattern=5&order=posttime&orderType=desc",
"https://rent.591.com.tw/?kind=0&region=1&pattern=5&hasimg=1&not_cover=1&role=1"]

for i, url in enumerate(urls):
    print("||||||||    Running", i + 1, '/', len(urls), "|||||||")
    print("*** EXTRACTING APPARTEMENT LIST INFO... ***")
    print("*** URL = ", url, " ***")
    list_urls = extract_link_each_flat(url)
    print("*** EXTRACTING EACH APPARTEMENT INFO... ***")
    dic_info = store_info(list_urls)
    print("*** EXTRACTING EACH APPARTEMENT MAP... ***")
    dic_info = extract_gps_info(dic_info)
    print("*** COMPUTING DISTANCE FROM CENTER AND CLOSEST MRT... ***")
    dic_info = save_distances(dic_info)
    print("*** STORING RESULTS INTO DATAFRAME ***")
    if i == 0:
        df = dataframe_results(dic_info)    
    else:
        # if second or more turn, concatenate df
        df2 = dataframe_results(dic_info, df2=df, add=1)
        df = df2

print("FINAL RESULTS: appartement are printed by order of best metric and then best price")
print(df)

from datetime import date
today = "day{}month{}".format(date.today().day, date.today().month)
df.to_excel("sorted_flat.xlsx", sheet_name='{}'.format(today))


















