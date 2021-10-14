from math import radians, cos, sin, asin, sqrt

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula (Groskreisentfernung)
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def am_i_in_the_area(lat1, lon1, lat2, lon2, radius):
    center_point = [{'lat': lat1, 'lng': lon1}]
    test_point = [{'lat': lat2, 'lng': lon2}]

    lat1 = center_point[0]['lat']
    lon1 = center_point[0]['lng']
    lat2 = test_point[0]['lat']
    lon2 = test_point[0]['lng']

    a = haversine(lon1, lat1, lon2, lat2)
    if a <= radius:
        return True, a
    else:
        return False, a

if __name__ == "__main__":
    #Test
    center_point = [{'lat': 13.376935, 'lng': 52.516181}]
    test_point = [{'lat': 12.22321116667, 'lng': 49.8696671667}]

    lat1 = center_point[0]['lat']
    lon1 = center_point[0]['lng']
    lat2 = test_point[0]['lat']
    lon2 = test_point[0]['lng']

    radius = 2.00 # in kilometer

    a = haversine(lon1, lat1, lon2, lat2)

    print('Distance (km) : ', a)
    if a <= radius:
        print('Inside the area')
    else:
        print('Outside the area')