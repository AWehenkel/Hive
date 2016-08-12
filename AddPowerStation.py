
"""

# Connect to google map API
gmaps = googlemaps.Client(key='AIzaSyBj7JAQHEc-eFQkfuCXBba0dItAUPL0fMI')

# Open database connection
db = pymysql.connect("localhost","root","","hive" )

loop = 1
ans = 0

while loop == 1:
    gps = int(raw_input("Coordonnee gps(1) ou addresse(0)?\n"))
    if gps == 1:
        lat = raw_input("latitude : \n")
        long = raw_input("longitude : \n")

        # Look up the address with reverse geocoding
        reverse_geocode_result = gmaps.reverse_geocode((lat, long))
        print "addresse : ", reverse_geocode_result[0]['formatted_address'], "\n"
        lat = reverse_geocode_result[0]['geometry']['location']['lat']
        long = reverse_geocode_result[0]['geometry']['location']['lng']
        ans = int(raw_input("Voulez-vous enregistrer la station? oui(1) ou non(0)\n"))
    else:
        address = raw_input("Entrez l'addresse de la borne de recharge\n")
        # Geocoding an address
        geocode_result = gmaps.geocode(address)
        lat = geocode_result[0]['geometry']['location']['lat']
        long = geocode_result[0]['geometry']['location']['lng']
        print "addresse : ", geocode_result[0]['formatted_address'], "\n"
        ans = int(raw_input("Voulez-vous enregistrer la station? oui(1) ou non(0)\n"))


    if ans == 1:
        type = int(raw_input("Privee(1) ou publique(0)\n"))
        power = int(raw_input("Entrez la puissance(en kW)\n"))
        add = str(lat) + ',' + str(long)
        insertStation(db, type, power, add)

    loop = int(raw_input("Voulez-vous enregistrer une autre station?\n"))

# disconnect from server
db.close()

"""