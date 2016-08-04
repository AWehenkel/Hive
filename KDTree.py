import googlemaps
import numpy as np
from datetime import datetime
import random
import sklearn
from sklearn.neighbors import NearestNeighbors
import numpy as np
import math
import MySQLdb
import pickle
from sklearn.externals import joblib
from sklearn.neighbors import DistanceMetric
from sklearn.neighbors.ball_tree import BallTree

# Connect to google map API
key1 = 'AIzaSyBj7JAQHEc-eFQkfuCXBba0dItAUPL0fMI'
key2 = 'AIzaSyD3_6utmMWtQ8gqcE6-aL5BmVsBvmi4aNM'
gmaps = googlemaps.Client(key=key2)

class KDTrees:

    def __init__(self, nb_neighbours, leaf_size):
        self.nbrs = NearestNeighbors(n_neighbors=nb_neighbours, algorithm='ball_tree', metric = 'pyfunc', func = self.twoPointsDistance, leaf_size=leaf_size)
    # Compute distance in time between two points on the map
    def mapDistance(self, x, y):
        if (len(x) > 2):
            return np.sum((x - y) ** 2)
        else:
            if(x[0] < y[0]):
                tmp = y
                y = x
                x = tmp
            pos1 = str(x[0]) + ", " + str(x[1])
            pos2 = str(y[0]) + ", " + str(y[1])
            timestamp = datetime.now()
            sec_to_add = 32 * 3600 + (timestamp - datetime(1970, 1, 1)).total_seconds() - 2*3600 - timestamp.hour * 3600 - timestamp.minute * 60 - timestamp.second
            traject = gmaps.directions(pos1, pos2, mode="transit", departure_time=timestamp.fromtimestamp(sec_to_add))
            try:
                print 'ok'
                return (traject[0]["legs"][0]["arrival_time"]["value"] - traject[0]["legs"][0]["departure_time"]["value"])
            except:
                print 'bug'
                return 1000000000

    # Compute the distance between two points on the map
    def twoPointsDistance(self, x, y):
        if (len(x) != 2):
            return np.sum((x - y) ** 2)
        lat1 = x[0]
        long1 = x[1]
        lat2 = y[0]
        long2 = y[1]
        rad_earth = 6371e3  # earth radius in m

        delta_lat = math.fabs(math.radians(lat2 - lat1))
        delta_long = math.fabs(math.radians(long2 - long1))

        tmp = math.sin(delta_lat / 2) * math.sin(delta_long / 2)
        tmp += math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(delta_lat / 2) * math.sin(
            delta_long / 2)

        rel_dist = 2 * math.atan2(math.sqrt(tmp), math.sqrt(1 - tmp))

        dist = rad_earth * rel_dist
        return dist


    def addPoints(self, points):
        self.nbrs.fit(points)

    def getNeighbours(self, points):
        self.nbrs.kneighbors(points)


# Open database connection
db = MySQLdb.connect("localhost","root","videogame2809","hive" )

cursor = db.cursor()

request = "SELECT * FROM power_station "

try:
    results = cursor.execute(request)
    points = []
    for row in results:
        pr
except:
    print "error"

