import googlemaps
from datetime import datetime
from sklearn.neighbors import NearestNeighbors
import numpy as np
import pymysql
import random

# Connect to google map API
key1 = 'AIzaSyBj7JAQHEc-eFQkfuCXBba0dItAUPL0fMI'
key2 = 'AIzaSyD3_6utmMWtQ8gqcE6-aL5BmVsBvmi4aNM'
gmaps = googlemaps.Client(key=key2)

class KDTrees:

    def __init__(self, nb_neighbours, leaf_size):
        self.nbrs = NearestNeighbors(n_neighbors=nb_neighbours, algorithm='ball_tree', metric = 'haversine', leaf_size=leaf_size)
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


    def addPoints(self, points):
        self.nbrs.fit(points)

    def getNeighbours(self, points):
        self.nbrs.kneighbors(points)

lat = 50.5227
lng = 128.383
points = []
for i in range(0,5000):
    points.append([lat + random.random(), lng + random.random()])