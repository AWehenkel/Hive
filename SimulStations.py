import json

import MySQLdb
import OptimStations
import random

class SimulStations:

    def __bookStation(self, id_station, id_user):
        request = "INSERT INTO reservation(id_station, id_vehicle) VALUES(%d, %d)" % (id_station, id_user)
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        try:
            cursor.execute(request)
            db.commit()
            db.close()
        except:
            print "error booking"

    def __getBookingInfo(self):
        request = "SELECT * FROM reservation"
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        try:
            cursor.execute(request)
            db.close()
            return cursor.fetchall()
        except:
            print "error booking info"
            return 0

    def addUser(self, nb_user):
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()

        booking_info = self.__getBookingInfo()
        self.user_registered = []
        self.station_registered = []
        for reservation in booking_info:
            self.station_registered.append(reservation[0])
            self.user_registered.append(int(reservation[1]))

        if booking_info:
            request = "SELECT * FROM destinations WHERE id_vehicle NOT IN (%s) LIMIT %d" % (str(self.user_registered)[1:-1], nb_user)
        else:
            request = "SELECT * FROM destinations LIMIT %d" % (nb_user)
        try:
            cursor.execute(request)
            vehicles = cursor.fetchall()
        except:
            print "error in adduser"
            return -1
        self.__optAndBook(vehicles, 1)

    def calculateDetour(self):
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        request = "SELECT * FROM reservation"
        cursor.execute(request)
        datas = cursor.fetchall()
        distance_totale = 0.0
        for data in datas:
            id_station = data[0]



    def __optAndBook(self, vehicles, percentage_booking):
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()

        optimiser = OptimStations.OptimStations()
        min_power = 15 #In the futur let the user choose the minimal power and the sorting criteria

        print len(vehicles)
        problem = {}
        #Creation of the graph
        for vehicle in vehicles:
            problem[vehicle[0]] = vehicle[4]
            close_stations = json.loads(vehicle[4])
            stations = optimiser.sortAndFilterStations(close_stations, min_power)
            for station in stations:
                weight = 1000
                for close in close_stations:
                    if(close[0] == station[0]):
                        weight = close[1]
                        break
                request = "INSERT INTO graph_station_vehicle(id_vehicle, id_station, weight) VALUES (%d, %d, %f)" % (vehicle[0], station[0], weight)
                try:
                    cursor.execute(request)
                except:
                    print "error in acces db optandbook"
        db.commit()

        # Register the result of the spanning tree
        st = optimiser.registerProposedStations()

        #Retrieve data of station already
        # Affection of a station for each vehicle
        id = 0
        for vehicle in st:
            id += 1
            if vehicle and random.random() < percentage_booking:

                vehicle.sort(key=lambda tup: tup[1])
                for station_proposed in vehicle:
                    if station_proposed[0] not in self.station_registered:
                        request = "INSERT INTO reservation(id_station, id_vehicle) VALUES (%d, %d)" % (station_proposed[0], id)
                        cursor.execute(request)
                        request = "DELETE FROM graph_station_vehicle WHERE id_vehicle=%d" % (id)
                        cursor.execute(request)
                        request = "DELETE FROM graph_station_vehicle WHERE id_station=%d" % (station_proposed[0])
                        cursor.execute(request)
                        self.station_registered.append(station_proposed[0])
                        problem.__delitem__(id)
                        break
        # Reserve a station not chosen by the spanning tree
        for key in problem.keys():
            for vehicle in vehicles:
                if vehicle[0] == key:
                    close_stations = json.loads(vehicle[4])
                    stations = optimiser.sortAndFilterStations(close_stations, 0, order="power")
                    for station_proposed in stations:
                        if station_proposed[0] not in self.station_registered:
                            request = "INSERT INTO reservation(id_station, id_vehicle) VALUES (%d, %d)" % (
                            station_proposed[0], key)
                            cursor.execute(request)
                            request = "DELETE FROM graph_station_vehicle WHERE id_vehicle=%d" % (key)
                            cursor.execute(request)
                            request = "DELETE FROM graph_station_vehicle WHERE id_station=%d" % (station_proposed[0])
                            cursor.execute(request)
                            self.station_registered.append(station_proposed[0])
                            problem.__delitem__(key)
                            break
        print "%d vehicule sans stations" % len(problem)

        db.commit()


t = SimulStations()
t.addUser(3800)