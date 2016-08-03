import MySQLdb
import googlemaps
import math
import random

def genRandomLocation(lat, lng, dist, number):
    lat = lat/180 * math.pi
    lng = lng/180 * math.pi
    rad_earth = 6372.796924
    random.seed()
    #Convert dist to radian
    dist = dist/rad_earth
    print dist

    result = []
    for i in range(0, number):
        r1 = random.random()
        r2 = random.random()
        print r1, r2
        rand_dist = math.acos(r1*(math.cos(dist) - 1) + 1)
        brg = 2*math.pi*r2
        r_lat = math.asin(math.sin(lat)*math.cos(rand_dist) + math.cos(lat)*math.sin(rand_dist)*math.cos(brg))
        r_lon = lng + math.atan2(math.sin(brg)*math.sin(rand_dist)*math.cos(lat), math.cos(rand_dist)-math.sin(lat)*math.sin(lat))
        result.append(str(r_lat * 180/math.pi) + ", " + str(r_lon * 180/math.pi))

    return result



ville = {}

ville['liege'] = {}
ville['liege']["lat"] = 50.586133
ville["liege"]["lng"] = 5.560259
ville["liege"]["number"] = 3500

print genRandomLocation(50.586133, 5.560259, 20, 20)






