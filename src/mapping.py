import folium
from folium import FeatureGroup, LayerControl
import osmnx as ox
from dataclasses import dataclass
from shapely import LineString
from constants import C 
from colorama import Fore, Style

@dataclass
class MapData():
    walking_graph: any
    df: any
    start_node: any
    boundary: any
    shelter_nums: any
    shelter_mapping: any
    shelters: any
    model: any
    start_address: any

def create_map(map_data: MapData):
    nodes = ox.graph_to_gdfs(map_data.walking_graph, nodes=True)[0]
    grouped = map_data.df.groupby(['demographic', 'destination_node'])
    unique_dests = sorted(map_data.df['destination_node'].unique())
    
    profile_colors = {
        'Elderly': '#1f77b4',  # Blue
        'Family': '#2ca02c',   # Green
        'Young Adult': '#ff7f0e',  # Orange
        'Mobility Impaired': '#d62728'  # Red
    }
    
    folium_map = folium.Map(location=[nodes.loc[map_data.start_node]['y'], nodes.loc[map_data.start_node]['x']], zoom_start=15, tiles='openstreetmap')
    
    # Add base graph edges
    base_layer = FeatureGroup(name="Base Map", show=True)
    for u, v, key, data in map_data.walking_graph.edges(keys=True, data=True):
        if 'geometry' in data:
            line = data['geometry']
        else:
            line = LineString([(nodes.loc[u, 'x'], nodes.loc[u, 'y']), (nodes.loc[v, 'x'], nodes.loc[v, 'y'])])
        locations = [(y, x) for x, y in line.coords]
        folium.PolyLine(locations, color='gray', weight=1, opacity=0.5).add_to(base_layer)
    base_layer.add_to(folium_map)
    
    folium.GeoJson(map_data.boundary, style_function=lambda x: {'color': 'black', 'weight': 2, 'fillOpacity': 0}).add_to(base_layer)
    
    # Add profile-specific layers
    profile_layers = {profile: FeatureGroup(name=f"{profile} Paths", show=False) for profile in C.AGENT_DEMOGRAPHICS}
    for (profile, dest), group in grouped:
        path = group['path'].iloc[0]
        if len(path) < 2:
            continue
        path_coords = [[nodes.loc[n]['y'], nodes.loc[n]['x']] for n in path if n in nodes.index]
        if path_coords:
            color = profile_colors[profile]
            distance = group['total_distance'].iloc[0]
            total_agents = len(group)
            avg_arrival = group['arrival_time'].mean()
            total_water = group['water_needed'].sum()
            vuln_stats = group.groupby('vulnerability').agg({
                'arrival_time': 'mean',
                'water_needed': 'mean',
                'vulnerability': 'count'
            }).rename(columns={'vulnerability': 'count'})
            vuln_stats['percentage'] = vuln_stats['count'] / vuln_stats['count'].sum() * 100
            vuln_stats = vuln_stats.round(2)
            stats_table_html = vuln_stats.to_html(border=1)
            route_attrs = group['route_attrs'].iloc[0]
            tooltip_html = f"""
            <b>Path to Shelter {map_data.shelter_nums.get(dest, 'Unknown')} (Profile: {profile})</b><br>
            Distance: {distance:.2f} meters<br>
            Total Agents: {total_agents}<br>
            Avg Arrival Time: {avg_arrival:.2f} min<br>
            Total Water Needed: {total_water:.2f} L<br>
            Avg Heat Exposure: {route_attrs['avg_heat_exposure']:.2f}<br>
            Avg Shade: {route_attrs['avg_shade_coverage']:.2f}<br>
            Avg Slope: {route_attrs['avg_slope']:.2f}<br>
            Rest Areas: {route_attrs['total_rest_areas']}<br>
            <br><b>Statistics by Vulnerability:</b><br>
            {stats_table_html}
            """
            folium.PolyLine(path_coords, color=color, weight=3, opacity=0.8, tooltip=tooltip_html).add_to(profile_layers[profile])
    
    for layer in profile_layers.values():
        layer.add_to(folium_map)
    
    folium.Marker(location=[nodes.loc[map_data.start_node]['y'], nodes.loc[map_data.start_node]['x']],
                    popup='Start Point', icon=folium.Icon(color='red', icon='info-sign')).add_to(base_layer)
    
    for node in unique_dests:
        if node in nodes.index:
            lat = nodes.loc[node]['y']
            lon = nodes.loc[node]['x']
            shelter_idx = map_data.shelter_mapping[node]
            capacity = map_data.shelters.iloc[shelter_idx]['capacity']
            occupancy = map_data.model.shelter_occupancy.get(node, 0)
            popup = f"Shelter {map_data.shelter_nums.get(node, 'Unknown')}<br>Occupancy: {occupancy}/{capacity}"
            folium.Marker(location=[lat, lon], popup=popup,
                            icon=folium.Icon(color='blue', icon='info-sign')).add_to(base_layer)
    
    LayerControl().add_to(folium_map)
    folium_map.save('evac_paths_' + map_data.start_address + '.html')
    print(f"{Fore.GREEN}Map saved to 'evac_paths_{map_data.start_address}.html' with profile filters.{Style.RESET_ALL}")