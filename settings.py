class C:
    # Hardcoded API key (as per provided document)
    API_KEY_PATH = "key.txt"
    BOUNDARY_PATH = "data/bancho.geojson"
    SHELTERS_PATH = "data/tokyo_shelters.csv"
    
    # Constants
    DRIVING_SPEED_KMH = 30  # Driving speed in km/h
    BASE_WALKING_SPEED_MPS = 1.4  # Base walking speed in meters per second (approx 5 km/h)
    WATER_PER_MINUTE = 0.008  # Liters of water needed per minute of walking

    # Vulnerability and mobility factors
    VULNERABILITY_FACTORS = {'Low': 1.0, 'Medium': 1.5, 'High': 2.0}
    LEVEL_ORDER = {'Low': 1, 'Medium': 2, 'High': 3}
    MOBILITY_FACTORS = {'High': 1.0, 'Medium': 0.8, 'Low': 0.6}

    # Demographics/Profiles
    AGENT_DEMOGRAPHICS = ["Elderly","Family","Mobility Impaired", "Young Adult"]