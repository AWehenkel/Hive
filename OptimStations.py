import MySQLdb
from sklearn.neighbors import NearestNeighbors
import gmplot
import math
import numpy
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import minimum_spanning_tree
import networkx as nx
import matplotlib.pyplot as plt
import gmplot
import googlemaps

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

    # Faudrait incorporer le systme de cotation dans le poids egalement, pour que les stations les mieux
    # cotees viennent en premier

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
                    weight = self.computeWeight(destination[0], int(station[i]))
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

    def registerProposedStations(self):
        graph = csr_matrix(op.getAdjMatrix())
        mst = minimum_spanning_tree(graph)

        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        request = "SELECT COUNT(id_vehicle) AS nb_dest FROM destinations"
        try:
            cursor.execute(request)
            result = cursor.fetchone()
            nb_vehicle = result[0]
            print nb_vehicle
            #Init matrix adj of the spanning tree
            matrix = []
            for i in range(0, nb_vehicle):
                matrix.append("")
            msta = mst.toarray()
            for i in range(0, len(msta)):
                for j in range(0, len(msta[i])):
                    if msta[i][j]:
                        if(i >= nb_vehicle):
                            id_station = i - nb_vehicle + 1
                            id_vehicle = j
                        else:
                            id_station = j - nb_vehicle + 1
                            id_vehicle = i
                        matrix[id_vehicle] += "%d-%f," % (id_station, msta[i][j])
            for i in range(0, nb_vehicle):
                request = "UPDATE destinations SET proposed_stations='%s' WHERE id_vehicle=%d" % (matrix[i], i + 1)
                cursor.execute(request)
            db.commit()

        except:
            print "error"

    #Creates a map in html format of the vehicle and their destinations
    def createMap(self, destination_id):
        gmaps = googlemaps.Client(key='AIzaSyD0QmwrWQGk3YPqvYv7-iUxdqqK7Zh0MO4')
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        request = "SELECT * FROM destinations NATURAL JOIN vehicles HAVING id_vehicle = id AND id_vehicle=%d" % destination_id
        try:
            cursor.execute(request)
            datas = cursor.fetchall()
            for data in datas:
                print data
                dep_pos = data[2].split(", ")
                dep_lat = dep_pos[0]
                dep_lng = dep_pos[1]
                des_pos = data[3]
                title = "EV%d" % data[0]
                text = "<h3 style = \"text-align:center;\">" + title + "</h3>Capacite: " + str(data[6]) + "kWh<br/>Niveau de charge: " + str(data[9]) \
                       + "%%<br/>Consommation moyenne: " + str(data[7]) + "kW/100km<br/>Position: " + data[2] + "<br/>Destination: " + data[3] + "<br/>"

                gmap = gmplot.GoogleMapPlotter(dep_lat, dep_lng, 16)
                #Draw departure point
                gmap.marker(dep_lat, dep_lng, des_pos, title, text, 'green')
            gmap.draw("data/vehiclesMatchingMap.html", 'AIzaSyD0QmwrWQGk3YPqvYv7-iUxdqqK7Zh0MO4')


        except:
            print "error"



op = OptimStations()
#op.registerGraph(5)
op.registerProposedStations()
#op.registerCloseStations(15)
#op.computeWeight(12,12)
#graph = csr_matrix(op.getAdjMatrix())
#mst = minimum_spanning_tree(graph)
#print mst[2222]
#op.createMap(15)