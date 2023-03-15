from google.cloud.firestore_v1 import GeoPoint

# create a GeoPoint object
location = GeoPoint(37.7749, -122.4194)

# get the latitude and longitude attributes
lat = location.latitude
lng = location.longitude

# format the location into a string
location_str = f"{lat}, {lng}"

print(location_str)  # output: "37.7749, -122.4194"