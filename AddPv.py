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

s = data.sheet_by_index(0)
print s.nrows
for i in range(6, s.nrows//300):
    request = 'INSERT INTO pv (position, power) VALUES '
    print i
    raw_input("pause")
    for j in range(300*i, 300*(i+1)):
        street = str(s.col(5)[j].value.encode('ascii', 'ignore'))
        power = s.col(4)[j].value
        geocode_result = gmaps.geocode(street )
        if(geocode_result):
            lat = geocode_result[0]['geometry']['location']['lat']
            long = geocode_result[0]['geometry']['location']['lng']
            add = str(lat) + ',' + str(long)
            print j
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