import logging
import pandas as pd
from colorama import init, Fore, Style
from tqdm import tqdm
from src.setup import setup
from src.path_finding import find_path
from src.model import EvacuationModel
from src.mapping import MapData, create_map

# Initialize colorama for colored output
init()

def main():
    """Main function to run the ABM evacuation route planner."""

    # Announce to console 
    print(f"{Fore.CYAN}=== Nihonbashi Evacuation Route Planner v11 (ABM) ==={Style.RESET_ALL}")
    
    # Load files and stuff
    walking_graph, shelters, start_coords, start_address = setup()

    # Find shortest path to shelters
    shelter_options, shelter_nums, start_node, shelter_mapping = find_path(
        walking_graph, start_coords, shelters
    )

    # Prompt agent number input
    while True:
        try:
            num_agents = int(input("Enter number of agents to simulate: "))
            if num_agents <= 0:
                raise ValueError("Number of agents must be positive.")
            break
        except ValueError as e:
            print(f"{Fore.RED}Invalid input: {e}. Please enter a positive integer.{Style.RESET_ALL}")
    
    try:
        # Run model
        model = EvacuationModel(num_agents, walking_graph, shelters, start_node, shelter_options)

        # Show progress bar
        with tqdm(total=model.estimated_steps, desc="Simulating evacuation", unit="steps", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]") as pbar:
            while model.running:
                model.step()
                arrived_count = sum(1 for agent in model.evacuees if agent.arrived)
                pbar.n = min(arrived_count * (model.estimated_steps // num_agents), model.estimated_steps)
                pbar.refresh()
        
        # Get data from agents
        data = []
        for agent in model.evacuees:
            if agent.arrival_time is not None:
                data.append(vars(agent))
        
        # Announce if no data
        if not data:
            print(f"{Fore.RED}No agents reached the shelter. Check graph connectivity or shelter location.{Style.RESET_ALL}")
            return
        
        # Print results
        df = pd.DataFrame(data)
        print(f"\n{Fore.GREEN}Simulation completed.{Style.RESET_ALL}")
        print(f"Average arrival time: {df['arrival_time'].mean():.2f} minutes")
        print(f"Total water needed: {df['water_needed'].sum():.2f} liters")
        print(f"Average distance traveled: {df['total_distance'].mean():.2f} meters")
        
        # Group stats by profile, show results
        print(f"\n{Fore.GREEN}Statistics by demographic:{Style.RESET_ALL}")
        stats = df.groupby('demographic').agg({
            'arrival_time': ['mean', 'count'],
            'distance': 'mean',
            'water_needed': ['mean', 'sum'],
            'age': 'mean',
            'medical_needs': 'mean',
            'family_status': 'mean',
            'mobility_level': lambda x: x.value_counts().to_dict()
        }).round(2)
        print(stats)
        
        # Show shelter results
        print(f"\n{Fore.GREEN}Shelter Distribution by Profile:{Style.RESET_ALL}")
        shelter_dist = pd.crosstab(df['demographic'], df['destination_node'], normalize='index').round(3) * 100
        shelter_dist.columns = [f"Shelter {shelter_nums.get(col, 'Unknown')}" for col in shelter_dist.columns]
        print(shelter_dist)
        
        # Show results by shelter
        print("\nShelter Capacity Usage:")
        for node in shelter_options:
            shelter_idx = shelter_mapping[node]
            capacity = shelters.iloc[shelter_idx]['capacity']
            occupancy = model.shelter_occupancy.get(node, 0)
            print(f"Shelter {shelter_nums.get(node, 'Unknown')}: {occupancy}/{capacity} ({occupancy/capacity*100:.1f}%)")
        
        # Save evac data
        df.to_csv('evacuation_data.csv', index=False)
        print(f"\n{Fore.GREEN}Data saved to 'evacuation_data.csv'.{Style.RESET_ALL}")

        # Create map data object, show map
        map_data = MapData(
            walking_graph,
            df,
            start_node,
            None,
            shelter_nums,
            shelters, 
            model, 
            start_address
        )
        create_map(map_data)
        
    except Exception as e:
        print(f"{Fore.RED}Simulation failed: {e}. Exiting.{Style.RESET_ALL}")
        logging.error(f"Simulation error: {e}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print(f"{Fore.RED}An error occurred. Check logs for details.{Style.RESET_ALL}")