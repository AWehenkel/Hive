import MySQLdb
import random
import datetime

request = "SELECT COUNT(id_vehicle) AS counter FROM destinations"
db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
cursor = db.cursor()
try:
    cursor.execute(request)
    data = cursor.fetchone()
    for i in range(1, data[0] + 1):
        arrival_time = random.randrange(8, 16)
        duration = random.randrange(1, 18 - arrival_time)
        request = "SELECT capacity, charge FROM vehicles WHERE id=%d" % i
        cursor.execute(request)
        car = cursor.fetchone()
        energy_to_charge = float(100 - car[1]) * float(car[0])/100
        request = "UPDATE destinations SET torecharge=%f, duration=%d, des_time='%s' WHERE id_vehicle=%d" % (energy_to_charge, duration, datetime.datetime(2016, 9, 28, arrival_time), i)
        print request
        cursor.execute(request)
except:
    print "pas ok"

db.commit()
