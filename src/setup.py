import os 
import logging
import geopandas as gpd
from shapely.ops import polygonize
from shapely.geometry import Point, LineString, Polygon
import osmnx as ox
import random 
import pandas as pd 
import numpy as np
import requests 
from colorama import Fore, Style
from constants import C 

def read_key():
    with open(C.API_KEY_PATH, "r") as f:
        key = f.read()
    return key 

def load_bounds(path):
    """Load Nihonbashi boundary shapefile and convert to polygon in EPSG:4326."""
    if not os.path.exists(path):
        raise FileNotFoundError("Boundary shapefile not found.")
    logging.info("Loading boundary shapefile...")
    try:
        boundary = gpd.read_file(path)
        # Set CRS
        if boundary.crs is None:
            boundary.set_crs(epsg=2451, inplace=True)
        boundary = boundary.to_crs(epsg=4326)
        
        # Make polygon
        geom = boundary.union_all()
        if geom.geom_type == 'Polygon':
            polygon = geom
        elif geom.geom_type in ['LineString', 'MultiLineString']:
            polygon = polygonize(geom)
            if isinstance(polygon, Polygon):
                pass
            else:
                polygon = next(iter(polygon))
        else:
            raise ValueError("Unsupported geometry type")
        if not polygon.is_valid:
            polygon = polygon.buffer(0)
        boundary.at[boundary.index[0], 'geometry'] = polygon
        return boundary
    except Exception as e:
        logging.error(f"Failed to load boundary shapefile: {e}")
        raise

def load_walking_graph(polygon, key):
    """Load walking graph from polygon and enhance with attributes."""
    logging.info("Loading walking graph from polygon...")
    graph = ox.graph_from_polygon(polygon, network_type='walk')
    try:
        graph = ox.add_node_elevations_google(graph, api_key=key)
        graph = ox.add_edge_grades(graph)
    except Exception as e:
        logging.warning(f"Failed to add elevations: {e}. Using synthetic slopes.")
        for u, v, k, data in graph.edges(keys=True, data=True):
            data['grade'] = random.uniform(0, 0.05)
    for u, v, k, data in graph.edges(keys=True, data=True):
        highway = data.get('highway', '')
        data['heat_exposure'] = random.uniform(0.1, 0.4) if highway == 'footway' else random.uniform(0.5, 0.8)
        data['shade_coverage'] = 1 - data['heat_exposure']
        data['rest_areas'] = 1 if random.random() < 0.1 else 0
        data['accessibility_rating'] = 0.2 if 'steps' in str(highway) else random.uniform(0.8, 1.0)
    return graph

def load_evacuation_shelters():
    """Load evacuation shelters from provided CSV data."""
    if not os.path.exists(C.SHELTERS_PATH):
        raise FileNotFoundError("evac_shelters.csv not found.")
    logging.info("Loading evacuation shelters from CSV...")
    try:
        shelters_data = pd.read_csv(C.SHELTERS_PATH)
        shelters_data['geometry'] = shelters_data.apply(lambda row: Point(row['longitude'], row['latitude']), axis=1)
        shelters = gpd.GeoDataFrame(shelters_data, geometry='geometry', crs="EPSG:4326")
        shelters['capacity'] = np.random.randint(50, 201, size=len(shelters))  # Random capacity
        shelters['current_occupancy'] = 0  # Initialize occupancy
        shelters['has_medical'] = np.random.choice([True, False], size=len(shelters))
        shelters['family_friendly'] = np.random.choice([True, False], size=len(shelters))
        shelters['accessible'] = np.random.choice([True, False], size=len(shelters))
        return shelters
    except Exception as e:
        logging.error(f"Failed to load shelters CSV: {e}")
        raise

def geocode_address(address, api_key):
    """Geocode an address using Google Maps API with Nominatim fallback."""
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&region=jp&key={api_key}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data['status'] == 'OK':
            location = data['results'][0]['geometry']['location']
            logging.info(f"Geocoded {address} to {location['lat']}, {location['lng']} via Google Maps")
            return location['lat'], location['lng']
        else:
            logging.warning(f"Google Maps geocoding failed: {data['status']}")
    except requests.RequestException as e:
        logging.error(f"Google Maps API request failed: {e}")

    try:
        url = f"https://nominatim.openstreetmap.org/search?q={address}&format=json&limit=1"
        headers = {'User-Agent': 'NihonbashiRoutePlanner/1.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            lat, lon = float(data[0]['lat']), float(data[0]['lon'])
            logging.info(f"Geocoded {address} to {lat}, {lon} via Nominatim")
            return lat, lon
        else:
            logging.error("Nominatim geocoding returned no results")
            return None
    except requests.RequestException as e:
        logging.error(f"Nominatim API request failed: {e}")
        return None
        
def setup():
        # Read API key
        key = read_key()

        # Load bounds
        boundary = load_bounds(C.BOUNDARY_PATH)
        polygon = boundary.geometry.iloc[0]

        # Load graph
        walking_graph = load_walking_graph(polygon, key)
        max_edge_length = max((data['length'] for u, v, data in walking_graph.edges(data=True)), default=0)
        logging.info(f"Maximum edge length in walking graph: {max_edge_length} meters")

        # Load walking graph
        shelters = load_evacuation_shelters()
        shelters = shelters[shelters.geometry.within(polygon)]
        if shelters.empty:
            print(f"{Fore.RED}No shelters found within the boundary. Exiting.{Style.RESET_ALL}")
            return
        
        # Geocode addresses
        start_address = input("Enter starting address: ")
        start_coords = geocode_address(start_address, key)
        if start_coords is None:
            print(f"{Fore.RED}Failed to geocode starting address. Exiting.{Style.RESET_ALL}")
            return

        # Return stuff
        return walking_graph, shelters, start_coords, start_address, polygon