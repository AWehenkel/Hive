import MySQLdb
import googlemaps
import json
from pprint import pprint
import gmplot
from xlrd import open_workbook

# Connect to google map API
gmaps = googlemaps.Client(key='AIzaSyD3_6utmMWtQ8gqcE6-aL5BmVsBvmi4aNM')

# Open database connection
db = MySQLdb.connect("localhost","root","videogame2809","hive" )

fn = 'pv_puiss2.xlsx'
data = open_workbook('data/' + fn)
request = 'INSERT INTO pv (position, power) VALUES '
s = data.sheet_by_index(0)
for i in range(1, 200):
    street = str(s.col(5)[i].value.encode('ascii', 'ignore'))
    power = s.col(4)[i].value
    geocode_result = gmaps.geocode(street )
    if(geocode_result):
        lat = geocode_result[0]['geometry']['location']['lat']
        long = geocode_result[0]['geometry']['location']['lng']
        add = str(lat) + ',' + str(long)
        print i
        request += '(\'' + add + '\', \'' + str(power) + '\'),'

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