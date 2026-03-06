from dataclasses import dataclass
import random
import numpy as np 

@dataclass
class Preference():
    weight_distance: float
    weight_heat_avoidance: float
    weight_mobility: float
    weight_medical: float
    weight_capacity: float
    weight_group: float

class Elderly():
    def __init__(self):
        self.demographic = "Elderly"
        self.age = random.randint(65, 80)
        self.vulnerability = np.random.choice(['Medium', 'High'], p=[0.5, 0.5])
        self.medical_needs = random.random() < 0.7
        self.family_status = random.random() < 0.2
        self.mobility_level = np.random.choice(['Medium', 'Low'], p=[0.5, 0.5])
        self.risk_aversion = random.uniform(0.7, 1.0)
        self.water_reserve = random.uniform(0.5, 1.0)
        self.preferences = Preference(
            weight_distance=.35,
            weight_heat_avoidance=.3,
            weight_mobility=.2,
            weight_medical=.15,
            weight_capacity=0.0,
            weight_group=0.0
        )

class Family():
    def __init__(self):
        self.demographic = "Family"
        self.age = random.randint(30, 50)
        self.vulnerability = np.random.choice(['Low', 'Medium'], p=[0.6, 0.4])
        self.medical_needs = random.random() < 0.2
        self.family_status = True
        self.mobility_level = np.random.choice(['Medium', 'High'], p=[0.7, 0.3])
        self.risk_aversion = random.uniform(0.5, 0.8)
        self.water_reserve = random.uniform(1.0, 2.0)
        self.preferences = Preference(
            weight_distance=.2,
            weight_heat_avoidance=.2,
            weight_mobility=.15,
            weight_medical=.05,
            weight_capacity=0.15,
            weight_group=0.25
        )

class YoungAdult():
    def __init__(self):
        self.demographic = "Young Adult"
        self.age = random.randint(18, 35)
        self.vulnerability = np.random.choice(['Low', 'Medium'], p=[0.8, 0.2])
        self.medical_needs = random.random() < 0.1
        self.family_status = random.random() < 0.1
        self.mobility_level = np.random.choice(['High', 'Medium'], p=[0.8, 0.2])
        self.risk_aversion = random.uniform(0.0, 0.5)
        self.water_reserve = random.uniform(1.0, 2.0)
        self.preferences = Preference(
            weight_distance=.3,
            weight_heat_avoidance=.15,
            weight_mobility=.05,
            weight_medical=0.0,
            weight_capacity=.30,
            weight_group=.2
        )

class MobilityImpaired():
    def __init__(self):
        self.demographic = "Mobility Impaired"
        self.age = random.randint(40, 70)
        self.vulnerability = np.random.choice(['Medium', 'High'], p=[0.5, 0.5])
        self.medical_needs = random.random() < 0.6
        self.family_status = random.random() < 0.3
        self.mobility_level = 'Low'
        self.risk_aversion = random.uniform(0.6, 1.0)
        self.water_reserve = random.uniform(0.5, 1.5)
        self.preferences = Preference(
            weight_distance=.25,
            weight_heat_avoidance=.2,
            weight_mobility=.35,
            weight_medical=.15,
            weight_capacity=.05,
            weight_group=0.0
        )

def pick_profile():
    agents = [Elderly(), Family(), YoungAdult(), MobilityImpaired()]
    return random.choice(agents)