import MySQLdb
import gmplot
import googlemaps
from data import towns
import random


def create():
    # Open database connection
    db = MySQLdb.connect("localhost","root","videogame2809","hive" )

    townss = towns.Towns(0.1)
    pos = []
    capa = 25, 30, 60, 80
    consom = 18
    request = 'INSERT INTO vehicles (capacity, consumption, position, charge, home) VALUES '
    for town in townss.ville.values():
        capacity = 60
        consom = 18
        charge = 50
        pos = townss.genRandomLocation(town["lat"],town["lng"], town["radius"], town["nb_cars"])
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

def printMap():
    gmaps = googlemaps.Client(key='AIzaSyD0QmwrWQGk3YPqvYv7-iUxdqqK7Zh0MO4')
    gmap = gmplot.GoogleMapPlotter(50.850, 4.350, 16)
    # Open database connection
    db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
    cursor = db.cursor()
    request = "SELECT * FROM `destinations` NATURAL JOIN vehicles HAVING id_vehicle = id"
    try:
        cursor.execute(request)
        datas = cursor.fetchall()
        for add in datas:
            rand = random.random()
            if (rand < 0.5):
                addresse =  add[2].split(',')
                lat = float(addresse[0])
                lng = float(addresse[1])
                name = "ev"+str(add[0])
                text = "<h3 style = \"text-align:center;\">"+ name +"</h3>Capacite: " + str(add[6]) + "kWh<br/>Niveau de charge: " + str(add[9]) \
                       + "%%<br/>Consommation moyenne: " + str(add[7]) +"kW/100km<br/>Position: " + add[2] + "<br/>Destination: " + add[3] + "<br/>"
                gmap.marker(lat, lng, add[3], name, text)
        gmap.draw("data/vehiclesMap.html", 'AIzaSyD0QmwrWQGk3YPqvYv7-iUxdqqK7Zh0MO4')
    except:
        print "problem"

printMap()






