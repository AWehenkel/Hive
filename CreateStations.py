import pymysql
import googlemaps
import math
import random

#Compute the distance between two points on the map
def twoPointsDistance(lat1, long1, lat2, long2):

    rad_earth = 6371e3  #earth radius in m

    delta_lat = math.fabs(math.radians(lat2-lat1))
    delta_long = math.fabs(math.radians(long2-long1))

    tmp = math.sin(delta_lat/2) * math.sin(delta_long/2)
    tmp += math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(delta_lat/2) * math.sin(delta_long/2)

    rel_dist = 2 * math.atan2(math.sqrt(tmp), math.sqrt(1-tmp))

    dist = rad_earth*rel_dist

    return dist

# Generate a list of random locations for chargers at places where there are PVs
def genRandomStations (towns, number) :

    # Open database connection
    db = pymysql.connect("localhost","root","","hive")

    #Get the pv positions
    request = 'SELECT position, power FROM pv'
    cur = db.cursor()
    try:
       # Execute the SQL command
       cur.execute(request)
       # Fetch all the rows in a list of lists.
       pv_positions = cur.fetchall()

       for row in pv_positions:
           lat = row[0]
           long = row[1]
           power = row[2]

           #Compute the distance of each pv to the different towns and keep the closer
           min = 400000000
           closest = towns[0]
           for town in towns :
               tmp = twoPointsDistance(lat, long, town['lat'], town['long'])
               if tmp < min :
                   min = tmp
                   closest = town



    except:
        print ("Error: unable to fetch data")



genRandomStations(2, 2)
