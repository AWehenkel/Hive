import pymysql
from OptimStations import *
from data.towns import *
import gmplot
from Dijkstra import *
import random
import statistics


class StationsOnTheGo:

    #Determines the station that are situated on the way between two locations
    #The smaller closeness is, the less station you will get
    def onTheWay (self, x, y, des_time, closeness):

        x[0] = float(x[0])
        y[0] = float(y[0])
        x[1] = float(x[1])
        y[1] = float(y[1])

        station = []
        try:
            #Get all the stations
            db = pymysql.connect("localhost", "root", "", "hive")
            cursor = db.cursor()
            request = "SELECT * FROM power_station"
            cursor.execute(request)
            stations = cursor.fetchall()
        except:
            print "Unable to fetch data"

        #Draw the two points on the map
        mymap = gmplot.GoogleMapPlotter(x[0], x[1], 8)
        mymap.marker(float(x[0]), float(x[1]),title="PointA", c="#00FF00")
        mymap.marker(float(y[0]), float(y[1]),title="PointB", c="#00FF00")

        #Generate two points on the mediatrice and compute their distance to the original points
        op = OptimStations()
        med_points = self.generatePointsAtSameDistance(x, y, closeness)
        med_distances = [0 for z in range(2)]
        med_distances[0] = op.asTheCrowFlies(x, med_points[0])
        med_distances[1] = op.asTheCrowFlies(x, med_points[1])

        # Compute the distance between the two points and the data for the third circle
        distance = op.asTheCrowFlies(x, y)
        center = [(x[0]+y[0])/2, (x[1]+y[1])/2]
        mymap.marker(float(center[0]), float(center[1]),title="Center", c="#00FF00")

        #Compute the time to reach the destination
        time_to_reach = op.distanceBetween(x, y, "Driving", option="time")
        time_to_reach = 0
        dep_time = des_time - time_to_reach

        #Select the stations that are in the two circles
        selected_stations = []
        for station in stations:
            dist_to_center = op.asTheCrowFlies(center, [station[2], station[3]])
            dist_to_med0 = op.asTheCrowFlies(med_points[0], [station[2], station[3]])
            dist_to_med1 = op.asTheCrowFlies(med_points[1], [station[2], station[3]])

            if dist_to_center < distance/2 and dist_to_med0 < med_distances[0] and dist_to_med1 < med_distances[1]:

                #Remove the stations that will not be available during the trip
                # !!! MAYBE DO STH MORE PRECISE LATER ON !!!
                slots = []
                request = "SELECT DISTINCT * FROM power_slot WHERE id_station='%d' AND id_vehicle=%d AND begin_time<=%f AND begin_time>=%d"\
                          % (station[0], -1, des_time, dep_time)
                try:
                    #Get all the stations
                    cursor.execute(request)
                    slots = cursor.fetchone()
                except:
                    print "Unable to fetch data about slots"

                #If there is a slot available, we keep the station
                if slots:
                    selected_stations.append(station)
                    title = "Station%d" % station[0]
                    text = "<h3 style = \"text-align:center;\">" + title + "</h3>Puissance: " + str(station[4]) + \
                           "kW<br/>Type: " + str(station[1]) \
                           + "<br/>Position: " + str(station[2]) + ", " + str(station[3]) + "<br/>"
                    mymap.marker(float(station[2]), float(station[3]), title=title, text=text, c="#FF0000")

        mymap.draw("./mymap.html", 'AIzaSyD0QmwrWQGk3YPqvYv7-iUxdqqK7Zh0MO4')

        return selected_stations

    #Generate two points that are situated on the mediatrice of two given points
    def generatePointsAtSameDistance(self, x, y, closeness):

        x[0] = float(x[0]); x[1] = float(x[1]); y[0] = float(y[0]); y[1] = float(y[1])

        mymap = gmplot.GoogleMapPlotter(x[0], x[1], 8)
        op = OptimStations()
        distance = op.asTheCrowFlies(x, y)
        mymap.marker(float(x[0]), float(x[1]),title="Center", c="#00FF00")
        mymap.marker(float(y[0]), float(y[1]),title="Center", c="#00FF00")

        center = [(x[0]+y[0])/2, (x[1]+y[1])/2]
        mymap.marker(float(center[0]), float(center[1]),title="Center", c="#00FF00")

        t = Towns(0.1)
        points = t.genRandomLocation(center[0], center[1], distance/closeness, int(distance/100))

        #Keep only the points that are situated at the same distance of the two original points
        tresh = 1000
        ok_points = []
        for point in points:
            point = point.split(',')
            distance1 = op.asTheCrowFlies(point, x)
            distance2 = op.asTheCrowFlies(point, y)
            if (math.fabs(distance1-distance2)) < tresh:
                ok_points.append(point)

        #Keep the two points that are the furthest away from the center
        max = 0
        chosen_point1 = ok_points[0]
        for point in ok_points:
            dist = op.asTheCrowFlies(point, center)
            if dist > max:
                max = dist
                chosen_point1 = [float(point[0]), float(point[1])]
        mymap.marker(float(chosen_point1[0]), float(chosen_point1[1]), title="Point", c="#000000")
        chosen_point2 = [center[0]-(float(chosen_point1[0])-center[0]), center[1]-(float(chosen_point1[1])-center[1])]
        mymap.marker(float(chosen_point2[0]), float(chosen_point2[1]), title="Point", c="#000000")

        #mymap.draw("./mymap.html", 'AIzaSyD0QmwrWQGk3YPqvYv7-iUxdqqK7Zh0MO4')

        return  [chosen_point1, chosen_point2]

    #This function gives how long you need to charge to reach a destination at a certain distance,
    # knowing your level of charge, your consumption and the power delivered by the charger your are at
    # distance in meter
    # charge in %
    # capacity in kWh
    # csmpt in kWh/100km
    # power in kW
    def chargingTime(self, dist, charge, capacity, csmpt, power):
        #Compute the energy that is necessary to travel the distance + 10% (in kWh)
        energy = (csmpt/1e5)*dist

        #Compute the time needed to charge (in hours)
        if power > 200:
            power = 160
        elif power > 40:
            power = 40

        if energy < (charge*capacity)/100:
            time = 0
        else:
            time = energy/power

        return time

    def travelTime(self, x, y):
        speed = 80000 #in m/hours
        op = OptimStations()
        distance = op.distanceBetween(x, y)
        time = distance/speed #in hours

        return time

    #This function gives the id of the stations someone with low carburant (or making a long trip) has
    # to go through to get to his destination in a minimum amount of time
    def fastestPath(self, dep_pos, des_pos, ev_csmpt, ev_capacity, ev_charge, des_time, closeness):

        max_distance = (float(ev_capacity)/ev_csmpt)*1e5
        #First we select the station that are along the path
        stations = self.onTheWay(dep_pos, des_pos, des_time, closeness)
        op = OptimStations()

        #Add all the vertexes to the graph
        g = Graph()
        g.add_vertex('dep')
        g.add_vertex('des')
        for station in stations:
            g.add_vertex(str(station[0]))

        #Add all the links and their weight
        dist_dep_des = op.distanceBetween(dep_pos, des_pos)
        if dist_dep_des < max_distance:
            weight = self.travelTime(dep_pos, des_pos) + self.chargingTime(dist_dep_des, ev_charge, ev_capacity, ev_csmpt, 3)
            g.add_edge('dep', 'des', weight)

        for station in stations:
            #Link all the station to the departure and destination if possible
            dist_dep = op.distanceBetween(dep_pos, [station[2], station[3]])
            if dist_dep < max_distance:
                # Compute the weight (in hours)
                weight = self.travelTime(dep_pos, [station[2],station[3]]) + self.chargingTime(dist_dep, ev_charge, ev_capacity, ev_csmpt, 3)
                g.add_edge('dep', str(station[0]), weight)

            dist_des =  op.distanceBetween(des_pos, [station[2], station[3]])
            if dist_des < max_distance:
                # Compute the weight (in hours)
                weight = self.travelTime(des_pos, [station[2],station[3]]) + self.chargingTime(dist_des, 0, ev_capacity, ev_csmpt, station[4])
                g.add_edge(str(station[0]), 'des', weight)

            #Connect the station to all other station that are accesible and forwarding
            for next_station in stations:
                dist_next_to_des = op.distanceBetween(des_pos, [next_station[2], next_station[3]])
                dist_to_next = op.distanceBetween([station[2], station[3]], [next_station[2], next_station[3]])
                if dist_to_next < max_distance and dist_next_to_des < dist_des:
                    # Compute the weight (in hours)
                    weight = self.travelTime([station[2],station[3]], [next_station[2],next_station[3]])\
                             + self.chargingTime(dist_to_next, 0, ev_capacity, ev_csmpt, station[4])
                    g.add_edge(str(station[0]), str(next_station[0]), weight)

        #Compute the shortest path
        dijkstra(g, g.get_vertex('dep'), g.get_vertex('des'))
        target = g.get_vertex('des')
        path = [target.get_id()]
        shortest(target, path)

        #Get the stations through which you have to pass
        stations = []
        for i in range(1, len(path)-1):
            stations.insert(0, int(path[i]))

        #print "You have to pass through station " + str(stations)

        #Compute different times
        # 1) Without stop
        straight_time = self.travelTime(dep_pos, des_pos)
        print "Time without stop is: " + str(straight_time) + " hours"

        # 2) Time with the different stops
        w = g.get_vertex('des')
        print "Time with the stops is: " + str(w.get_distance()) + " hours"

        lost_time = w.get_distance() - straight_time
        return [stations, lost_time]


    def dateTimeToTime (self, dateTime):
        time = str(dateTime.time()).split(':', 2)
        time = float(time[0]) + float(time[1])/60 + float(time[2])/3600
        return time



    def displayFastestPath(self, nb_vehicles, closeness):

        lost_times = []
        stations_info = []
        vehicles = []
        destinations = []
        try:
            #Get all the stations
            db = pymysql.connect("localhost", "root", "", "hive")
            cursor = db.cursor()
            request1 = "SELECT * FROM power_station"
            request2 = "SELECT * FROM vehicles"
            request3 = "SELECT * FROM destinations"
            cursor.execute(request1)
            stations_info = cursor.fetchall()
            cursor.execute(request2)
            vehicles = cursor.fetchall()
            cursor.execute(request3)
            destinations = cursor.fetchall()
            db.close()
        except:
            print "Unable to fetch data"

        op = OptimStations()
        mymap = gmplot.GoogleMapPlotter(50.8550624, 4.3053506, 8)
        random_ev = [random.randrange(1, len(vehicles)) for _ in range(nb_vehicles)]
        for id in random_ev:

            # !!!! A BOUGER: UTILISER POUR SIMULER UNE CHARGE PLUS FAIBLE
            charge = vehicles[id][4]/5

            dep_pos = destinations[id][2].split(',')
            des_pos = destinations[id][3].split(',')
            des_time = self.dateTimeToTime(destinations[id][1])
            result = self.fastestPath(dep_pos, des_pos, vehicles[id][2], vehicles[id][1], charge,
                                        des_time, closeness)
            stations_path = result[0]
            lost_times.append(result[1])

            #Fetch the info about the stations
            stations_path_info = []
            for i in stations_path:
                stations_path_info.append(stations_info[int(i)-1])

            #Display info on a map
            if  len(stations_path_info) == 0:
                dist = op.distanceBetween(dep_pos, des_pos)
                charging = self.chargingTime(dist, charge, vehicles[id][1], vehicles[id][2], 3)
                title = "DepartforEV" + str(id)
                text = "<h3 style = \"text-align:center;\">" + title + "</h3><h4> HomeStation </h4>Charging time: " \
                           + str(charging) + " hours<br/>Power: 3 kW<h4> Vehicule </h4>Capacity: " + str(vehicles[id][1]) + \
                           " kWh<br/>Charge: " + str(charge) + " %%<br/>Consumption: " + str(vehicles[id][2]) \
                           + " kWh/100km<br/>Position: " + str(dep_pos)  + "<br/>Destination: " +  str(des_pos)

                mymap.marker(dep_pos[0], dep_pos[1], destinations[id][3], title=title, text=text, c="#00FF00")
            else:
                cur = 0
                for station in stations_path_info:
                    #If we reach the last station before destination
                    if cur == len(stations_path_info)-1:
                        dist = op.distanceBetween([station[2], station[3]], des_pos)
                        charging = self.chargingTime(dist, 0, vehicles[id][1], vehicles[id][2], station[4])
                        title = "Station" + str(station[0]) + "forEV" + str(id)
                        text = "<h3 style = \"text-align:center;\">" + title + "</h3>Charging time: " + str(charging)+\
                               " hours<br/>Power: " + str(station[4]) + " kW<br/>Position: " + str(station[2]) \
                               + ", " + str(station[3])
                        mymap.marker(station[2], station[3], destinations[id][3], title=title, text=text, c="#FF0000")
                    if cur == 0:
                        stat_pos = str(station[2]) + ", " + str(station[3])
                        dist = op.distanceBetween(dep_pos, [station[2], station[3]])
                        charging = self.chargingTime(dist, charge, vehicles[id][1], vehicles[id][2], 3)
                        title = "DepartforEV" + str(id)
                        text = "<h3 style = \"text-align:center;\">" + title + "</h3><h4> HomeStation </h4>Charging time: " \
                           + str(charging) + " hours<br/>Power: 3 kW<h4> Vehicule </h4>Capacity: " + str(vehicles[id][1]) + \
                           " kWh<br/>Charge: " + str(charge) + " %%<br/>Consumption: " + str(vehicles[id][2]) \
                           + " kWh/100km<br/>Position: " + str(dep_pos)  + "<br/>Destination: " +  str(des_pos)
                        mymap.marker(dep_pos[0], dep_pos[1], stat_pos, title=title, text=text, c="#00FF00")
                    else:
                        next_station = stations_path_info[cur+1]
                        nxt_stat_pos = str(next_station[2]) + ", " + str(next_station[3])
                        dist = op.distanceBetween([station[2], station[3]], nxt_stat_pos)
                        charging = self.chargingTime(dist, 0, vehicles[id][1], vehicles[id][2], station[4])
                        title = "Station" + str(station[0]) + "forEV" + str(id)
                        text = "<h3 style = \"text-align:center;\">" + title + "</h3>Charging time: " + str(charging) +\
                               " hours<br/>Power: " + str(station[4]) + " kW<br/>Position: " + str(station[2]) \
                               + ", " + str(station[3])
                        mymap.marker(station[2], station[3], nxt_stat_pos, title=title, text=text, c="#FF0000")

            title = "DestforEV" + str(id)
            text = "<h3 style = \"text-align:center;\">" + title + "</h3>Position: " + str(des_pos)
            mymap.marker(des_pos[0], des_pos[1], title=title, text=text, c="#FFFF00")

        #Print statistics
        average = sum(lost_times)/len(lost_times)
        print "The average lost time is " + str(average) + " hours for " + str(nb_vehicles) + " vehicles."

        if len(lost_times) > 1:
            variance = statistics.variance(lost_times)
            print "The variance of lost time is " + str(variance) + " hours for " + str(nb_vehicles) + " vehicles."

        #Print statistics for deviated vehicles
        dev_lost_times = []
        for i in lost_times:
            if i != float(0):
                dev_lost_times.append(i)

        if len(dev_lost_times) != 0:
            dev_average = sum(dev_lost_times)/len(dev_lost_times)
            print "The average lost time is " + str(dev_average) + " hours for " + str(len(dev_lost_times)) + " deviated vehicles."

            if len(dev_lost_times) != 1:
                dev_variance = statistics.variance(dev_lost_times)
                print "The variance of lost time is " + str(dev_variance) + " hours for " + str(len(dev_lost_times)) + " deviated vehicles."

        mymap.draw('./mymap.html', 'AIzaSyBj7JAQHEc-eFQkfuCXBba0dItAUPL0fMI')


sotg = StationsOnTheGo()
#sol = sotg.fastestPath([50.9058436133, 4.55486282443], [51.2472636991, 3.03663216625], 18, 60, 50, 2)
#sotg.fastestPath([50.9058436133, 4.55486282443], [51.2472636991, 3.03663216625], 18, 10, 50, 0.5)
sotg.displayFastestPath(1, 2)
