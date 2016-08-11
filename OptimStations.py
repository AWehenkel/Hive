import pymysql
#from sklearn.neighbors import NearestNeighbors
import gmplot
import math
import numpy
#from scipy.sparse import csr_matrix
#from scipy.sparse.csgraph import minimum_spanning_tree
import networkx as nx
import matplotlib.pyplot as plt
import gmplot
import googlemaps
#import pybingmaps
import datetime
import operator
import json
import pybingmaps

class OptimStations:

    def getSortedStations(self, stations, destination):
        stat_dest = {}
        db = pymysql.connect("localhost", "root", "", "hive")
        cursor = db.cursor()
        c = 0
        for station in stations:
            c += 1
            if c % len(stations) / 4 == 0:
                print (float(c) / float(len(stations)))

            start = station[0:2]
            y = (float(destination[0]), float(destination[1]))
            request = "SELECT physical_distance FROM distance WHERE (latA='%f' AND latB='%f' AND lngA='%f' AND lngB='%f') OR (latA='%f' AND latB='%f' AND lngA='%f' AND lngB='%f')" % (
                start[0], y[0], start[1], y[1], y[0], start[0], y[1], start[1])
            try:
                cursor.execute(request)
                data = cursor.fetchone()
                if data:
                    distance = data[0]
                elif self.distanceBetween(destination, start) > 2500:
                    distance = self.distanceBetween(start, y) / 1000 * 1.5
                else:
                    bingMapsKey = "AmOtkPDIx-WA0ushTf-RENb0U_xe_7K6kBW7Xkl6JOpTG41mLY5rtUftM5H-QyUv"
                    bing = pybingmaps.Bing(bingMapsKey)
                    data = bing.route(list(station[0:2]), [float(destination[0]), float(destination[1])],
                                      transite="Transit", timeType="Departure", dateTime="8:00:00AM")
                    distance = data['resourceSets'][0]['resources'][0]["routeLegs"][0]["routeSubLegs"][0][
                        "travelDistance"]
                    time = data['resourceSets'][0]['resources'][0]["routeLegs"][0]["routeSubLegs"][0]["travelDuration"]
                    type_transport = "Transit"
                    now = datetime.datetime.now()
                    timestamp = (
                        datetime.datetime(now.year, now.month, now.day, 8) - datetime.datetime(1970, 1,
                                                                                               1)).total_seconds()
                    timestamp = datetime.datetime.fromtimestamp(timestamp - 7200)
                    query = "INSERT INTO distance(latA, lngA, latB, lngB, type, time_distance, time_departure, physical_distance)" \
                            + " VALUES (%f, %f, %f, %f, '%s', %d, '%s', %f)" % (
                        start[0], start[1], y[0], y[1], type_transport, time, timestamp, distance)
                    cursor.execute(query)
                    db.commit()
            except:
                print "error"
                distance = self.distanceBetween(start, y) / 1000 * 1.5

            stat_dest[station[2]] = distance
        return sorted(stat_dest.items(), key=operator.itemgetter(1))

    # metricKdtree
    def metricKdtree(self, x, y):
        lat1 = x[0]
        lat2 = y[0]
        long1 = x[1]
        long2 = y[1]
        distance = 1
        if (lat1 == lat2 and long1 == long2):
            return 0
        distance += self.distanceBetween(x, y)
        return distance

    def distanceBetween(self, x, y, transit="Driving", option="distance"):

        x[0] = float(x[0])
        y[0] = float(y[0])
        x[1] = float(x[1])
        y[1] = float(y[1])

        if x == y:
            return 0

        db = pymysql.connect("localhost", "root", "", "hive")
        cursor = db.cursor()
        request = "SELECT physical_distance, time_distance FROM distance WHERE (latA='%f' AND latB='%f' AND lngA='%f' AND lngB='%f') " \
                  "OR (latA='%f' AND latB='%f' AND lngA='%f' AND lngB='%f') AND type='%s'" % ( x[0], y[0], x[1], y[1], y[0], x[0], y[1], x[1], transit)
        try:
            cursor.execute(request)
            data = cursor.fetchone()
            if data:
                if option=="distance":
                    return data[0]*1e3
                else:
                    return data[1]
            else:
                print "bingbing"
                # Your Bing Maps Key
                bingMapsKey = "AmOtkPDIx-WA0ushTf-RENb0U_xe_7K6kBW7Xkl6JOpTG41mLY5rtUftM5H-QyUv"
                bing = pybingmaps.Bing(bingMapsKey)
                data = bing.route(x, y, transite=transit, timeType="Departure",
                                  dateTime="8:00:00AM")
                distance = data['resourceSets'][0]['resources'][0]["routeLegs"][0]["routeSubLegs"][0]["travelDistance"]
                time = data['resourceSets'][0]['resources'][0]["routeLegs"][0]["routeSubLegs"][0]["travelDuration"]
                type = transit
                now = datetime.datetime.now()
                timestamp = (
                    datetime.datetime(now.year, now.month, now.day, 8) - datetime.datetime(1970, 1, 1)).total_seconds()
                timestamp = datetime.datetime.fromtimestamp(timestamp - 7200)
                query = "INSERT INTO distance(latA, lngA, latB, lngB, type, time_distance, time_departure, physical_distance)" \
                        + " VALUES (%f, %f, %f, %f, '%s', %d, '%s', %f)" % (
                    x[0], x[1], y[0], y[1], type, time, timestamp, distance)
                cursor.execute(query)
                db.commit()
                # print "map works"
                db.close()
                if option=="distance":
                    return distance*1e3
                else:
                    return time

        except:
            # print "map crashes"
            return self.asTheCrowFlies(x, y)

    # Compute the distance between two points on the map
    def asTheCrowFlies(self, x, y):
        lat1 = float(x[0])
        lat2 = float(y[0])
        long1 = float(x[1])
        long2 = float(y[1])
        rad_earth = 6371e3  # earth radius in m

        delta_lat = math.fabs(math.radians(lat2 - lat1))
        delta_long = math.fabs(math.radians(long2 - long1))

        tmp = math.sin(delta_lat / 2) * math.sin(delta_lat / 2)
        tmp += math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(delta_long / 2) * math.sin(
            delta_long / 2)

        rel_dist = 2 * math.atan2(math.sqrt(tmp), math.sqrt(1 - tmp))

        dist = rad_earth * rel_dist
        return dist

    # returns the closest stations of a destination
    def getCloseStations(self, nb_station, perimeter, destination):
        request = "Select * FROM power_station"
        db = MySQLdb.connect("localhost", "root", "", "hive")
        cursor = db.cursor()

        # Hardcode a big number of station
        if nb_station == 0:
            nb_station = 1000
        # Hardcode a big perimeter
        if perimeter == 0:
            perimeter = 40000
        try:
            cursor.execute(request)
            stations = cursor.fetchall()
            points = []
            c = 0
            for station in stations:
                if self.distanceBetween(destination, ([station[2], station[3]])) < perimeter:
                    points.append((station[2], station[3], station[0]))
                    c += 1
            print "nbre de station: %d" % c
            toreturn = self.getSortedStations(points, destination)
            if nb_station < len(toreturn):
                return self.getSortedStations(points, destination)[0:nb_station]
            return toreturn
        except:
            print "error in db access"

    # Draws an html google map of the point and its neigbours
    def printMapForPoint(self, point, nb_neighbors):
        db = pymysql.connect("localhost", "root", "", "hive")
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
                mymap.marker(result[0][0], result[0][1], title=str(station + 1), dest=pos, text="%d" % station)
            except:
                print "error"
        mymap.draw("result.html", "AIzaSyBj7JAQHEc-eFQkfuCXBba0dItAUPL0fMI")

    # Registers the nb_stations the nearest from each destination in a certain perimeter
    def registerCloseStations(self, nb_stations=0, perimeter=0):
        request = "SELECT * FROM destinations"
        db = pymysql.connect("localhost", "root", "", "hive")
        cursor = db.cursor()
        try:
            cursor.execute(request)
            data = cursor.fetchall()
            for dest in data:
                print "station numero %d " % dest[0]
                coord = dest[3].split(", ")
                close = self.getCloseStations(nb_stations, perimeter, (coord[0], coord[1]))
                close_stat = json.dumps(close)
                request = "UPDATE destinations SET closestations='%s' WHERE id_vehicle=%d" % (
                    str(close_stat), dest[0])
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
        db = pymysql.connect("localhost", "root", "", "hive")
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
        return self.distanceBetween(des_pos, station_pos)

    # Computes and registers in the DB the weight of each edge of the graph
    def registerGraph(self, nb_edge):
        request = "SELECT id_vehicle, closestations FROM destinations"
        db = pymysql.connect("localhost", "root", "", "hive")
        cursor = db.cursor()
        try:
            cursor.execute(request)
            destinations = cursor.fetchall()
            for destination in destinations:
                station = destination[1].split(",")
                for i in range(0, nb_edge):
                    weight = self.computeWeight(destination[0], int(station[i]))
                    request = "INSERT INTO graph_station_vehicle (id_vehicle, id_station, weight) VALUES (%d, %d, %f)" % (
                        destination[0], int(station[i]), weight)
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
            for edge in data:
                vehicle = edge[0] - 1
                station = edge[1] + nb_destination - 1
                matrix[vehicle][station] = edge[2]
                matrix[station][vehicle] = edge[2]
            return matrix
        except:
            print "problem"
        db.close()

    # Registers the stations proposed by the spanning tree
    def registerProposedStations(self):
        graph = csr_matrix(self.getAdjMatrix())
        mst = minimum_spanning_tree(graph)

        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        request = "SELECT COUNT(id_vehicle) AS nb_dest FROM destinations"
        try:
            cursor.execute(request)
            result = cursor.fetchone()
            nb_vehicle = result[0]
            # Init matrix adj of the spanning tree
            matrix = []
            for i in range(0, nb_vehicle):
                matrix.append([])
            msta = mst.toarray()

            for i in range(0, len(msta)):
                for j in range(0, len(msta[i])):
                    if msta[i][j]:
                        if (i >= nb_vehicle):
                            id_station = i - nb_vehicle + 1
                            id_vehicle = j
                        else:
                            id_station = j - nb_vehicle + 1
                            id_vehicle = i
                        matrix[id_vehicle].append((id_station, msta[i][j]))
            for i in range(0, nb_vehicle):
                request = "UPDATE destinations SET proposed_stations='%s' WHERE id_vehicle=%d" % (json.dumps(matrix[i]), i + 1)
                cursor.execute(request)
            db.commit()
            return matrix

        except:
            print "error"

    # Creates a map in html format of the vehicle and their destinations
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
                text = "<h3 style = \"text-align:center;\">" + title + "</h3>Capacite: " + str(
                    data[6]) + "kWh<br/>Niveau de charge: " + str(data[9]) \
                       + "%%<br/>Consommation moyenne: " + str(data[7]) + "kW/100km<br/>Position: " + data[
                           2] + "<br/>Destination: " + data[3] + "<br/>"

                gmap = gmplot.GoogleMapPlotter(dep_lat, dep_lng, 16)
                # Draw departure point
                gmap.marker(dep_lat, dep_lng, des_pos, title, text, 'green')
            gmap.draw("data/vehiclesMatchingMap.html", 'AIzaSyD0QmwrWQGk3YPqvYv7-iUxdqqK7Zh0MO4')

        except:
            print "error"


    # Displays in green the destinations that are deserved by a station and in red the other destinations
    def displayDispatching(self):
        request = "SELECT id_vehicle, des_pos, proposed_stations FROM destinations"
        db = MySQLdb.connect("localhost", "root", "", "hive")
        cursor = db.cursor()
        mymap = gmplot.GoogleMapPlotter(50.8550624, 4.3053506, 8)
        try:
            cursor.execute(request)
            vehicles = cursor.fetchall()

            for vehicle in vehicles:
                if vehicle[2] == "":
                    color = "#FF0000"
                else:
                    color = "#00FF00"

                position = vehicle[1].split(',', 1)
                mymap.marker(float(position[0]), float(position[1]), title=str(vehicle[0]), c=color)

        except:
            print "Unable to fetch data"
        db.close()
        mymap.draw('./mymap.html', 'AIzaSyBj7JAQHEc-eFQkfuCXBba0dItAUPL0fMI')

    # Insert the element in the list so that the elements in the list are sorted by their length
    def inOrderInsert(self, element, list):
        cur = 0
        while cur < len(list) and len(element[1]) > len(list[cur][1]):
            cur += 1
        if cur == len(list):
            list.append(element)
        else:
            list.insert(cur, element)

    # Option 1: Displays in green the destinations that are deserved by a station, in orange the
    # destinations that share a station and in red the other destinations
    # Option 2: Or displays the station that are deserved in red and the one that are not deserved in black
    def displayDispatching(self, option=1):
        request = "SELECT id_vehicle, des_pos, proposed_stations FROM destinations"
        db = pymysql.connect("localhost", "root", "", "hive")
        cursor = db.cursor()
        mymap = gmplot.GoogleMapPlotter(50.8550624, 4.3053506, 8)
        try:
            cursor.execute(request)
            vehicles = cursor.fetchall()
            ok_vehicles = [0 for x in range(len(vehicles))]

            proposed_stations = []
            cur = 0
            for vehicle in vehicles:
                proposed_stations_for_1EV = [vehicle[0], vehicle[2].split(',', vehicle[2].count(','))]
                self.inOrderInsert(proposed_stations_for_1EV, proposed_stations)

            # Assign a station to each vehicle
            stations_number = range(4000)
            cur = 0
            for row in proposed_stations:
                cur += 1
                for stat in row[1]:
                    stat = int(stat.split('-')[0])
                    # Check if the station is still available
                    if stat in stations_number:
                        ok_vehicles[row[0] - 1] = 1
                        stations_number.remove(stat)
                        break

            if option == 1:
                for vehicle in vehicles:
                    # Check if there is no station for this vehicle
                    if vehicle[2] == "":
                        color = "#FF0000"
                    # Check if it shares stations but didn't get one
                    else:
                        if ok_vehicles[vehicle[0] - 1] == 0:
                            color = "#FFA500"
                        else:
                            color = "#00FF00"

                    position = vehicle[1].split(',', 1)
                    mymap.marker(float(position[0]), float(position[1]), title=str(vehicle[0]), c=color)

            if option == 2:
                # Compute also the percentage of power that is acquired
                total_power = 0
                used_power = 0
                for i in range(1, 4000):
                    request = "SELECT * FROM power_station where id=%d" % i
                    cursor.execute(request)
                    station_info = cursor.fetchone()
                    total_power += station_info[4]
                    if i in stations_number:
                        color = "#FFFF00"
                    else:
                        color = "#FF0000"
                        used_power += station_info[4]

                    title = "Station%d" % station_info[0]
                    text = "<h3 style = \"text-align:center;\">" + title + "</h3>Puissance: " + str(
                        station_info[4]) + "kW<br/>Type: " + str(station_info[1]) \
                           + "<br/>Position: " + str(station_info[2]) + ", " + str(station_info[3]) + "<br/>"
                    mymap.marker(float(station_info[2]), float(station_info[3]), title=title, text=text, c=color)
                print 'percentage of stations used: %f' % (float(len(stations_number)) / 4000)
                print "percentage of power used: %f" % (used_power / total_power)
                print "percentage of destinations deserved: %f " % (float(ok_vehicles.count(1)) / (len(vehicles)))

        except:
            print "Unable to fetch data"
        db.close()
        mymap.draw('./mymap.html', 'AIzaSyBj7JAQHEc-eFQkfuCXBba0dItAUPL0fMI')

    # Display information about the selected vehicle (can choose to display close stations and
    # priviledged stations
    def displayEVInfo(self, mymap, id, close=1, priv=1):
        request = "SELECT * FROM destinations WHERE id_vehicle=%d" % id
        db = MySQLdb.connect("localhost", "root", "", "hive")
        cursor = db.cursor()
        try:
            cursor.execute(request)
            vehicle = cursor.fetchone()
            dep_time = vehicle[1]
            dep_pos = vehicle[2].split(',')
            des_pos = vehicle[3].split(',')
            closestations = vehicle[4].split(',', vehicle[4].count(','))
            proposed_stations = vehicle[5].split(',', vehicle[5].count(','))

            # Display departure (blue) and destination (green)
            request = "SELECT * FROM vehicles WHERE id=%d" % vehicle[0]
            cursor.execute(request)
            ev_info = cursor.fetchone()
            title = "EV%d" % vehicle[0]
            text = "<h3 style = \"text-align:center;\">" + title + "</h3>Capacite: " + str(
                ev_info[1]) + "kWh<br/>Niveau de charge: " + str(ev_info[4]) \
                   + "%%<br/>Consommation moyenne: " + str(ev_info[2]) + "kW/100km<br/>Depart: " + vehicle[
                       2] + "<br/>Destination: " + vehicle[3] + "<br/>"
            mymap.marker(float(dep_pos[0]), float(dep_pos[1]), vehicle[3], title=title, text=text, c="#00FFFF")
            mymap.marker(float(des_pos[0]), float(des_pos[1]), title=title, c="#00FF00")

            if close:
                # Display the destinations that are close to the destination (in black)
                cur = 0
                for station in closestations:
                    request = "SELECT * FROM power_station WHERE id=%d" % int(closestations[cur])
                    cursor.execute(request)
                    station_info = cursor.fetchone()
                    title = "Station%d" % station_info[0]
                    text = "<h3 style = \"text-align:center;\">" + title + "</h3>Puissance: " + str(
                        station_info[4]) + "kW<br/>Type: " + str(station_info[1]) \
                           + "<br/>Position: " + str(station_info[2]) + ", " + str(station_info[3]) + "<br/>"
                    mymap.marker(float(station_info[2]), float(station_info[3]), vehicle[3],
                                 title=title, text=text, c="#000000")
                    cur += 1

            if priv:
                # Display the proposed station with their weight (in red)
                for station in proposed_stations:
                    station = station.split('-')
                    request = "SELECT * FROM power_station WHERE id=%d" % int(station[0])
                    cursor.execute(request)
                    station_info = cursor.fetchone()
                    title = "Station%d" % station_info[0]
                    text = "<h3 style = \"text-align:center;\">" + title + "</h3>Puissance: " + str(
                        station_info[4]) + "kW<br/>Type: " + str(station_info[1]) \
                           + "<br/>Position: " + str(station_info[2]) + ", " + str(station_info[3]) + "<br/>"
                    mymap.marker(float(station_info[2]), float(station_info[3]), vehicle[3],
                                 title=title, text=text, c="#FF0000")

        except:
            print "Unable to fetch data"
        db.close()

    # Display several vehicles at a time (by a certain step) with their respective info
    def recDisplayEVInfo(self, close=1, priv=1, step=1):

        mymap = gmplot.GoogleMapPlotter(50.8550624, 4.3053506, 8)

        for id in range(1, 3000):
            self.displayEVInfo(mymap, id, close, priv)
            mymap.draw('./mymap.html', 'AIzaSyBj7JAQHEc-eFQkfuCXBba0dItAUPL0fMI')
            if id % step == 0:
                raw_input("Click for next step")

    def displayEvandStation(self, nb_ev, nb_station):
        request1 = "SELECT * FROM vehicles"
        request2 = "SELECT * FROM power_station"
        db = MySQLdb.connect("localhost", "root", "", "hive")
        cursor = db.cursor()
        mymap = gmplot.GoogleMapPlotter(50.8550624, 4.3053506, 8)
        try:
            # Display the vehicle
            cursor.execute(request1)
            vehicles = cursor.fetchmany(nb_ev)
            for vehicle in vehicles:
                request = "SELECT des_pos FROM destinations WHERE id_vehicle=%d" % vehicle[0]
                cursor.execute(request)
                des_pos = cursor.fetchone()
                des_pos_split = des_pos[0].split(',')
                title = "EV%d" % vehicle[0]
                text = "<h3 style = \"text-align:center;\">" + title + "</h3>Capacite: " + str(
                    vehicle[1]) + "kWh<br/>Niveau de charge: " + str(vehicle[4]) \
                       + "%%<br/>Consommation moyenne: " + str(vehicle[2]) + "kW/100km<br/>Depart: " + vehicle[
                           3] + "<br/>Destination: " + des_pos[0] + "<br/>"
                mymap.marker(float(des_pos_split[0]), float(des_pos_split[1]), title=title, text=text, c="#00FFFF")

            # Display the station
            cursor.execute(request2)
            stations = cursor.fetchmany(nb_station)

            # Display the station
            cursor.execute(request2)
            stations = cursor.fetchmany(nb_station)
            for station in stations:
                title = "Station%d" % station[0]
                text = "<h3 style = \"text-align:center;\">" + title + "</h3>Puissance: " + str(
                    station[4]) + "kW<br/>Type: " + str(station[1]) \
                       + "<br/>Position: " + str(station[2]) + ", " + str(station[3]) + "<br/>"
                mymap.marker(float(station[2]), float(station[3]), title=title, text=text, c="#000000")

            mymap.draw('./mymap.html', 'AIzaSyBj7JAQHEc-eFQkfuCXBba0dItAUPL0fMI')

        except:
            print "Unable to fetch data"
        db.close()

    def sortAndFilterStations(self, stations, power, order = "distance"):
        #type: (stations, power, order) -> stations

        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        #Loads the station that are already reserved
        request = "SELECT id_station FROM reservation"
        try:
            id = "AND id NOT IN ("
            cursor.execute(request)
            datas = cursor.fetchall()
            for data in datas:
                id += "%d," % data[0]
            id = id[:-1] + ")"
            if(not(datas)):
                id = ""
        except:
            print "error"
            id =""

        id_stations = "("
        for station in stations:
            id_stations += "%d," % station[0]
        id_stations = id_stations[:-1] + ")"

        if(order != "distance"):
            if(order[0] == "-"):
                sql_order = "ORDER BY %s DESC" % order[1:]
            else:
                sql_order = "ORDER BY %s" % order
        else:
            sql_order = "ORDER BY FIELD (id, %s)" % id_stations[1:-1]

        request = "SELECT * FROM power_station WHERE id IN %s %s AND power > %f %s" % (id_stations, id, power, sql_order)
        try:
            cursor.execute(request)
            data = cursor.fetchall()
        except:
            #print "problem"
            return []
        return data

    def getStations(self, id_des):
        request = "SELECT * FROM destinations WHERE id_vehicle=%d" % id_des
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        try:
            cursor.execute(request)
            data = cursor.fetchone()
        except:
            print "problem"
            return -1
        da = data[4]
        dic = json.loads(da)
        self.sortAndFilterStations(dic, 100, order="-power")


op = OptimStations()
#op.getStations(1)
# op.registerGraph(5)
#op.displayDispatching(2)
#op.registerCloseStations(100, 10000)
# op.computeWeight(12,12)
# graph = csr_matrix(op.getAdjMatrix())
# mst = minimum_spanning_tree(graph)
# print mst[2222]
# op.createMap(15)
