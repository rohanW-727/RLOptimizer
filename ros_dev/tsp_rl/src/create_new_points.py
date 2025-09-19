import googlemaps #Google Maps API client
import requests # For the Weather API
import json # Data Extraction in Responses are in JSON
import numpy as np # Numpy for mathematical/numerical computations and tinkering
import pandas as pd

with open(".../credentials.json") as f:
    creds = json.load(f)

gmaps = googlemaps.Client(key=creds["gmaps"])

file = pd.read_excel("Dataset.xlsx", engine="openpyxl")
new_df = pd.DataFrame(file)
new_df.index = np.arange(1, len(new_df) + 1)
new_df = new_df.drop_duplicates()
new_df = new_df.dropna()
new_df["Long"] = 0
new_df["Lat"] = 0
for i in range(len(new_df)):
    address = new_df.iloc[i,0]
    geocoded_result = gmaps.geocode(address)

    #Gather the latitude and longitudes of each location using Google's Geocode API
    if geocoded_result:
        location = geocoded_result[0]["geometry"]["location"]
        new_df.at[i+1, "Lat"] = location["lat"]
        new_df.at[i+1, "Long"] = location["lng"]

print(new_df)

#calculates the weather adjusted speed using Directions API for various routes
def get_weather_speed(origin, destination, gmaps):
    # Weather impact from traffic congestion variability in Directions API
    result = gmaps.directions(
        origin, 
        destination,
        mode="driving",
        departure_time = "now",
        alternatives=True
    )
    #Success
    if result:
        durations = [route["legs"][0]["duration_in_traffic"]["value"] for route in result[:3]] #Gets the traffic timing data from the API for each route
        baseline_duration = min(durations)
        max_duration = max(durations)
        #Edge Case Detection: Checking baseline_duration ensures the situation where there are no viable paths is caught
        ratio = max_duration/baseline_duration if baseline_duration > 0 else 1.0 
        return 0.8 if ratio > 1.2 else 1.0
    return 1.0

#Applies the weather adjusted feed process to specific start and end point
def load_location_nodes(credentials_file):
    global new_df
    nodes = [(row["Lat"], row["Long"]) for _, row in new_df.iterrows()]

    if len(nodes) > 1:
        speed = get_weather_speed((nodes[0][0], nodes[0][1]), (nodes[1,0], nodes[1,1]), gmaps)
    else:
        speed = 1.0
    return nodes[:10], speed

def get_directions_matrix(nodes, gmaps):
    #Fetches traffic aware travel times using Distance Matrix API and Caches them
    cache_file = "../cache/distance_matrix.json"
    try:
        with open(cache_file, "r") as f:
            return json.load(f)
    except: 
        matrix = gmaps.distance_matrix(origins=nodes, destinations=nodes, mode="driving", departure_time = "now")
        with open(cache_file, "w") as f:
            json.dump(matrix, f)
    return matrix


def validate_nodes(nodes):
    if len(nodes) != 10 or len(set(nodes)) != 10:
        raise ValueError("Must have 10 nodes")
    return nodes

#Generates a complete TSP instance with nodes, distances, and speed
#Needed for initialization of RL training data and dynamic replanning
def generate_tsp_instance(credentials_file):
    nodes, speed = load_location_nodes(credentials_file)
    global new_df
    with open(credentials_file) as f:
        gmaps = googlemaps.Client(key=json.load(f)["map_api_key"])
    distance_matrix = get_directions_matrix(nodes, gmaps)
    return validate_nodes(nodes), distance_matrix, speed, new_df

if __name__ == "__main__":
    credentials_file = "../credentials.json"
    nodes, distance_matrix, speed, new_df = generate_tsp_instance(credentials_file)
    print("Nodes: ", nodes, "Speed: ", speed)
    print("Dataframe: ", new_df)




    

    





