# Read the live traffic data from the NYC DOT and append it to dump.csv.
#
# The columns written are:
# 	the current time in seconds since the Unix epoch (i.e. time())
#	the reported measurement time of the data point (as a string)
#	the ID of the measurement location
#	the traffic speed in miles per hour
#	the duration of a vehicle in this traffic region in seconds (?)
#
# The data is pulled in XML format from:
# http://207.251.86.229/nyc-links-cams/TrafficSpeed.php
#
# For more information, see:
# http://a841-dotweb01.nyc.gov/datafeeds/TrafficSpeed/metadata_trafficspeeds.pdf

import csv
import urllib
import time
from xml.dom.minidom import parseString

now = time.time()
data = urllib.urlopen("http://207.251.86.229/nyc-links-cams/TrafficSpeed.php").read()
doc = parseString(data)

save_fields = ("DataAsOf", "Id", "Speed", "TravelTime")

output = csv.writer(open("dump.csv", "a"))

for node in doc.getElementsByTagName("Speed"):
	output.writerow([now] + [ node.getAttribute(attr) for attr in save_fields ])

