

def calculate_normalized_pole_distance(latitude_str):
    """
    Calculate normalized distance from a latitude to the nearest pole.
    
    Args:
        latitude_str (str): Latitude in format "846168,568474"
    
    Returns:
        float: Normalized distance where:
               - Positive values (0 to 1) = closer to North Pole
               - Negative values (0 to -1) = closer to South Pole
               - 0 = at a pole, ±1 = at equator
    """
    # Parse the latitude string
    lat_parts = latitude_str.split(',')
    latitude = float(lat_parts[0] + '.' + lat_parts[1]) / 100000
    
    # Calculate distances to both poles
    distance_to_north_pole = 90 - latitude
    distance_to_south_pole = 90 + latitude
    
    # Determine which pole is closer and return signed normalized distance
    if distance_to_north_pole <= distance_to_south_pole:
        # Closer to North Pole - return positive value
        return distance_to_north_pole / 90
    else:
        # Closer to South Pole - return negative value
        return -(distance_to_south_pole / 90)


def main():
    latitude = "846168,568474"
    normalized_latitude = calculate_normalized_pole_distance(latitude)
    print(normalized_latitude)


if __name__ == "__main__":
    main()
