# Analyze the live feed data dump for patterns that hold across
# all of the measurement sites.

import csv
from xml.dom.minidom import parseString
from scipy.linalg import svd
from scipy.interpolate import UnivariateSpline

# map measurement site IDs to row numbers in our location-by-time data matrix
row_index = { }
doc = parseString(open('TrafficSpeed.php.xml').read())
for node in doc.getElementsByTagName("Speed"):
	if node.getAttribute('Id') not in row_index:
		row_index[node.getAttribute('Id')] = len(row_index)

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
for column in read_and_group(csv.reader(open("dump.csv"))):
	# Add the values from this column into the appropriate rows
	# of data_matrix.
	pingtimes.append(column[0][0])
	seen_sites = set()
	for pingtime, reportedtime, siteid, speed, duration in column:
		seen_sites.add(siteid)
		data_matrix[row_index[siteid]].append(speed)
		seen_sites.add(siteid)
		
	# We tracked which rows we've seen because some pings of the
	# live feed URL didn't return data points for all ids, and we
	# need to fill in those cells with something --- e.g. the
	# previous value in that row.
	for s in row_index:
		if s not in seen_sites:
			data_matrix[row_index[s]].append( data_matrix[row_index[s]][-1] )

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
for d in (0,):
	# Find the maximum absolute value factor that this time series pattern
	# applies to the measurement locations.
	m = 0.0
	for i in xrange(len(row_index)):
		if abs(U[i,d]) > abs(m):
			m = U[i,d]
			
	# Compute the extreme values of this time series in miles per hour.
	print m * S[d] * min(Vh[d])
	print m * S[d] * max(Vh[d])
	
	continue
	fit = UnivariateSpline(range(0, len(Vh[d])), Vh[d])
	for t in range(0, len(Vh[d]), 10): # re-evaluate at 10-minute intervals
		pass
		#print fit(t)

#print pingtimes
