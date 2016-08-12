import MySQLdb
import json

db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
cursor = db.cursor()
request = "SELECT id_vehicle,closestations FROM destinations"
cursor.execute(request)
destinations = cursor.fetchall()
for destination in destinations:
    stations = json.loads(destination[1])
    new_stations = []
    for station in stations:
        request = "SELECT power FROM power_slot WHERE id_station=%d" % station[0]
        cursor.execute(request)
        power = cursor.fetchone()
        new_stations.append([station[0], station[1], power])
    new_stations_json = json.dumps(new_stations)
    request = "UPDATE destinations SET closestations='%s' WHERE id_vehicle=%d" % (new_stations_json, destination[0])
    cursor.execute(request)
db.commit()
