import json
import math

def euclidean_distance(p1, p2):
        return math.sqrt((p1["X"] - p2["X"])**2 + 
                         (p1["Y"] - p2["Y"])**2 + 
                         (p1["Z"] - p2["Z"])**2)

            
def compare_json_poses(json1, json2, threshold=0.05):
    total_points = len(json1)
    similar_points = 0

    for key in json1:
        if key in json2:
            distance = euclidean_distance(json1[key], json2[key])
            if distance <= threshold:
                similar_points += 1
    
    if total_points > 0:
        similarity = similar_points / total_points 
    else: 
        similarity = 0

    return {
        "similarity_score": similarity * 100,
        "moves_are_similar": similarity >= 0.8
    }
