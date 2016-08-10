import pymysql
from OptimStations import *
from data.towns import *
import gmplot
from Dijkstra import *


class StationsOnTheGo:

    #Determines the station that are situated on the way between two locations
    #The smaller closeness is, the less station you will get
    def onTheWay (self, x, y, closeness):

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
        med_distances[0] = op.twoPointsDistance(x, med_points[0])
        med_distances[1] = op.twoPointsDistance(x, med_points[1])

        # Compute the distance between the two points and the data for the third circle
        distance = op.twoPointsDistance(x, y)
        center = [(x[0]+y[0])/2, (x[1]+y[1])/2]
        mymap.marker(float(center[0]), float(center[1]),title="Center", c="#00FF00")

        #Select the stations that are in the two circles
        selected_stations = []
        for station in stations:
            dist_to_center = op.twoPointsDistance(center, [station[2], station[3]])
            dist_to_med0 = op.twoPointsDistance(med_points[0], [station[2], station[3]])
            dist_to_med1 = op.twoPointsDistance(med_points[1], [station[2], station[3]])

            if dist_to_center < distance/2 and dist_to_med0 < med_distances[0] and dist_to_med1 < med_distances[1]:
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

        mymap = gmplot.GoogleMapPlotter(x[0], x[1], 8)
        op = OptimStations()
        distance = op.twoPointsDistance(x, y)
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
            distance1 = op.twoPointsDistance(point, x)
            distance2 = op.twoPointsDistance(point,y)
            if (math.fabs(distance1-distance2)) < tresh:
                ok_points.append(point)

        #Keep the two points that are the furthest away from the center
        max = 0
        chosen_point1 = ok_points[0]
        for point in ok_points:
            dist = op.twoPointsDistance(point, center)
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
        distance = op.twoPointsDistance(x, y)
        time = distance/speed #in hours

        return time

    #This function gives the id of the stations someone with low carburant (or making a long trip) has
    # to go through to get to his destination in a minimum amount of time
    def fastestPath(self, dep_pos, des_pos, ev_csmpt, ev_capacity, ev_charge, closeness):

        max_distance = (float(ev_capacity)/ev_csmpt)*1e5
        #First we select the station that are along the path
        stations = self.onTheWay(dep_pos, des_pos, closeness)
        op = OptimStations()

        #Add all the vertexes to the graph
        g = Graph()
        g.add_vertex('dep')
        g.add_vertex('des')
        for station in stations:
            g.add_vertex(str(station[0]))

        #Add all the links and their weight
        dist_dep_des = op.twoPointsDistance(dep_pos, des_pos)
        if dist_dep_des < max_distance:
            weight = self.travelTime(dep_pos, des_pos) + self.chargingTime(dist_dep_des, ev_charge, ev_capacity, ev_csmpt, 3)
            g.add_edge('dep', 'des', weight)

        for station in stations:
            #Link all the station to the departure and destination if possible
            dist_dep = op.twoPointsDistance(dep_pos, [station[2],station[3]])
            if dist_dep < max_distance:
                # Compute the weight (in hours)
                weight = self.travelTime(dep_pos, [station[2],station[3]]) + self.chargingTime(dist_dep, ev_charge, ev_capacity, ev_csmpt, 3)
                g.add_edge('dep', str(station[0]), weight)

            dist_des =  op.twoPointsDistance(des_pos, [station[2],station[3]])
            if dist_des < max_distance:
                # Compute the weight (in hours)
                weight = self.travelTime(des_pos, [station[2],station[3]]) + self.chargingTime(dist_des, 0, ev_capacity, ev_csmpt, station[4])
                g.add_edge(str(station[0]), 'des', weight)

            #Connect the station to all other station that are accesible and forwarding
            for next_station in stations:
                dist_next_to_des = op.twoPointsDistance(des_pos, [next_station[2],next_station[3]])
                dist_to_next = op.twoPointsDistance([station[2],station[3]], [next_station[2],next_station[3]])
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

        print "You have to pass through station " + str(stations)

        #Compute different times
        # 1) Without stop
        straight_time = self.travelTime(dep_pos, des_pos)
        print "Time without stop is: " + str(straight_time) + " hours"

        # 2) Time with the different stops
        w = g.get_vertex('des')
        print "Time with the stops is: " + str(w.get_distance()) + " hours"



sotg = StationsOnTheGo()
#sol = sotg.fastestPath([50.9058436133, 4.55486282443], [51.2472636991, 3.03663216625], 18, 60, 50, 2)
sotg.fastestPath([50.9058436133, 4.55486282443], [51.2472636991, 3.03663216625], 18, 10, 50, 0.5)
