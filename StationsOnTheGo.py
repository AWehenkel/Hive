import pymysql
from OptimStations import *
from data.towns import *
import gmplot
from Dijkstra import *
import random
import statistics


'''
# This class contains functions used to determine the optimal traject for a vehicle
# that goes from a depart to a destination at a certain time and with certain
# characteristics (capacity, consumption, level of charge).
'''
class StationsOnTheGo:

    '''
    #Determines the stations that are situated on the way between two locations
    #PARAMETERS
    # x , [lat, long] of point x
    # y , [lat, long] of point y
    # dep_time, departure time
    # des_time, arrival time
    # closeness, the smaller this paramater, the closer to the path the stations will
    #            be selected
    '''
    def onTheWay (self, x, y, dep_time, des_time, closeness):

        x[0] = float(x[0]);y[0] = float(y[0]);  x[1] = float(x[1]); y[1] = float(y[1])

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

        # Compute the distance between the two points and determine the center
        op = OptimStations()
        distance = op.asTheCrowFlies(x, y)
        center = [(x[0]+y[0])/2, (x[1]+y[1])/2]
        mymap.marker(float(center[0]), float(center[1]),title="Center", c="#00FF00")

        #Generate two points on the mediatrice and compute their distance to the original points
        med_points = self.generatePointsAtSameDistance(x, y, closeness)
        med_distances = [0 for z in range(2)]
        med_distances[0] = op.asTheCrowFlies(x, med_points[0])
        med_distances[1] = op.asTheCrowFlies(x, med_points[1])

        #Select the stations that are situated in the cirle centered at the center and passing through
        # the points x and y and that are also in the circles centered at the two mediatrice points.
        #In addition, remove the stations that have no time slots available in the traject time.
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

    '''
    #Generate two points that are situated on the mediatrice of two given points
    #PARAMETERS
    # x, [lat, long]
    # y, [lat, long]
    # closeness, the smaller this parameter the further away the two points from the center
    '''
    def generatePointsAtSameDistance(self, x, y, closeness):

        x[0] = float(x[0]); x[1] = float(x[1]); y[0] = float(y[0]); y[1] = float(y[1])

        op = OptimStations()
        distance = op.asTheCrowFlies(x, y)
        center = [(x[0]+y[0])/2, (x[1]+y[1])/2]

        #Generate random points around the center and keep only the points that are situated
        #  at the same distance of x and y
        t = Towns(0.1)
        points = t.genRandomLocation(center[0], center[1], distance/closeness, int(distance/100))
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
        chosen_point2 = [center[0]-(float(chosen_point1[0])-center[0]), center[1]-(float(chosen_point1[1])-center[1])]

        '''
        mymap = gmplot.GoogleMapPlotter(x[0], x[1], 8)
        mymap.marker(float(x[0]), float(x[1]),title="Center", c="#00FF00")
        mymap.marker(float(y[0]), float(y[1]),title="Center", c="#00FF00")
        mymap.marker(float(center[0]), float(center[1]),title="Center", c="#00FF00")
        mymap.marker(float(chosen_point1[0]), float(chosen_point1[1]), title="Point", c="#000000")
        mymap.marker(float(chosen_point2[0]), float(chosen_point2[1]), title="Point", c="#000000")
        mymap.draw("./mymap.html", 'AIzaSyD0QmwrWQGk3YPqvYv7-iUxdqqK7Zh0MO4')
        '''

        return  [chosen_point1, chosen_point2]

    '''
    #This function gives how long you need to charge to reach a destination at a certain distance,
    # knowing your level of charge, your consumption and the power delivered by the charger your are at
    #PARAMETERS
    # dist, distance in meter
    # charge, charge level in %
    # capacity, capacity in kWh
    # csmpt, consumption in kWh/100km
    # power, power in kW
    '''
    def chargingTime(self, dist, charge, capacity, csmpt, power):
        #Compute the energy that is necessary to travel the distance (in kWh)
        energy = (csmpt/1e5)*dist

        #Compute the time needed to charge (in hours)
        if power > 200:
            power = 160
        elif power > 40:
            power = 40

        #If you already have enough energy, you don't wait at this station
        if energy < (charge*capacity)/100:
            time = 0
        else:
            time = energy/power
        return time

    '''
    #This function gives the time needed to travel from one position to another by car
    #PARAMETERS
    # x, [lat, long]
    # y, [lat, long]
    '''
    def travelTime(self, x, y):
        op = OptimStations()
        time = op.distanceBetween(x, y, option="time")
        return time

    '''
    #This function reserveres the appropriate time slots for a vehicle that leaves at a certain
    # time and that needs to stop at given stations at given times.
    #/!\ The stations should at least have one empty spot left at the time the vehicle reaches it
    # or the reservation will not be done
    #PARAMETERS
    # dep_time, departure time in hours
    # stations_n_time, list of [station_id, time] where time is the time to reach the station from
    #                  the departure
    '''
    def reserveSlots(self, dep_time, stations_n_time, id_vehicle):
        next_station_pos = []
        for station in stations_n_time:
            #Round the arrival time to get a full slot
            stat_arrival_time = int(round(dep_time + station[1]))
            if stat_arrival_time < 8:
                stat_arrival_time = 8

            try:
                db = pymysql.connect("localhost", "root", "", "hive")
                cursor = db.cursor()
                request = "UPDATE power_slot SET id_vehicle=%d WHERE id_station=%d AND id_vehicle=%d AND begin_time=%d" % (
                           id_vehicle,  station[0], -1, stat_arrival_time)
                cursor.execute(request)
                db.commit()
                db.close()
            except:
                print "Unable to update data"


    '''
    #This function gives the id of the stations someone with low carburant (or making a long trip) has
    # to go through to get to his destination in a minimum amount of time
    #PARAMETERS
    # dep_pos, [lat, long] of the departure
    # des_pos, [lat, long] of the destination
    # ev_id, electric vehicle identifier
    # ev_csmpt, consumption in kWh/100km
    # ev_capacity, capacity in kWh
    # ev_charge, charge level in %
    # des_time, time of arrival at the destination in hours
    # closeness, the smaller this parameter the less stations will be considered
    '''
    def fastestPath(self, dep_pos, des_pos, ev_id, ev_csmpt, ev_capacity, ev_charge, des_time, closeness):

        #First we select the station that are along the path
        #Compute the time to reach the destination
        op = OptimStations()
        time_to_reach = op.distanceBetween(dep_pos, des_pos, "Driving", option="time")
        dep_time = des_time - time_to_reach
        stations = self.onTheWay(dep_pos, des_pos, dep_time, des_time, closeness)

        #Add all the vertexes to the graph
        g = Graph()
        g.add_vertex('dep')
        g.add_vertex('des')
        for station in stations:
            g.add_vertex(str(station[0]))

        #Add all the links and their weight
        dist_dep_des = op.distanceBetween(dep_pos, des_pos)
        max_distance = (float(ev_capacity)/ev_csmpt)*1e5
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

            #Link the departure to all accesible stations
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
        stations_n_time = []
        for i in range(1, len(path)-1):
            w = g.get_vertex(path[i])
            time = w.get_distance()
            stations_n_time.insert(0, [int(path[i]), time])

        #Reserve the slots if you need a station
        if stations_n_time:
            #Recompute the real departure time
            w = g.get_vertex('des')
            dep_time = des_time - w.get_distance()
            self.reserveSlots(dep_time, stations_n_time, ev_id)

        #Compute different times
        # 1) Without stop
        straight_time = self.travelTime(dep_pos, des_pos)
        #print "Time without stop is: " + str(straight_time) + " hours"

        # 2) Time with the different stops
        w = g.get_vertex('des')
        #print "Time with the stops is: " + str(w.get_distance()) + " hours"

        lost_time = w.get_distance() - straight_time
        return [stations_n_time, lost_time]

    def dateTimeToTime (self, dateTime):
        time = str(dateTime.time()).split(':', 2)
        time = float(time[0]) + float(time[1])/60 + float(time[2])/3600
        return time

    '''
    #This function computes and displays the different stations that a series of vehicles has
    # to pass through to go from their departure to their destination.
    #PARAMETERS
    # nb_vehicles, the nb of vehicles to simulate
    '''
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
            result = self.fastestPath(dep_pos, des_pos, id, vehicles[id][2], vehicles[id][1], charge,
                                      des_time, closeness)

            stations_path_n_time = result[0]
            lost_times.append(result[1])

            #Fetch the info about the stations
            stations_path_info = []
            for station_n_time in stations_path_n_time:
                stations_path_info.append(stations_info[int(station_n_time[0])-1])

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
sotg.displayFastestPath(10, 0.5)
