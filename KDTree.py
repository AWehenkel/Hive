import googlemaps
import numpy as np
from datetime import datetime
import random
import sklearn
from sklearn.neighbors import NearestNeighbors
import numpy as np
from sklearn.neighbors import DistanceMetric
from sklearn.neighbors.ball_tree import BallTree

# Connect to google map API
key1 = 'AIzaSyBj7JAQHEc-eFQkfuCXBba0dItAUPL0fMI'
key2 = 'AIzaSyD3_6utmMWtQ8gqcE6-aL5BmVsBvmi4aNM'
gmaps = googlemaps.Client(key=key2)

class KDTrees:
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


    def getNearest(self, points, nb_neighbours, leaf_size):
        nbrs = NearestNeighbors(n_neighbors=nb_neighbours, algorithm='ball_tree', metric = 'pyfunc', func = self.mapDistance)
        nbrs.fit(points)
        print nbrs.kneighbors(points)



t = KDTrees()
t.mapDistance((50.3551856216, 4.4355738111), (50.2686040185, 4.4299929502))
points = []
for i in range(0,50):
    points.append([50.0 + random.random(), 4 + random.random()])

t.getNearest(points, 3, 5)
