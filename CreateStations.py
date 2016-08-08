import math
import pymysql
from data import towns
import random
from data.towns import Towns
import gmplot
from AddPowerStation import insertStation

#Determine opening hours for a station
def openingHours():
    hours = [int(random.uniform(0,12)), int(random.uniform(13,24))]
    return hours

#Compute the distance between two points on the map
def twoPointsDistance(lat1, long1, lat2, long2):

    rad_earth = 6371e3  #earth radius in m

    delta_lat = math.fabs(math.radians(lat2-lat1))
    delta_long = math.fabs(math.radians(long2-long1))

    tmp = math.sin(delta_lat/2) * math.sin(delta_long/2)
    tmp += math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(delta_lat/2) * math.sin(delta_long/2)

    rel_dist = 2 * math.atan2(math.sqrt(tmp), math.sqrt(1-tmp))

    dist = rad_earth*rel_dist

    return dist

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
    try:
       # Execute the SQL command
       cursor.execute(request)
       # Fetch all the rows in a list of lists.
       pv_positions = cursor.fetchall()

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
           for town in towns.items() :
               tmp = twoPointsDistance(lat, long, town[1]['lat'], town[1]['lng'])
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

    except:
        print ("Error: unable to fetch data")

stations = getRandomStations(3000)
mymap = gmplot.GoogleMapPlotter(50.8550624, 4.3053506, 8)

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