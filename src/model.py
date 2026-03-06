from mesa import Model
from mesa.space import NetworkGrid
import numpy as np
import networkx as nx
from constants import C 
import logging 
from src.profiles import pick_profile
from src.agent import EvacueeAgent

class EvacuationModel(Model):
    """Model for simulating evacuation of multiple agents to a chosen shelter."""
    def __init__(self, num_agents, walking_graph, shelters, start_node, shelter_nodes):
        super().__init__()
        self.num_agents = num_agents
        self.walking_graph = walking_graph
        self.shelters = shelters
        self.grid = NetworkGrid(walking_graph)
        self.time = 0
        self.evacuees = []
        self.shelter_nodes = shelter_nodes
        self.shelter_mapping = {node: i for i, node in enumerate(shelter_nodes)}
        self.max_capacity = self.shelters['capacity'].max()
        self.shelter_occupancy = {node: 0 for node in shelter_nodes}  # Track occupancy
        self.start_node = start_node

        # Estimate total steps for progress bar
        lengths = nx.single_source_dijkstra_path_length(self.walking_graph, start_node, weight='length')
        avg_distance = np.mean([lengths.get(node, 0) for node in shelter_nodes if node in lengths])
        avg_speed = C.BASE_WALKING_SPEED_MPS * np.mean(list(C.MOBILITY_FACTORS.values())) / np.mean(list(C.VULNERABILITY_FACTORS.values()))
        self.estimated_steps = int((avg_distance / avg_speed / 60) * num_agents * 1.5)  # Conservative estimate

    def create_agents(self):
        """ Builds agents """
        for _ in range(self.num_agents):
            profile = pick_profile()
            prefs = profile.preferences

            def personal_weight(u, v, d):
                length = d[0].get('length', 0)
                grade = abs(d[0].get('grade', 0))
                heat = d[0].get('heat_exposure', 0.5)
                shade = d[0].get('shade_coverage', 0.5)
                access = d[0].get('accessibility_rating', 0.8)
                cost = length * (1 + prefs.weight_heat_avoidance * heat + 
                                prefs.weight_mobility * grade - 
                                prefs.weight_heat_avoidance* shade - 
                                prefs.weight_mobility * access)
                return cost

            utilities = {}

            # Calc shortest path to shelters
            for shelter_node in self.shelter_nodes:
                shelter_idx = self.shelter_mapping[shelter_node]
                if self.shelter_occupancy[shelter_node] >= self.shelters.iloc[shelter_idx]['capacity']:
                    continue
                try:
                    path = nx.shortest_path(self.walking_graph, self.start_node, shelter_node, weight=personal_weight)
                    path_cost = nx.shortest_path_length(self.walking_graph, self.start_node, shelter_node, weight=personal_weight)
                    route_attrs = self.calculate_route_attributes(self.walking_graph, path)
                except nx.NetworkXNoPath:
                    continue
                shelter = self.shelters.iloc[shelter_idx]

                # Ensure shelter meets needs / capacity
                match_medical = 10 if profile.medical_needs and shelter['has_medical'] else 0
                match_group = 10 if profile.family_status and shelter['family_friendly'] else 0
                match_access = 10 if profile.mobility_level == 'Low' and shelter['accessible'] else 0
                norm_capacity = shelter['capacity'] / self.max_capacity
                utility = (-path_cost * prefs.weight_distance + 
                          match_medical * prefs.weight_medical + 
                          match_group * prefs.weight_group + 
                          match_access * prefs.weight_mobility + 
                          norm_capacity * prefs.weight_capacity)
                utilities[shelter_node] = (utility, path, route_attrs)
            
            # Warn if none can be reached    
            if not utilities:
                logging.warning(f"No reachable shelters with capacity for agent with profile {profile}")
                continue

            # Sort utilities
            sorted_utilities = sorted(utilities.items(), key=lambda x: x[1][0], reverse=True)
            assigned = False

            # Assign shelters
            for shelter_node, (utility, path, route_attrs) in sorted_utilities:
                shelter_idx = self.shelter_mapping[shelter_node]
                if self.shelter_occupancy[shelter_node] < self.shelters.iloc[shelter_idx]['capacity']:
                    self.shelter_occupancy[shelter_node] += 1
                    agent = EvacueeAgent(self, self.start_node, shelter_node, profile, path, route_attrs)
                    self.evacuees.append(agent)
                    self.grid.place_agent(agent, self.start_node)
                    assigned = True
                    break
            
            # Warn if agent can't be assigned
            if not assigned:
                logging.warning(f"No available shelter with capacity for agent with profile {profile}")
        
        # Set model to running
        self.running = True

    def calculate_route_attributes(self, graph, path):
        """Calculate aggregated route attributes from path."""
        if len(path) < 2:
            return {
                'total_length': 0,
                'avg_slope': 0,
                'avg_heat_exposure': 0,
                'avg_shade_coverage': 0,
                'total_rest_areas': 0,
                'avg_accessibility': 0
            }
        total_length = 0
        total_slope = 0
        total_heat = 0
        total_shade = 0
        total_rest = 0
        total_access = 0
        num_edges = len(path) - 1
        for u, v in zip(path[:-1], path[1:]):
            data = graph.get_edge_data(u, v, 0)
            length = data.get('length', 0)
            total_length += length
            total_slope += abs(data.get('grade', 0)) * length
            total_heat += data.get('heat_exposure', 0.5) * length
            total_shade += data.get('shade_coverage', 0.5) * length
            total_rest += data.get('rest_areas', 0)
            total_access += data.get('accessibility_rating', 0.8) * length
        avg_slope = total_slope / total_length if total_length > 0 else 0
        avg_heat = total_heat / total_length if total_length > 0 else 0
        avg_shade = total_shade / total_length if total_length > 0 else 0
        avg_access = total_access / total_length if total_length > 0 else 0
        return {
            'total_length': total_length,
            'avg_slope': avg_slope,
            'avg_heat_exposure': avg_heat,
            'avg_shade_coverage': avg_shade,
            'total_rest_areas': total_rest,
            'avg_accessibility': avg_access
        }