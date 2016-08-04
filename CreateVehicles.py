import MySQLdb
import googlemaps
from data import Towns

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
    pos = towns.genRandomLocation(town["lat"],town["lng"], town["radius"], town["nb_cars"])
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







