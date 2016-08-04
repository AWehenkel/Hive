import math
import math
import random

#Datas about begian towns
class Towns:
    ville = {}

    ville['antwerp'] = {}
    ville['antwerp']['lat'] = 51.2604803
    ville['antwerp']['lng'] = 4.0890894
    ville['antwerp']['pop'] = 506922
    ville['antwerp']['superficie'] = 204.51

    ville['gent'] = {}
    ville['gent']['lat'] = 51.082572
    ville['gent']['lng'] = 3.5743995
    ville['gent']['pop'] = 248739
    ville['gent']['superficie'] = 156.2

    ville['brugge'] = {}
    ville['brugge']['lat'] = 51.2607981
    ville['brugge']['lng'] = 3.0820595
    ville['brugge']['pop'] = 117377
    ville['brugge']['superficie'] = 138.4

    ville['leuven'] = {}
    ville['leuven']['lat'] = 50.8842427
    ville['leuven']['lng'] = 4.5653444
    ville['leuven']['pop'] = 98002
    ville['leuven']['superficie'] = 56.63

    ville['malines'] = {}
    ville['malines']['lat'] = 51.0349419
    ville['malines']['lng'] = 4.3894747
    ville['malines']['pop'] = 82573
    ville['malines']['superficie'] = 65.19

    ville['alost'] = {}
    ville['alost']['lat'] = 50.9471822
    ville['alost']['lng'] = 4.0030697
    ville['alost']['pop'] = 82037
    ville['alost']['superficie'] = 78.12

    ville['hasselt'] = {}
    ville['hasselt']['lat'] = 50.9246522
    ville['hasselt']['lng'] = 5.2434247
    ville['hasselt']['pop'] = 74694
    ville['hasselt']['superficie'] = 102.24

    ville['kortrijk'] = {}
    ville['kortrijk']['lat'] = 50.8029382
    ville['kortrijk']['lng'] = 3.1396994
    ville['kortrijk']['pop'] = 74694
    ville['kortrijk']['superficie'] = 80.02

    ville['sint-niklaas'] = {}
    ville['sint-niklaas']['lat'] = 51.1687717
    ville['sint-niklaas']['lng'] = 4.0334847
    ville['sint-niklaas']['pop'] = 73317
    ville['sint-niklaas']['superficie'] = 83.80

    ville['ostende'] = {}
    ville['ostende']['lat'] = 51.2142266
    ville['ostende']['lng'] = 2.8517547
    ville['ostende']['pop'] = 70618
    ville['ostende']['superficie'] = 37.72

    ville['genk'] = {}
    ville['genk']['lat'] = 50.9668071
    ville['genk']['lng'] = 5.4199297
    ville['genk']['pop'] = 65321
    ville['genk']['superficie'] = 87.85

    ville['roeselare'] = {}
    ville['roeselare']['lat'] = 50.9406272
    ville['roeselare']['lng'] = 3.0499447
    ville['roeselare']['pop'] = 59147
    ville['roeselare']['superficie'] = 59.79

    ville['liege'] = {}
    ville['liege']["lat"] = 50.586133
    ville["liege"]["lng"] = 5.560259
    ville["liege"]["pop"] = 182741
    ville["liege"]["superficie"] = 69.4

    ville['bxl'] = {}
    ville['bxl']["lat"] = 50.85034
    ville["bxl"]["lng"] = 4.35171
    ville["bxl"]["pop"] = 1310000
    ville["bxl"]["superficie"] = 520

    ville['chrl'] = {}
    ville['chrl']["lat"] = 50.4
    ville["chrl"]["lng"] = 4.433
    ville["chrl"]["pop"] = 201433
    ville["chrl"]["superficie"] = 102.1

    ville['namur'] = {}
    ville['namur']["lat"] = 50.467388
    ville["namur"]["lng"] = 4.871985
    ville["namur"]["pop"] = 126954
    ville["namur"]["superficie"] = 175.7

    ville['mons'] = {}
    ville['mons']["lat"] = 50.454241
    ville["mons"]["lng"] = 3.956659
    ville["mons"]["pop"] = 90946
    ville["mons"]["superficie"] = 146.5

    ville['louviere'] = {}
    ville['louviere']["lat"] = 50.4748
    ville["louviere"]["lng"] = 4.183739
    ville["louviere"]["pop"] = 77013
    ville["louviere"]["superficie"] = 64.2

    ville['tournai'] = {}
    ville['tournai']["lat"] = 50.605648
    ville["tournai"]["lng"] = 3.387934
    ville["tournai"]["pop"] = 67553
    ville["tournai"]["superficie"] = 213.8

    ville['seraing'] = {}
    ville['seraing']["lat"] = 50.583883
    ville["seraing"]["lng"] = 5.49963
    ville["seraing"]["pop"] = 60672
    ville["seraing"]["superficie"] = 35.3

    ville['verviers'] = {}
    ville['verviers']["lat"] = 50.591056
    ville["verviers"]["lng"] = 5.865595
    ville["verviers"]["pop"] = 53275
    ville["verviers"]["superficie"] = 33.1

    ville['mouscron'] = {}
    ville['mouscron']["lat"] = 50.7379476
    ville["mouscron"]["lng"] = 3.1829996
    ville["mouscron"]["pop"] = 52639
    ville["mouscron"]["superficie"] = 40.1

    def __init__(self, percent):
        self.__setNumberOfCars(percent)
        self.__setRadius()


    def __setNumberOfCars(self, percent):
        for town in self.ville.values() :
            town["nb_cars"] = town["pop"] * percent/100

    def __setRadius(self):
        for town in self.ville.values() :
            town["radius"] = (town["superficie"] / math.pi)**.5

    # Generates a number of random gps points
    def genRandomLocation(self, lat, lng, dist, number):
        lat = lat / 180 * math.pi
        lng = lng / 180 * math.pi
        rad_earth = 6372.796924
        random.seed()
        # Convert dist to radian
        dist = dist / rad_earth

        result = []
        for i in range(0, number):
            r1 = random.random()
            r2 = random.random()
            rand_dist = math.acos(r1 * (math.cos(dist) - 1) + 1)
            brg = 2 * math.pi * r2
            r_lat = math.asin(math.sin(lat) * math.cos(rand_dist) + math.cos(lat) * math.sin(rand_dist) * math.cos(brg))
            r_lon = lng + math.atan2(math.sin(brg) * math.sin(rand_dist) * math.cos(lat),
                                     math.cos(rand_dist) - math.sin(lat) * math.sin(lat))
            if (r_lon < -math.pi):
                r_lon += 2 * math.pi

            result.append(str(r_lat * 180 / math.pi) + ", " + str(r_lon * 180 / math.pi))

        return result


