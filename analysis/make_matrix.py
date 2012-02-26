# Convert the dump CSV file to a matrix where the columns
# are measurement sites and the rows are measurement times.
# Fill in missing measurements by copying from the most
# recently available measurement. Also, drop some measurement
# sites that yielded no actual measurements.
# Outputs matrix_speeds.csv and matrix_traveltimes.csv.

import csv
from xml.dom.minidom import parseString

# Map measurement site IDs to column numbers.
col_index = { }
site_ignore = set([ '3', '312', '314' ])
doc = parseString(open('../fetch/TrafficSpeed.php.xml').read())
for node in doc.getElementsByTagName("Speed"):
	id = node.getAttribute('Id')
	if id in site_ignore: continue
	if id not in col_index:
		col_index[id] = len(col_index)

# Read in data dump and build the data matrix.

def read_block(src):
	# Read in the rows of src, but group them by the value in the
	# first column (the time), so that we return all measurements
	# at a single measurement time together.
	rows = []
	for row in src:
		if len(rows) == 0 or rows[0][0] != row[0]:
			if len(rows) > 0: yield rows
			rows = []
		rows.append(row)
	if len(rows) > 0: yield rows

dump_fields = ("DataAsOf", "Id", "Speed", "TravelTime")

output_speeds = csv.writer(open("matrix_speeds.csv", "w"))
output_speeds.writerow(["time"] + ["SITE_" + siteid for siteid in col_index])

output_times = csv.writer(open("matrix_traveltimes.csv", "w"))
output_times.writerow(["time"] + ["SITE_" + siteid for siteid in col_index])

last_row = None
for block in read_block(csv.reader(open("../fetch/dump.csv"))):
	# What time were these measurements made? This is actually the UNIX time
	# of the HTTP request. We have the reported measurement time so a TODO
	# would be to use that instead (but it might vary across sites). Anyway,
	# this is number of seconds since the UNIX epoch.
	time = float(block[0][0])
	
	# Convert the list of measurements into a dict of speeds/times.
	row = { }
	for site in block:
		# Convert row into a dict of values.
		site = dict((dump_fields[i], site[i+1]) for i in xrange(len(dump_fields)))
		
		# Store the speed in the row dict.
		row[site["Id"]] = (float(site["Speed"]), float(site["TravelTime"]))
	
	# Fill in misssing measurements with the previous value (or 0.0 if
	# no previous value).
	for siteid in col_index:
		if not siteid in row:
			if last_row and siteid in last_row:
				row[siteid] = last_row[siteid]
			else:
				row[siteid] = (0.0, 0.0)
	
	# And output.
	output_speeds.writerow([time] + [row[siteid][0] for siteid in col_index])
	output_times.writerow([time] + [row[siteid][1] for siteid in col_index])

