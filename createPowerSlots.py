import MySQLdb
import random
import datetime

request = "SELECT id, nominal_power FROM power_station"
db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
cursor = db.cursor()

try:
    cursor.execute(request)
    data = cursor.fetchall()
    for station in data:
        power = station[1]/4
        if(power > 160):
            nb_supercharger = int(power/160)
            for i in range(0, nb_supercharger):
                for j in range(8, 19):
                    request = "INSERT INTO power_slot(id_station, power, begin_time) VALUES (%d, %f, %d)" % (station[0], 160, j)
                    cursor.execute(request)
        elif(power > 40):
            nb_charger = int(power/40)
            for i in range(0, nb_charger):
                for j in range(8, 19):
                    request = "INSERT INTO power_slot(id_station, power, begin_time) VALUES (%d, %f, %d)" % (
                    station[0], 40, j)
                    cursor.execute(request)
        else:
            for j in range(8, 19):
                request = "INSERT INTO power_slot(id_station, power, begin_time) VALUES (%d, %f, %d)" % (
                    station[0], power, j)
                cursor.execute(request)
except:
    print "pas ok"
db.commit()