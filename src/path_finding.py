import osmnx as ox
import networkx as nx
from colorama import Fore, Style

def find_path(walking_graph, start_coords, shelters):
    start_lat, start_lon = start_coords
    try:
        start_node = ox.distance.nearest_nodes(walking_graph, start_lon, start_lat)
    except Exception as e:
        print(f"{Fore.RED}Failed to find nearest node for start address: {e}. Exiting.{Style.RESET_ALL}")
        return
    
    shelter_nodes = [ox.distance.nearest_nodes(walking_graph, s.geometry.x, s.geometry.y) for s in shelters.itertuples()]
    shelter_mapping = {node: i for i, node in enumerate(shelter_nodes)}
    
    try:
        lengths = nx.single_source_dijkstra_path_length(walking_graph, start_node, weight='length')
        shelter_distances = {shelter_node: lengths[shelter_node] for shelter_node in shelter_nodes if shelter_node in lengths}
        if not shelter_distances:
            print(f"{Fore.RED}No shelters reachable from the starting location. Exiting.{Style.RESET_ALL}")
            return
        top_5_shelters = sorted(shelter_distances.items(), key=lambda x: x[1])[:5]
    except Exception as e:
        print(f"{Fore.RED}Failed to compute shelter distances: {e}. Exiting.{Style.RESET_ALL}")
        return
    
    # Define shelter_nums early
    shelter_nums = {shelter_node: i for i, (shelter_node, _) in enumerate(top_5_shelters, 1)}
    
    print(f"{Fore.CYAN}Closest evacuation shelters:{Style.RESET_ALL}")
    shelter_options = []
    for i, (shelter_node, distance) in enumerate(top_5_shelters, 1):
        shelter_idx = shelter_mapping[shelter_node]
        shelter_info = shelters.iloc[shelter_idx]
        name = shelter_info.get('name', f"Shelter at {shelter_info['latitude']:.4f}, {shelter_info['longitude']:.4f}")
        has_medical_str = " (medical)" if shelter_info['has_medical'] else ""
        family_str = " (family)" if shelter_info['family_friendly'] else ""
        access_str = " (accessible)" if shelter_info['accessible'] else ""
        print(f"{i}. {name}{has_medical_str}{family_str}{access_str} - Capacity: {shelter_info['capacity']} - Distance: {distance:.2f} m")
        shelter_options.append(shelter_node)
    print("Agents will choose shelters based on profiles, preferences, and capacity.")

    return shelter_options, shelter_nums, start_node, shelter_mapping