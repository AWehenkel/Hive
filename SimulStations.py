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
                optimiser = OptimStations.OptimStations(self.power_slot_manager)
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
    def addUser(self, nb_user, type_algo, tri = "distance"):
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

        try:
            cursor.execute(request)
            vehicles = cursor.fetchall()
        except:
            print "error in adduser"
            return -1
        if(type_algo == "s-tree"):
            print 'ok'
            return self.__optAndBook(vehicles, 1, tri)
        else:
            return self.bookRandomly(vehicles)

    # Computes all the detour that will be done, detour are read from the reservation table
    def calculateDetour(self):
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        request = "SELECT id_station, id_vehicle, power, COUNT(begin_time) AS nb_slot FROM power_slot WHERE id_vehicle > 0 GROUP BY id_vehicle, id_station"
        cursor.execute(request)
        datas = cursor.fetchall()
        distance_totale = []
        energy_recharged = []
        percentage_recharged = []
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
            optimiser = OptimStations.OptimStations(self.power_slot_manager)
            distance = optimiser.distanceBetween(list((station[0], station[1])), list((lat2, lng2)))
            distance_totale.append(distance)
            request = "SELECT capacity, charge FROM vehicles WHERE id = %d" % id_vehicle
            cursor.execute(request)
            da = cursor.fetchone()
            energy_max = float(100-da[1])/100.0 * float(da[0])
            energy_charged = data[3] * data[2]
            energy_recharged.append(min(energy_charged, energy_max))
            percentage_recharged.append(float(min(energy_charged, energy_max))/float(energy_max))
            i += 1

        return (distance_totale, energy_recharged, percentage_recharged)


    #IN: vehicles: A list of vehicles as represented in the database
    #    percentage_booking: The probability for a vehicle to book a station.
    #OUT: the number of car without registration, register in the reservation table all the car that has a reservation
    def __optAndBook(self, vehicles, percentage_booking, weight_type = "distance"):
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()

        optimiser = OptimStations.OptimStations(self.power_slot_manager)
        min_power = 15 #In the futur let the user choose the minimal power and the sorting criteria

        print len(vehicles)
        problem = {}
        print "creation of the graph"
        id = 0
        #Creation of the graph
        for vehicle in vehicles:
            problem[vehicle[0]] = vehicle[4]
            id += 1
            close_stations = json.loads(vehicle[4])
            min_power = float(vehicle[7])/float(vehicle[8])
            stations = optimiser.sortAndFilterStations(close_stations, min_power, vehicle[1], vehicle[8])
            for station in stations:
                weight = 1000
                for close in close_stations:
                    if(close[0] == station[0]):
                        if(weight_type == "distance"):
                            weight = close[1]
                        else: #(weight_type == "power"):
                            weight = abs(close[2][0] - min_power)
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
            if vehicle and random.random() < percentage_booking:
                #data about vehicle
                request = "SELECT duration, des_time FROM destinations WHERE id_vehicle=%d" % id
                cursor.execute(request)
                car = cursor.fetchone()
                vehicle.sort(key=lambda tup: tup[1])
                begin_time = datetime.datetime.strptime(str(car[1]), "%Y-%m-%d %H:%M:%S")
                hour_begin = begin_time.hour

                for station_proposed in vehicle:
                    if self.isFreeStation(station_proposed[0], car[1], car[0]):
                        self.power_slot_manager.bookSlot(station_proposed[0], hour_begin, car[0], id)
                        problem.__delitem__(id)
                        break
        # Reserve a station not chosen by the spanning tree
        for key in problem.keys():
            for vehicle in vehicles:
                if vehicle[0] == key:
                    request = "SELECT duration, des_time, torecharge, duration FROM destinations WHERE id_vehicle=%d" % id
                    cursor.execute(request)
                    car = cursor.fetchone()
                    begin_time = datetime.datetime.strptime(str(car[1]), "%Y-%m-%d %H:%M:%S")
                    hour_begin = begin_time.hour
                    close_stations = json.loads(vehicle[4])
                    best_power = float(car[2])/float(car[3])
                    self.sortStations(close_stations, weight_type, best_power)
                    stations = close_stations
                    for station_proposed in stations:
                        if self.isFreeStation(station_proposed[0], car[1], car[0]):
                            self.power_slot_manager.bookSlot(station_proposed[0], hour_begin, car[0], key)
                            problem.__delitem__(key)
                            break
                    break

        request = "TRUNCATE TABLE graph_station_vehicle"
        cursor.execute(request)
        db.commit()
        return len(problem)
    def sortStations(self, stations, order, power = 0):
        if(order == "distance"):
            stations.sort(key=lambda tup: tup[1])
        else:#if(order == "power"):
            stations.sort(key=lambda tup: abs(tup[2][0] - power))

    def computeStats(self, type_algo = "s-tree"):
        simulations = ["distance", "power"]
        for sim in simulations:
            type_weight = sim
            for size in [500, 1000, 3800]:
                nb_voiture_list = [0]
                mean_distance_list = [0]
                et_distance_list = [0]
                percentage_power_list = [0]
                percentage_et_list = [0]
                for i in range(0, 5):
                    t2 = PowerSlotManager.PowerSlotManager()
                    t2.resetBooking()
                    self.power_slot_manager = PowerSlotManager.PowerSlotManager()
                    nb_step = self.nb_cars/size + 1
                    number = 0
                    print nb_step
                    for i in range(0, nb_step):
                        number = t.addUser(size + number, type_algo, type_weight)
                    detours = self.calculateDetour()
                    square_sum = 0.0
                    sums = 0.0
                    percentage_power = 0.0
                    square_percentage = 0.0
                    for i in detours[0]:
                        square_sum += i**2.0
                        sums += i
                    for i in detours[2]:
                        percentage_power += i/len(detours[2])
                        square_percentage += i**2.0/len(detours[2])
                    mean = sums/len(detours[0])
                    square_mean = square_sum/len(detours[0])
                    variance = square_mean - mean**2.0
                    variance_percentage = square_percentage - percentage_power**2.0
                    #variance = 0
                    ecart_type = variance**(0.5)
                    print "resultats pour des packet de %d voitures et nombre de station de %d" % (size, self.nb_stations)
                    print "nbre de voiture avec une station: %d" % len(detours[0])
                    nb_voiture_list.append(len(detours[0]))
                    print "nbre de voiture total: %d" % self.nb_cars
                    print "detour moyen: %f" % mean
                    mean_distance_list.append(mean)
                    print "variance: %f, E-T: %f" % (variance, ecart_type)
                    et_distance_list.append(ecart_type)
                    print "percentage moyen recharge: %f" % percentage_power
                    percentage_power_list.append(percentage_power)
                    print "variance du pourcentage: %f et ET: %f" % (variance_percentage, variance_percentage**0.5)
                    percentage_et_list.append(variance_percentage**0.5)

                print "-------- Resultat pour %s ---------" % sim
                mean = reduce(lambda x,y: x + y, nb_voiture_list) / float(len(nb_voiture_list) - 1)
                et = reduce(lambda x,y: x + y**2.0, nb_voiture_list) / float(len(nb_voiture_list) - 1) - mean**2.0
                print "nbre de voiture avec une station: mean : %f ET : %f" % (mean, et)
                mean = reduce(lambda x, y: x + y, mean_distance_list) / float(len(mean_distance_list) - 1)
                et = reduce(lambda x, y: x + y ** 2.0, mean_distance_list) / float(len(mean_distance_list) - 1) - mean ** 2.0
                print "detour moyen: mean : %f ET : %f" % (mean, et)
                mean = reduce(lambda x, y: x + y, et_distance_list) / float(len(et_distance_list) - 1)
                et = reduce(lambda x, y: x + y ** 2.0, et_distance_list) / float(
                    len(et_distance_list) - 1) - mean ** 2.0
                print "variance du detour: mean : %f ET : %f" % (mean, et)
                mean = reduce(lambda x, y: x + y, percentage_power_list) / float(len(percentage_power_list) - 1)
                et = reduce(lambda x, y: x + y ** 2.0, percentage_power_list) / float(
                    len(percentage_power_list) - 1) - mean ** 2.0
                print "percentage moyen recharge: mean : %f ET : %f" % (mean, et)
                mean = reduce(lambda x, y: x + y, percentage_et_list) / float(len(percentage_et_list) - 1)
                et = reduce(lambda x, y: x + y ** 2.0, percentage_et_list) / float(
                    len(percentage_et_list) - 1) - mean ** 2.0
                print "percentage moyen recharge: mean : %f ET : %f" % (mean, et)


    def isFreeStation(self, id_station, time_slot, nb_slot):
        begin_time = datetime.datetime.strptime(str(time_slot), "%Y-%m-%d %H:%M:%S")
        hour_begin = begin_time.hour
        return self.power_slot_manager.isFree(int(id_station), hour_begin, int(nb_slot))

    def bookRandomly(self, vehicles):
        print "random algo"
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        counter = 0
        c = 0
        for vehicle in vehicles:
            c += 1
            request = "SELECT closestations, duration, des_time FROM destinations WHERE id_vehicle=%d" % vehicle[0]
            cursor.execute(request)
            data = cursor.fetchone()
            type(data[2])
            begin_time = datetime.datetime.strptime(str(data[2]), "%Y-%m-%d %H:%M:%S")
            hour_begin = begin_time.hour
            stations = json.loads(data[0])
            if(len(stations) > 0):
                id = random.randrange(0, len(stations))
            while (len(stations) > 0 and not(self.isFreeStation(stations[id][0], data[2], data[1]))):
                stations.remove(stations[id])
                if(len(stations) > 0):
                    id = random.randrange(0, len(stations))
            if(len(stations) > 0 and self.isFreeStation(stations[id][0], data[2], data[1])):
                self.power_slot_manager.bookSlot(int(stations[id][0]), hour_begin, data[1], vehicle[0])
            else:
                counter += 1

        return counter


t = SimulStations()
#t.updateFuel()

t.computeStats()

