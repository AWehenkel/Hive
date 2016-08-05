import MySQLdb
from sklearn.neighbors import NearestNeighbors
import gmplot
import math
import numpy
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import minimum_spanning_tree
import networkx as nx
import matplotlib.pyplot as plt

class OptimStations:

    # Compute the distance between two points on the map
    def twoPointsDistance(self, x, y):
        lat1 = x[0]
        lat2 = y[0]
        long1 = x[1]
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

    #returns the closest stations of a destination
    def getCloseStations(self, nb_station, leaf_size, destination):
        request = "Select * FROM power_station"
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        nbrs = NearestNeighbors(n_neighbors=nb_station, algorithm='ball_tree', metric='haversine',
                                     leaf_size=leaf_size)
        try:
            cursor.execute(request)
            stations = cursor.fetchall()
            points = []
            for station in stations:
                points.append([station[2], station[3]])
            points.append(destination)
            nbrs.fit(points)
        except:
            print "error in db access"

        return nbrs.kneighbors(destination)

    #Draw an html google map of the point and its neigbours
    def printMapForPoint(self, point, nb_neighbors):
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        stations = self.nbrs.kneighbors(point, nb_neighbors)[1]
        stations.tolist
        mymap = gmplot.GoogleMapPlotter(point[0], point[1], 12)
        for station in stations[0]:
            request = "SELECT lat, lng FROM power_station WHERE id = %d" % (station + 1)
            try:
                cursor.execute(request)
                result = cursor.fetchall()
                pos = ("%s, %s" % (point[0], point[1]))
                mymap.marker(result[0][0], result[0][1], title=str(station + 1), dest=pos, text="%d"%station)
            except:
                print "error"
        mymap.draw("result.html", "AIzaSyBj7JAQHEc-eFQkfuCXBba0dItAUPL0fMI")


    def registerCloseStations(self, nb_stations):
        request = "SELECT * FROM destinations"
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        try:
            cursor.execute(request)
            data = cursor.fetchall()
            print len(data)
            c = 0
            for dest in data:
                print c
                c += 1
                coord = dest[3].split(", ")
                close = self.getCloseStations(nb_stations,5,(coord[0], coord[1]))
                close[1].tolist
                close_stat = ""
                for el in close[1][0][1:]:
                    close_stat += str(el + 1) + ","
                request = "UPDATE destinations SET closestations='%s' WHERE id_vehicle=%d" % (str(close_stat[:-1]), dest[0])
                cursor.execute(request)
            db.commit()
        except:
            print "error to access db"
        db.close()

    # Returns the weight associate to the edge linking a vehicle to a station
    def computeWeight(self, id_vehicle, id_station):
        request_ev = "SELECT des_pos FROM destinations WHERE id_vehicle=%d" % id_vehicle
        request_st = "SELECT lat, lng FROM power_station WHERE id=%d" % id_station
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        try:
            cursor.execute(request_ev)
            data = cursor.fetchone()
            des_pos = data[0].split(", ")
            des_pos[0] = float(des_pos[0])
            des_pos[1] = float(des_pos[1])
            cursor.execute(request_st)
            station_pos = cursor.fetchone()

        except:
            print "problem"
        return self.twoPointsDistance(des_pos, station_pos)

    # Computes and registers in the DB the weight of each edge of the graph
    def registerGraph(self, nb_edge):
        request = "SELECT id_vehicle, closestations FROM destinations"
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        try:
            cursor.execute(request)
            destinations = cursor.fetchall()
            for destination in destinations:
                station = destination[1].split(",")
                print destination[0]
                for i in range(0, nb_edge):
                    weight = 1/self.computeWeight(destination[0], int(station[i])) * 10000
                    request = "INSERT INTO graph_station_vehicle (id_vehicle, id_station, weight) VALUES (%d, %d, %f)" % (destination[0], int(station[i]), weight)
                    cursor.execute(request)
            db.commit()
        except:
            print "problem"

    # Creates a graph from the data of the db
    def getAdjMatrix(self):
        request0 = "SELECT * FROM destinations GROUP BY id_vehicle"
        request1 = "SELECT * FROM power_station GROUP BY id"
        request = "SELECT * FROM graph_station_vehicle"
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        nb_node = 0
        try:
            cursor.execute(request0)
            nb_destination = cursor.rowcount
            cursor.execute(request1)
            nb_station = cursor.rowcount
            nb_node = nb_destination + nb_station
            matrix = numpy.zeros((nb_node, nb_node))
            cursor.execute(request)
            data = cursor.fetchall()
            print nb_node
            for edge in data:
                vehicle = edge[0] - 1
                station = edge[1] + nb_destination - 1
                matrix[vehicle][station] = edge[2]
                matrix[station][vehicle] = edge[2]
            return matrix
        except:
            print "problem"
        db.close()


op = OptimStations()
#op.registerCloseStations(15)
#op.computeWeight(12,12)
graph = csr_matrix(op.getAdjMatrix())
mst = minimum_spanning_tree(graph)
print mst[2222]