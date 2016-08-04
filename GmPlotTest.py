import gmplot
import googlemaps

gmaps = googlemaps.Client(key='AIzaSyBj7JAQHEc-eFQkfuCXBba0dItAUPL0fMI')

gmap = gmplot.GoogleMapPlotter(37.428, -122.145, 16)

gmap.plot(37.427, -122.145, 'cornfolwerblue', edge_width=10)


gmap.draw("mymap.html")