import gmplot
import googlemaps

gmaps = googlemaps.Client(key='AIzaSyBj7JAQHEc-eFQkfuCXBba0dItAUPL0fMI')

gmap = gmplot.GoogleMapPlotter(50.8550624, 4.3053506, 16)


gmap.draw('./mymap.html', 'AIzaSyBj7JAQHEc-eFQkfuCXBba0dItAUPL0fMI')