# Analyze the live feed data dump for patterns that hold across
# all of the measurement sites.

import csv
from xml.dom.minidom import parseString
import json
from datetime import datetime
from scipy.linalg import svd
#from scipy.interpolate import UnivariateSpline
#from scipy.stats import scoreatpercentile
import math, numpy

# map measurement site IDs to row numbers in our location-by-time data matrix
row_index = { }
site_ignore = set([ '3', '312', '314' ])
doc = parseString(open('TrafficSpeed.php.xml').read())
for node in doc.getElementsByTagName("Speed"):
	if node.getAttribute('Id') in site_ignore: continue
	if node.getAttribute('Id') not in row_index:
		row_index[node.getAttribute('Id')] = len(row_index)
#print row_index

# read in data dump and build the data matrix.

def read_and_group(src):
	# Read in the rows of src, but group them by the first column,
	# so that we return a whole column of values at a time.
	rows = []
	for row in src:
		if len(rows) == 0 or rows[0][0] != row[0]:
			if len(rows) > 0: yield rows
			rows = []
		rows.append(row)
	if len(rows) > 0: yield rows
	
data_matrix = [ [] for row in row_index ]
pingtimes = []
first = True
for column in read_and_group(csv.reader(open("dump.csv"))):
	# Add the values from this column into the appropriate rows
	# of data_matrix.
	pingtimes.append(float(column[0][0]))
	seen_sites = set()
	for pingtime, reportedtime, siteid, speed, duration in column:
		if siteid in site_ignore: continue
		seen_sites.add(siteid)
		data_matrix[row_index[siteid]].append(math.log(float(speed))) # log miles per hour
		seen_sites.add(siteid)
		
	# We tracked which rows we've seen because some pings of the
	# live feed URL didn't return data points for all ids, and we
	# need to fill in those cells with something --- e.g. the
	# previous value in that row.
	for s in row_index:
		if s not in seen_sites:
			data_matrix[row_index[s]].append( 0.0 if first else data_matrix[row_index[s]][-1] )
	first = False
	
print len(data_matrix), "measurement locations"
print len(pingtimes), "measurement times"

# smooth the measurements by applying a weighed average over a moving gaussian window
def smoothListGaussian(list,degree=5):
 # from http://www.swharden.com/blog/2008-11-17-linear-data-smoothing-in-python/
 window=degree*2-1  
 weight=numpy.array([1.0]*window)  
 weightGauss=[]  
 for i in range(window):  
	 i=i-degree+1  
	 frac=i/float(window)  
	 gauss=1/(numpy.exp((4*(frac))**2))  
	 weightGauss.append(gauss)  
 weight=numpy.array(weightGauss)*weight  
 smoothed=[0.0]*(len(list)-window)  
 for i in range(len(smoothed)):  
	 smoothed[i]=sum(numpy.array(list[i:i+window])*weight)/sum(weight)  
 return smoothed  
for i in xrange(len(data_matrix)):
	data_matrix[i] = smoothListGaussian(data_matrix[i], degree=3)

# simplify the measurements by taking only every 10th measurement
simplify_at_every = 10
pingtimes = [pingtimes[x] for x in range(0, len(pingtimes), simplify_at_every)]
for i in xrange(len(data_matrix)):
	data_matrix[i] = [data_matrix[i][x] for x in range(0, len(data_matrix[i]), simplify_at_every)]

print len(pingtimes), "simplified measurement times"

# write out data points for display

script_data = open("../www/data.js", "w") 

# write out x-axis time values every so-many minutes
output_interval = 1
script_data.write("ts_x = %s;\n" % (json.dumps([datetime.fromtimestamp(pingtimes[t]).strftime("%A %I:%M %p") for t in range(0, len(pingtimes), output_interval)]),))

# write out point values for the raw data
for d in xrange(len(data_matrix)):
	script_data.write("ts_raw_%d = %s;\n" % (d, json.dumps([round(data_matrix[d][t], 1) for t in range(0, len(data_matrix[d]), output_interval)])))


## write out speed values for the traffic locations, simplified to longer intervals
#for s in range(len(data_matrix)):
#	script_data.write("ts_raw_%d = %s;\n" % (s, make_points(data_matrix[s], output_interval)))

# run the SVD

U, S, Vh = svd(data_matrix)
	# data_matrix = U * S * Vh

def save_matrix(a, fn):
	with open(fn, "w") as f:
		for r in a:
			f.write(",".join([ str(v) for v in r ]) + "\n")

# The rows of U correspond to the rows of data_matrix, i.e. the locations
# of traffic measurement. Each column of U corresponds with a dimension of
# the transformed data, i.e. a time series pattern, and gives the factor for
# which the time series pattern applies to the measurement location.
save_matrix(U, "output_u.txt")

# The columns of Vh correspond with the columns of the data_matrix, i.e. the
# time slices. The first row of Vh corresponds with the first time series pattern
# ocurring in the data.
save_matrix(Vh[0:20], "output_vh.txt")


# Fit a spline to the time series patterns to simplify them for display.
for d in (0,1,2,3,4,5):
	# Find the measurement location that most exemplifies this time series,
	# i.e. the one with the highest absolute value of U[i,d].
	m = 0.0
	md = None
	for i in xrange(len(row_index)):
		if abs(U[i,d]) > abs(m):
			m = U[i,d]
			md = i
			
	print d, md
	
	# And multiply that by the singular value to compute the scale for
	# this dimension.
	m *= S[d]
	
	# Re-scale the vector by applying the factor from above including the
	# singular value to get the absolute effect on traffic speeds at that
	# location, and then shift the points so that the average value of the
	# time series matches the average value of the location's speed.
	pts = [m*y for y in Vh[d]]
	yoffset = numpy.mean(data_matrix[md]) - numpy.mean(pts)
	pts = [y+yoffset for y in pts]
	
	script_data.write("ts_pattern_%d = %s;\n" % (d, json.dumps([round(pts[t], 1) for t in range(0, len(pts), output_interval)])))
	

