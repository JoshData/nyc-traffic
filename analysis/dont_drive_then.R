# Read in the matrix of travel times.
travel_times = read.table("matrix_traveltimes.csv", header=T, sep=",")

# Select a route and combine the (simultaneous) travel times of the segments on the route.
# Travel times are in seconds.
tt = travel_times$SITE_88+travel_times$SITE_42+travel_times$SITE_43+travel_times$SITE_44

# Factor the total travel times to make the 66th percentile value one hour,
# simulating a one-hour rush hour trip.
tt = tt * 60*60 / quantile(tt, .66)

# Get the t0 time, the first recorded time. Recording times are in seconds
# since the Unix epoch. Subtract one (arbitrarily) because our first time
# was one second after a minute, and four minutes to shift to a multiple of 5.
t0 = travel_times$time[1] - 1 - 4*60

# Create a time vector that is relative to the start time (avoids precision loss
# when the effective t0 is the Unix epoch time).
t = travel_times$time - t0

# Smooth the data. Average across weeks by taking the modulus of
# the time value by the number of seconds in a week. Use 20
# knots per day.
spl = smooth.spline(x=t %% (60*60*24*7), y=tt, nknots=20*7)

# Compute the times (relative to the Unix epoch) where the first
# derivative of the travel time is less than one, meaning for
# each second the driver waits to begin the trip, the travel
# time decreases by at least a second, so that he will arrive
# at the destination at the same time or even earlier by waiting.
# Only evaluate at 5 minute intervals from t0.
t1 = seq(from=0, to=60*60*24*7, by=60*5)
dont_drive_then = t0 + t1[predict(spl, t1, deriv=1)$y < -1]

# Print out those times in human-readable format. Note that ISOdate
# returns a date that is tied to the UTC time zone, but strftime 
# converts the time to the EST time zone on output.
print(strftime(ISOdate(1970,1,1,0,0,0) + dont_drive_then, "%a %X", tz="EST"))


