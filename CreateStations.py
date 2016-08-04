import math
import pymysql
from data import towns
import random
from data.towns import Towns

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
         print w[0]
         del w # delete the row we just chose so that we don't take a second time
         return ret
      upto += w[0]
   assert False, "Shouldn't get here"

# Generate a list of random locations for chargers at places where there are PVs
def getRandomStations (number) :

    chosen_pv = [0 for x in range(number)]

    # Open database connection
    db = pymysql.connect("localhost","root","","hive")

    # Get the datas about towns
    towns = Towns().ville

    #Get the pv positions
    request = 'SELECT position, power FROM pv'
    cursor = db.cursor()
    try:
       # Execute the SQL command
       cursor.execute(request)
       # Fetch all the rows in a list of lists.
       pv_positions = cursor.fetchall()

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

           # Give a certain weight to the pvs according to their proximity to the center of a city
           rad_closest = math.sqrt(towns[closest]['superficie']*10e6/math.pi)
           weight = rad_closest/min
           if weight > 20:
               weight = 20
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

print getRandomStations(10)