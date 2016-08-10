import pymysql
from data.towns import Towns
import math
import gmplot
from CreateStations import *

stationsbxl = getRandomSationsBxl(1000)

# Insert station in database
# Open database connection
#db = pymysql.connect("localhost","root","","hive")
#for station in stationsbxl:
#    insertStation(db, 0, station[0], station[1], station[2])
#db.close()