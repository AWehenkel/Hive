import math
import pymysql
from data import towns
import random
from data.towns import Towns
import gmplot
#from AddPowerStation import insertStation
from OptimStations import *

#Determine opening hours for a station
def openingHours():
    hours = [int(random.uniform(0,12)), int(random.uniform(13,24))]
    return hours

# Choose a value in a list of element according to their weight
def weighted_choice(choices):
   total = sum(w[0] for w in choices)
   r = random.uniform(0, total)
   upto = 0
   for w in choices:
      if upto + w[0] >= r:
         ret = w[1:4]
         del choices[choices.index(w)] # delete the row we just chose so that we don't take it a second time
         return ret
      upto += w[0]
   assert False, "Shouldn't get here"

# Generate a list of random locations for chargers at places where there are PVs
def getRandomStations (number) :

    chosen_pv = [0 for x in range(number)]

    # Open database connection
    db = pymysql.connect("localhost","root","","hive")

    # Get the datas about towns
    towns = Towns(0.1).ville

    #Get the pv positions
    request = 'SELECT position, power FROM pv'
    cursor = db.cursor()
    pv_positions = []
    try:
       # Execute the SQL command
       cursor.execute(request)
       # Fetch all the rows in a list of lists.
       pv_positions = cursor.fetchall()
    except:
        print ("Error: unable to fetch data")

    #Compute the mean power of all stations. This will be used to compute the weigth of each pv location in
    # a dispatching strategy for the chargers
    mean_pow = sum(row[1] for row in pv_positions)/len(pv_positions)

    # Assign a weight to each pv location
    pv_number = pv_positions.__len__()
    pv_n_weight = [0 for x in range(pv_number)]
    cur = 0
    for row in pv_positions:

       coords = row[0].split(',', 1)
       lat = float(coords[0])
       long = float(coords[1])
       power = float(row[1])

       #Compute the distance of each pv to the different towns and keep the closest
       min = 400000000
       closest = towns['leuven']
       op = OptimStations()
       for town in towns.items() :
           tmp = op.asTheCrowFlies([lat, long],[town[1]['lat'], town[1]['lng']])
           if tmp < min :
              min = tmp
              closest = town[0]

       # Give a certain weight to the pvs according to their proximity to the center of a city and to the ratio
       # between the power of the station and the average power of all station
       rad_closest = math.sqrt(towns[closest]['superficie']*10e6/math.pi)
       weight = rad_closest/min * power/mean_pow
       if weight > 50:
          weight = 50
       pv_n_weight[cur] = [weight, lat, long, power]
       cur += 1

    # Choose randomly a certain number
    cur = 0
    for row in chosen_pv :
       chosen_pv[cur] = weighted_choice(pv_n_weight)
       cur += 1

    return chosen_pv


def getRandomSationsBxl(number):
    # Open database connection
    db = pymysql.connect("localhost","root","","hive")

    request = 'SELECT * From pv_tmp'
    cursor = db.cursor()
    pv_bxl = []
    try:
        # Execute the SQL command
        cursor.execute(request)
        # Fetch all the rows in a list of lists.
        pv_bxl = cursor.fetchall()
    except:
        print "Unable to fetch data"

    #Generate random positions for the stations
    towns = Towns(0.1)
    bxl_lat = towns.ville['bxl']['lat']
    bxl_long = towns.ville['bxl']['lng']
    bxl_rad = math.sqrt(towns.ville['bxl']['superficie']/math.pi)*1e3
    print bxl_rad
    if number > len(pv_bxl):
        number = pv_bxl
    pv_positions = towns.genRandomLocation(bxl_lat, bxl_long, bxl_rad, number)

    #Assign the different powers to the different positions and display it on the map

    mymap = gmplot.GoogleMapPlotter(50.8550624, 4.3053506, 8)
    cur = 0
    stations = [0 for x in range(number)]
    print number
    for row in pv_positions:
        pv_position = row.split(',', 1)
        hours = openingHours()
        mymap.marker(float(pv_position[0]), float(pv_position[1]), title=str(cur), text="Power: " + str(pv_bxl[cur][2]) + " (kW)" \
                     + "<br/>Open from " + str(hours[0]) + " to " + str(hours[1]))
        stations[cur] = [float(pv_position[0]), float(pv_position[1]), pv_bxl[cur][2]]
        cur += 1

    #To get the stations in the rest of the country at the same time
    stations = getRandomStations(3000)
    for station in stations:
        hours = openingHours()
        mymap.marker(station[0], station[1], title=str(cur), text="Power: " + str(station[2]) + " (kW)"
                    "<br/>Open from " + str(hours[0]) + " to " + str(hours[1]))
        cur += 1

    mymap.draw('./mymap.html', 'AIzaSyBj7JAQHEc-eFQkfuCXBba0dItAUPL0fMI')

    db.close()

    return stations

def createChargers():

    stations = []
    try:
        # Open database connection
        db = pymysql.connect("localhost","root","","hive")
        request = 'SELECT * From power_station'
        cursor = db.cursor()
        cursor.execute(request)
        stations = cursor.fetchall()

        for station in stations:
            power = station[4]
            charger_pow = 0
            nb_chargers = 0
            if power >= 200:
                #We use super chargers
                charger_pow = 160
                while power >= 160:
                    nb_chargers += 1
                    power -= 160
            elif power >= 40:
                #We use 40kWh chargers
                charger_pow = 40
                while power >= 40:
                    nb_chargers += 1
                    power -= 40
            else:
                #We use the maximum energy the station can deliver
                charger_pow = power
                nb_chargers = 1

            for i in range(nb_chargers):
                sql = "INSERT INTO chargers(type, lat, lng, power) VALUES ('%d', '%f', '%f', '%f')" % ( \
                      station[1], station[2], station[3], charger_pow)
                cursor.execute(sql)
                db.commit()

            print str(nb_chargers) + " chargers delivering " + str(charger_pow) + " from " + str(station[4])
    except:
        # Rollback in case there is any error
        db.rollback()


createChargers()

# inserts into the db a new station
def insertStation(db, type, lat, lng, power):

    # prepare a cursor object using cursor() method
    cursor = db.cursor()
    # Prepare SQL query to INSERT a record into the database.
    sql = "INSERT INTO POWER_STATION(type, lat, lng, power) VALUES ('%d', '%f', '%f', '%f')" % ( \
        type, lat, lng, power)

    try:
        # Execute the SQL command
        cursor.execute(sql)
        # Commit your changes in the database
        db.commit()
    except:
        # Rollback in case there is any error
        db.rollback()




stations = getRandomSationsBxl(1000)
'''
cur = 0
for station in stations:
    if(cur == 397 or cur == 2582 or cur == 1826 or cur == 1835):
        hours = openingHours()
        mymap.marker(station[0], station[1], title=str(cur), text="Power: " + str(station[2]) + " (kW)"
                            "<br/>Open from " + str(hours[0]) + " to " + str(hours[1]))
    cur += 1

mymap.draw('./mymap1.html', 'AIzaSyBj7JAQHEc-eFQkfuCXBba0dItAUPL0fMI')

# Insert station in database
# Open database connection
#db = pymysql.connect("localhost","root","","hive")
#for station in stations:
#    insertStation(db, 0, station[0], station[1], station[2])
#db.close()
'''