import pymysql
import random
from data import towns

def genDestination(lat, long, proba, dist_max):
    townss = towns.Towns(0.1)
    if(random.random() < proba):
        lat = townss.ville["bxl"]["lat"]
        long = townss.ville["bxl"]["lng"]

    return townss.genRandomLocation(lat, long, dist_max, 1)


# Open database connection
db = pymysql.connect("localhost","root","videogame2809","hive" )

cursor = db.cursor()

request = "SELECT * FROM vehicles"

try:
    cursor.execute(request)

    results = cursor.fetchall()
    request = "INSERT INTO destinations (id_vehicle, dep_pos, des_pos) VALUES "
    for row in results:
        position = row[5].split(',')
        lat = float(position[0])
        lng = float(position[1])
        dest = genDestination(lat, lng, 0.25, 10)
        request += "(" + str(row[0]) + ", \'" + row[5] + "\',\'" + dest[0] + "\'), "
except:
    print "error"
request = request[0:request.__len__() - 2]
try:
    # Execute the SQL command
    cursor.execute(request)
    # Commit your changes in the database
    db.commit()
    print "donnees enregistrees. \n"
except:
    # Rollback in case there is any error
    db.rollback()
db.close()

