import pymysql
from data.towns import Towns
import math
import gmplot
from CreateStations import *

def getRandomSationsBxl(number):
    # Open database connection
    db = pymysql.connect("localhost","root","","hive")

    request = 'SELECT * From pv_tmp'
    cursor = db.cursor()
    try:
        # Execute the SQL command
        cursor.execute(request)
        # Fetch all the rows in a list of lists.
        pv_bxl = cursor.fetchall()

        #Generate random positions for the stations
        towns = Towns(0.1)
        bxl_lat = towns.ville['bxl']['lat']
        bxl_long = towns.ville['bxl']['lng']
        bxl_rad = math.sqrt(towns.ville['bxl']['superficie']/math.pi)
        if number > len(pv_bxl):
            number = pv_bxl
        pv_positions = towns.genRandomLocation(bxl_lat, bxl_long, bxl_rad, number)

        #Assign the different powers to the different positions and display it on the map

        mymap = gmplot.GoogleMapPlotter(50.8550624, 4.3053506, 8)
        cur = 0
        stations = [0 for x in range(number)]
        for row in pv_positions:
            pv_position = row.split(',', 1)
            hours = openingHours()
            mymap.marker(float(pv_position[0]), float(pv_position[1]), title=str(cur), text="Power: " + str(pv_bxl[cur][2]) + " (kW)" \
                         + "<br/>Open from " + str(hours[0]) + " to " + str(hours[1]))
            stations[cur] = [float(pv_position[0]), float(pv_position[1]), pv_bxl[cur][2]]
            cur += 1

        #To get the stations in the rest of the country at the same time
        #stations = getRandomStations(3000)
        #for station in stations:
        #    hours = openingHours()
        #    mymap.marker(station[0], station[1], title=str(cur), text="Power: " + str(station[2]) + " (kW)"
        #                "<br/>Open from " + str(hours[0]) + " to " + str(hours[1]))
        #    cur += 1

        mymap.draw('./mymap.html', 'AIzaSyBj7JAQHEc-eFQkfuCXBba0dItAUPL0fMI')

        db.close()

        return stations

    except:
        print ("Error: unable to fetch data")

stationsbxl = getRandomSationsBxl(1000)

# Insert station in database
# Open database connection
#db = pymysql.connect("localhost","root","","hive")
#for station in stationsbxl:
#    insertStation(db, 0, station[0], station[1], station[2])
#db.close()