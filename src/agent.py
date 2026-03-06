from constants import C 
from mesa import Agent 

class EvacueeAgent(Agent):
    """Agent representing an evacuee moving to a shelter."""
    def __init__(self, model, start_node, destination_node, profile, path, route_attrs):
        # Init model
        super().__init__(model)

        # Model attributes
        self.start_node = start_node
        self.current_node = start_node
        self.destination_node = destination_node
        self.water_reserve = profile.water_reserve
        self.demographic = profile.demographic
        self.age = profile.age
        self.family_status = profile.family_status
        self.medical_needs = profile.medical_needs
        self.mobility_level = profile.mobility_level
        self.speed = (C.BASE_WALKING_SPEED_MPS / C.VULNERABILITY_FACTORS[profile.vulnerability]) * C.MOBILITY_FACTORS[profile.mobility_level]
        self.arrival_time = None
        self.path = path
        self.route_attrs = route_attrs
        self.water_needed = 0.0

        # Positional data
        if len(self.path) > 1:
            self.position_index = 0
            self.current_edge_remaining = model.walking_graph[self.path[0]][self.path[1]][0]['length']
            self.arrived = False
        else:
            self.position_index = len(self.path) - 1
            self.arrived = True
            self.arrival_time = 0
            self.current_edge_remaining = 0
        self.total_distance = self.route_attrs['total_length']

    def step(self):
        # End loop if arrived
        if self.arrived:
            return
        
        # Update distance to cover and time spent 
        distance_to_cover = self.speed * 60  # meters per minute
        time_spent = distance_to_cover / self.speed / 60  # minutes

        # Update heat related data
        if self.position_index < len(self.path) - 1:
            edge_data = self.model.walking_graph[self.path[self.position_index]][self.path[self.position_index + 1]][0]
            heat = edge_data.get('heat_exposure', 0.5)
            self.water_needed += C.WATER_PER_MINUTE * time_spent * (1 + heat)
            self.water_reserve -= C.WATER_PER_MINUTE * time_spent * (1 + heat)
            if self.water_reserve <= 0:
                self.arrived = True
                return
        
        # Traverse graph for one step
        while distance_to_cover > 0 and self.position_index < len(self.path) - 1:
            if self.current_edge_remaining <= distance_to_cover:
                distance_to_cover -= self.current_edge_remaining
                self.position_index += 1
                if self.position_index < len(self.path) - 1:
                    self.current_edge_remaining = self.model.walking_graph[self.path[self.position_index]][self.path[self.position_index + 1]][0]['length']
                else:
                    self.current_edge_remaining = 0
                next_node = self.path[self.position_index]
                self.model.grid.move_agent(self, next_node)
                self.current_node = next_node
                if self.position_index == len(self.path) - 1:
                    self.arrived = True
                    self.arrival_time = self.model.time
                    break
            else:
                self.current_edge_remaining -= distance_to_cover
                distance_to_cover = 0