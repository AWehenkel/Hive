import MySQLdb
import googlemaps
import math
import random
from data import Towns

#Generates a number of random gps points
def genRandomLocation(lat, lng, dist, number):
    lat = lat/180 * math.pi
    lng = lng/180 * math.pi
    rad_earth = 6372.796924
    random.seed()
    #Convert dist to radian
    dist = dist/rad_earth

    result = []
    for i in range(0, number):
        r1 = random.random()
        r2 = random.random()
        rand_dist = math.acos(r1*(math.cos(dist) - 1) + 1)
        brg = 2*math.pi*r2
        r_lat = math.asin(math.sin(lat)*math.cos(rand_dist) + math.cos(lat)*math.sin(rand_dist)*math.cos(brg))
        r_lon = lng + math.atan2(math.sin(brg)*math.sin(rand_dist)*math.cos(lat), math.cos(rand_dist)-math.sin(lat)*math.sin(lat))
        if (r_lon < -math.pi):
            r_lon += 2*math.pi

        result.append(str(r_lat * 180/math.pi) + ", " + str(r_lon * 180/math.pi))

    return result

# Open database connection
db = MySQLdb.connect("localhost","root","videogame2809","hive" )

towns = Towns.Towns(1)
pos = []
capa = 25, 30, 60, 80
consom = 18
request = 'INSERT INTO vehicles (capacity, consumption, position, charge, home) VALUES '
for town in towns.ville.values():
    capacity = 60
    consom = 18
    charge = 50
    pos = genRandomLocation(town["lat"],town["lng"], town["radius"], town["nb_cars"])
    for i in pos:
        request += "(" + str(capacity) + "," + str(consom) + ",'" + i + "'," + str(charge) + ",'" + i +"'),"

cur = db.cursor()
request = request[0:request.__len__() - 1]
try:
    # Execute the SQL command
    cur.execute(request)
    # Commit your changes in the database
    db.commit()
    print "donnees enregistrees. \n"
except:
    # Rollback in case there is any error
    db.rollback()







