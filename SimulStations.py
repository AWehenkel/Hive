import json
import datetime
import MySQLdb
import OptimStations
import random
import PowerSlotManager
# This class can be used to simulate vehicle using the algorithm at different time
class SimulStations:

    def __init__(self):
        request1 = "SELECT * FROM destinations WHERE enough_fuel"
        request2 = "SELECT * FROM power_station"
        self.power_slot_manager = PowerSlotManager.PowerSlotManager()
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        try:
            cursor.execute(request1)
            self.nb_cars = cursor.rowcount
            cursor.execute(request2)
            self.nb_stations = cursor.rowcount
        except:
            print "problem"

    def autonomy(self, id_vehicle):
        request = "SELECT capacity, consumption, charge FROM vehicles WHERE id = %d" % id_vehicle
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        try:
            cursor.execute(request)
            result = cursor.fetchone()
            return ((float(result[0])*float(result[2])/100.0)/float(result[1]) * 1e5)
        except:
            print "error in autonomy"

    def updateFuel(self):
        request = "SELECT * FROM destinations"
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        try:
            cursor.execute(request)
            destinations = cursor.fetchall()
            for destination in destinations:
                autonomy = self.autonomy(destination[0])
                vehicle = destination[2].split(', ')
                lat2 = float(vehicle[0])
                lng2 = float(vehicle[1])
                vehicle = destination[3].split(', ')
                lat1 = float(vehicle[0])
                lng1 = float(vehicle[1])
                optimiser = OptimStations.OptimStations()
                distance = optimiser.distanceBetween((lat1, lng1), (lat2, lng2))
                if(distance > 30000):
                    print distance
                    print autonomy
                    print destination[0]
                if(distance > autonomy):
                    request = "UPDATE destinations SET enough_fuel=0 WHERE id_vehicle=%d" % destination[0]
                else:
                    request = "UPDATE destinations SET enough_fuel=1 WHERE id_vehicle=%d" % destination[0]
                cursor.execute(request)
        except:
            print "updateDFuel problem"
        db.commit()

    #Books a station
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

    #Returns all the data of the table reservation
    def __getBookingInfo(self):
        request = "SELECT id_vehicle FROM power_slot WHERE id_vehicle > 0 GROUP BY id_vehicle"
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        try:
            cursor.execute(request)
            db.close()
            return cursor.fetchall()
        except:
            print "error booking info"
            return 0

    # Put a certain number of user in a simulation and return the number of user without reservation
    def addUser(self, nb_user):
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()

        booking_info = self.__getBookingInfo()
        self.user_registered = []
        self.station_registered = []
        for reservation in booking_info:
            self.user_registered.append(int(reservation[0]))

        if booking_info:
            request = "SELECT * FROM destinations WHERE enough_fuel AND id_vehicle NOT IN (%s) ORDER BY RAND() LIMIT %d" % (str(self.user_registered)[1:-1], nb_user)
        else:
            request = "SELECT * FROM destinations WHERE enough_fuel ORDER BY RAND() LIMIT %d" % (nb_user)
        print request

        try:
            cursor.execute(request)
            vehicles = cursor.fetchall()
        except:
            print "error in adduser"
            return -1
        return self.__optAndBook(vehicles, 1)

    # Computes all the detour that will be done, detour are read from the reservation table
    def calculateDetour(self):
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        request = "SELECT id_station, id_vehicle FROM reservation"
        cursor.execute(request)
        datas = cursor.fetchall()
        distance_totale = []
        i = 0
        for data in datas:
            id_station = data[0]
            id_vehicle = data[1]
            request = "SELECT lat, lng FROM power_station WHERE id = %d" % id_station
            cursor.execute(request)
            station = cursor.fetchone()
            request = "SELECT des_pos FROM destinations WHERE id_vehicle = %d" % id_vehicle
            cursor.execute(request)
            da = cursor.fetchone()
            vehicle = da[0].split(', ')
            lat2 = float(vehicle[0])
            lng2 = float(vehicle[1])
            optimiser = OptimStations.OptimStations()
            distance = optimiser.distanceBetween(station, (lat2, lng2))
            distance_totale.append(distance)
            i += 1

        return distance_totale


    #IN: vehicles: A list of vehicles as represented in the database
    #    percentage_booking: The probability for a vehicle to book a station.
    #OUT: the number of car without registration, register in the reservation table all the car that has a reservation
    def __optAndBook(self, vehicles, percentage_booking):
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()

        optimiser = OptimStations.OptimStations()
        min_power = 15 #In the futur let the user choose the minimal power and the sorting criteria

        print len(vehicles)
        problem = {}
        print "creation of the graph"
        id = 0
        #Creation of the graph
        for vehicle in vehicles:
            problem[vehicle[0]] = vehicle[4]
            id += 1
            print id
            close_stations = json.loads(vehicle[4])
            min_power = float(vehicle[7])/float(vehicle[8])
            stations = optimiser.sortAndFilterStations(close_stations, min_power, vehicle[1], vehicle[8])
            print id
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
        print "graph created"
        print "creates the spanning tree"
        # Register the result of the spanning tree
        st = optimiser.registerProposedStations()
        print "spanning tree created"
        #Retrieve data of station already
        # Affection of a station for each vehicle
        id = 0
        for vehicle in st:
            id += 1
            print id
            if vehicle and random.random() < percentage_booking:
                #data about vehicle
                request = "SELECT duration, des_time FROM destinations WHERE id_vehicle=%d" % id
                cursor.execute(request)
                car = cursor.fetchone()
                vehicle.sort(key=lambda tup: tup[1])
                begin_time = datetime.datetime.strptime(str(car[1]), "%Y-%m-%d %H:%M:%S")
                hour_begin = begin_time.hour

                #Faire un tri des station_proposed en fontion du critere que l'on veut, pour le moment il s'agit uniquement de la distance(utiliser
                #sort and filter

                for station_proposed in vehicle:
                    if self.isFreeStation(station_proposed[0], car[1], car[0]):
                        for slot in range(0, car[0]):
                            request = "SELECT min(id) FROM power_slot WHERE id_station=%d AND begin_time=%d" % (station_proposed[0], hour_begin + slot)
                            cursor.execute(request)
                            id_slot = cursor.fetchone()
                            request = "UPDATE power_slot SET id_vehicle=%d WHERE id=%d" % (id, id_slot[0])
                            cursor.execute(request)
                        db.commit()
                        problem.__delitem__(id)
                        break
        # Reserve a station not chosen by the spanning tree
        for key in problem.keys():
            for vehicle in vehicles:
                if vehicle[0] == key:
                    request = "SELECT duration, des_time FROM destinations WHERE id_vehicle=%d" % id
                    cursor.execute(request)
                    car = cursor.fetchone()
                    begin_time = datetime.datetime.strptime(str(car[1]), "%Y-%m-%d %H:%M:%S")
                    hour_begin = begin_time.hour
                    close_stations = json.loads(vehicle[4])
                    #stations = optimiser.sortAndFilterStations(close_stations, 0, order="power")
                    #Faire un tri des stations.
                    stations = close_stations
                    for station_proposed in stations:
                        if self.isFreeStation(station_proposed[0], car[1], car[0]):
                            for slot in range(0, car[0]):
                                request = "SELECT min(id) FROM power_slot WHERE id_station=%d AND begin_time=%d" % (
                                station_proposed[0], hour_begin + slot)
                                cursor.execute(request)
                                id_slot = cursor.fetchone()
                                request = "UPDATE power_slot SET id_vehicle=%d WHERE id=%d" % (key, id_slot[0])
                                cursor.execute(request)
                            db.commit()
                            problem.__delitem__(key)
                            break
                    break

        request = "TRUNCATE TABLE graph_station_vehicle"
        cursor.execute(request)
        db.commit()
        return len(problem)

    def computeStats(self, size):
        nb_step = self.nb_cars/size + 1
        number = 0
        print nb_step
        for i in range(0, nb_step):
            number = t.addUser(size + number)
        detours = self.calculateDetour()
        square_sum = 0.0
        sums = 0.0
        for i in detours:
            square_sum += i**2.0
            sums += i
        mean = sums/len(detours)
        square_mean = square_sum/len(detours)
        variance = square_mean - mean**2.0
        ecart_type = variance**(0.5)
        print "resultats pour des packet de %d voitures et nombre de station de %d" % (size, self.nb_stations)
        print "detour total: %f" % sums
        print "nbre de voiture avec une station: %d" % len(detours)
        print "nbre de voiture total: %d" % self.nb_cars
        print "detour moyen: %f" % mean
        print "variance: %f, E-T: %f" % (variance, ecart_type)


    def isFreeStation(self, id_station, time_slot, nb_slot):
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        begin_time = datetime.datetime.strptime(str(time_slot), "%Y-%m-%d %H:%M:%S")
        hour_begin = begin_time.hour
        return self.power_slot_manager.isFree(id_station, hour_begin, nb_slot)



t = SimulStations()
#t.updateFuel()
t.computeStats(50)