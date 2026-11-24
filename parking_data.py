"""
parking_data.py - Simulated Parking Dataset Manager
===================================================
Manages the parking lot dataset (36 parking spaces across 3 zones).
Handles loading, saving, resetting, randomizing, and simulating traffic steps.
"""

import json
import os
import random
import math

DATASET_DIR = os.path.join(os.path.dirname(__file__), "dataset")
DATASET_PATH = os.path.join(DATASET_DIR, "parking_data.json")

# In-memory store for serverless environments (e.g. Vercel read-only filesystem)
_IN_MEMORY_SPACES = None

# Default baseline dataset of 36 parking spaces
DEFAULT_SPACES = [
    # --- ZONE A (Slots P01 to P12, Upper Row) ---
    {"id": "P01", "slot_number": 1, "zone": "Zone A", "x": 3.0, "y": 4.0, "status": "Available", "parking_type": "EV", "hourly_rate": 3.50, "features": "Level 2 Fast Charger"},
    {"id": "P02", "slot_number": 2, "zone": "Zone A", "x": 6.0, "y": 4.0, "status": "Occupied", "parking_type": "EV", "hourly_rate": 3.50, "features": "Level 2 Fast Charger"},
    {"id": "P03", "slot_number": 3, "zone": "Zone A", "x": 9.0, "y": 4.0, "status": "Available", "parking_type": "Regular", "hourly_rate": 2.50, "features": "Standard Bay"},
    {"id": "P04", "slot_number": 4, "zone": "Zone A", "x": 12.0, "y": 4.0, "status": "Occupied", "parking_type": "Regular", "hourly_rate": 2.50, "features": "Standard Bay"},
    {"id": "P05", "slot_number": 5, "zone": "Zone A", "x": 15.0, "y": 4.0, "status": "Available", "parking_type": "Regular", "hourly_rate": 2.50, "features": "CCTV Monitored"},
    {"id": "P06", "slot_number": 6, "zone": "Zone A", "x": 18.0, "y": 4.0, "status": "Available", "parking_type": "Regular", "hourly_rate": 2.50, "features": "CCTV Monitored"},
    {"id": "P07", "slot_number": 7, "zone": "Zone A", "x": 21.0, "y": 4.0, "status": "Occupied", "parking_type": "Regular", "hourly_rate": 2.50, "features": "Standard Bay"},
    {"id": "P08", "slot_number": 8, "zone": "Zone A", "x": 24.0, "y": 4.0, "status": "Reserved", "parking_type": "Regular", "hourly_rate": 2.50, "features": "Staff Reserved"},
    {"id": "P09", "slot_number": 9, "zone": "Zone A", "x": 27.0, "y": 4.0, "status": "Available", "parking_type": "Regular", "hourly_rate": 2.50, "features": "Near Walkway"},
    {"id": "P10", "slot_number": 10, "zone": "Zone A", "x": 30.0, "y": 4.0, "status": "Occupied", "parking_type": "Regular", "hourly_rate": 2.50, "features": "Near Walkway"},
    {"id": "P11", "slot_number": 11, "zone": "Zone A", "x": 33.0, "y": 4.0, "status": "Available", "parking_type": "Disabled", "hourly_rate": 0.00, "features": "Wide Access & Ramp"},
    {"id": "P12", "slot_number": 12, "zone": "Zone A", "x": 36.0, "y": 4.0, "status": "Occupied", "parking_type": "Disabled", "hourly_rate": 0.00, "features": "Wide Access & Ramp"},

    # --- ZONE B (Slots P13 to P24, Central Double Bay) ---
    {"id": "P13", "slot_number": 13, "zone": "Zone B", "x": 5.0, "y": 10.0, "status": "Available", "parking_type": "EV", "hourly_rate": 3.50, "features": "Tesla & CCS Compatible"},
    {"id": "P14", "slot_number": 14, "zone": "Zone B", "x": 9.0, "y": 10.0, "status": "Occupied", "parking_type": "Regular", "hourly_rate": 2.50, "features": "Standard Bay"},
    {"id": "P15", "slot_number": 15, "zone": "Zone B", "x": 13.0, "y": 10.0, "status": "Available", "parking_type": "Regular", "hourly_rate": 2.50, "features": "Shaded Bay"},
    {"id": "P16", "slot_number": 16, "zone": "Zone B", "x": 17.0, "y": 10.0, "status": "Occupied", "parking_type": "Regular", "hourly_rate": 2.50, "features": "Shaded Bay"},
    {"id": "P17", "slot_number": 17, "zone": "Zone B", "x": 21.0, "y": 10.0, "status": "Reserved", "parking_type": "Regular", "hourly_rate": 2.50, "features": "Permit Parking"},
    {"id": "P18", "slot_number": 18, "zone": "Zone B", "x": 25.0, "y": 10.0, "status": "Available", "parking_type": "Regular", "hourly_rate": 2.50, "features": "Standard Bay"},
    {"id": "P19", "slot_number": 19, "zone": "Zone B", "x": 5.0, "y": 13.0, "status": "Occupied", "parking_type": "Regular", "hourly_rate": 2.50, "features": "Standard Bay"},
    {"id": "P20", "slot_number": 20, "zone": "Zone B", "x": 9.0, "y": 13.0, "status": "Available", "parking_type": "Regular", "hourly_rate": 2.50, "features": "Standard Bay"},
    {"id": "P21", "slot_number": 21, "zone": "Zone B", "x": 13.0, "y": 13.0, "status": "Occupied", "parking_type": "Regular", "hourly_rate": 2.50, "features": "Standard Bay"},
    {"id": "P22", "slot_number": 22, "zone": "Zone B", "x": 17.0, "y": 13.0, "status": "Available", "parking_type": "Regular", "hourly_rate": 2.50, "features": "Standard Bay"},
    {"id": "P23", "slot_number": 23, "zone": "Zone B", "x": 21.0, "y": 13.0, "status": "Available", "parking_type": "Disabled", "hourly_rate": 0.00, "features": "Level Ramp Access"},
    {"id": "P24", "slot_number": 24, "zone": "Zone B", "x": 25.0, "y": 13.0, "status": "Reserved", "parking_type": "Disabled", "hourly_rate": 0.00, "features": "Accessible Reserved"},

    # --- ZONE C (Slots P25 to P36, Lower Row) ---
    {"id": "P25", "slot_number": 25, "zone": "Zone C", "x": 3.0, "y": 19.0, "status": "Available", "parking_type": "EV", "hourly_rate": 3.50, "features": "Fast 50kW DC Charger"},
    {"id": "P26", "slot_number": 26, "zone": "Zone C", "x": 6.0, "y": 19.0, "status": "Available", "parking_type": "EV", "hourly_rate": 3.50, "features": "Fast 50kW DC Charger"},
    {"id": "P27", "slot_number": 27, "zone": "Zone C", "x": 9.0, "y": 19.0, "status": "Occupied", "parking_type": "Regular", "hourly_rate": 2.00, "features": "Economy Bay"},
    {"id": "P28", "slot_number": 28, "zone": "Zone C", "x": 12.0, "y": 19.0, "status": "Occupied", "parking_type": "Regular", "hourly_rate": 2.00, "features": "Economy Bay"},
    {"id": "P29", "slot_number": 29, "zone": "Zone C", "x": 15.0, "y": 19.0, "status": "Available", "parking_type": "Regular", "hourly_rate": 2.00, "features": "Economy Bay"},
    {"id": "P30", "slot_number": 30, "zone": "Zone C", "x": 18.0, "y": 19.0, "status": "Occupied", "parking_type": "Regular", "hourly_rate": 2.00, "features": "Economy Bay"},
    {"id": "P31", "slot_number": 31, "zone": "Zone C", "x": 21.0, "y": 19.0, "status": "Available", "parking_type": "Regular", "hourly_rate": 2.00, "features": "Economy Bay"},
    {"id": "P32", "slot_number": 32, "zone": "Zone C", "x": 24.0, "y": 19.0, "status": "Available", "parking_type": "Regular", "hourly_rate": 2.00, "features": "Economy Bay"},
    {"id": "P33", "slot_number": 33, "zone": "Zone C", "x": 27.0, "y": 19.0, "status": "Occupied", "parking_type": "Regular", "hourly_rate": 2.00, "features": "Economy Bay"},
    {"id": "P34", "slot_number": 34, "zone": "Zone C", "x": 30.0, "y": 19.0, "status": "Reserved", "parking_type": "Regular", "hourly_rate": 2.00, "features": "Carpool Reserved"},
    {"id": "P35", "slot_number": 35, "zone": "Zone C", "x": 33.0, "y": 19.0, "status": "Available", "parking_type": "Disabled", "hourly_rate": 0.00, "features": "Wheelchair Friendly"},
    {"id": "P36", "slot_number": 36, "zone": "Zone C", "x": 36.0, "y": 19.0, "status": "Occupied", "parking_type": "Disabled", "hourly_rate": 0.00, "features": "Wheelchair Friendly"}
]


def ensure_dataset():
    """Ensure dataset directory and file exist."""
    try:
        os.makedirs(DATASET_DIR, exist_ok=True)
        if not os.path.exists(DATASET_PATH):
            save_dataset(DEFAULT_SPACES)
    except OSError:
        pass


def load_dataset():
    """Load parking spaces from memory or JSON dataset file."""
    global _IN_MEMORY_SPACES
    if _IN_MEMORY_SPACES is not None:
        return [dict(s) for s in _IN_MEMORY_SPACES]

    ensure_dataset()
    try:
        if os.path.exists(DATASET_PATH):
            with open(DATASET_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                _IN_MEMORY_SPACES = [dict(s) for s in loaded]
                return loaded
    except Exception as e:
        print(f"Error loading dataset from disk: {e}. Falling back to defaults.")

    _IN_MEMORY_SPACES = [dict(s) for s in DEFAULT_SPACES]
    return [dict(s) for s in DEFAULT_SPACES]


def save_dataset(spaces):
    """Save parking spaces to in-memory store and JSON dataset file if writable."""
    global _IN_MEMORY_SPACES
    _IN_MEMORY_SPACES = [dict(s) for s in spaces]
    try:
        os.makedirs(DATASET_DIR, exist_ok=True)
        with open(DATASET_PATH, "w", encoding="utf-8") as f:
            json.dump(spaces, f, indent=2)
    except OSError:
        # Expected in read-only serverless environments like Vercel
        pass


def reset_dataset():
    """Reset dataset to pristine default baseline."""
    # Create fresh deep copy
    fresh_spaces = [dict(s) for s in DEFAULT_SPACES]
    save_dataset(fresh_spaces)
    return fresh_spaces


def randomize_dataset():
    """Randomize the occupancy status across all spaces."""
    spaces = load_dataset()
    statuses = ["Available", "Occupied", "Reserved"]
    # Probability weights: 55% Available, 35% Occupied, 10% Reserved
    weights = [0.55, 0.35, 0.10]
    
    for s in spaces:
        s["status"] = random.choices(statuses, weights=weights, k=1)[0]
    
    # Ensure at least 3 spots are available to guarantee intelligent choices
    avail_count = sum(1 for s in spaces if s["status"] == "Available")
    if avail_count < 3:
        for s in spaces[:3]:
            s["status"] = "Available"
            
    save_dataset(spaces)
    return spaces


def simulate_traffic_step():
    """
    Simulates dynamic real-world traffic:
    - 1 to 3 occupied spots become available (drivers leave).
    - 1 to 3 available spots become occupied (new arrivals park).
    Returns the updated dataset and a log message of the traffic events.
    """
    spaces = load_dataset()
    events = []

    occupied_slots = [s for s in spaces if s["status"] == "Occupied"]
    available_slots = [s for s in spaces if s["status"] == "Available"]

    # Departures: 1 to 2 cars leave
    departures = random.sample(occupied_slots, min(len(occupied_slots), random.randint(1, 2))) if occupied_slots else []
    for s in departures:
        s["status"] = "Available"
        events.append(f"Vehicle departed from {s['id']} ({s['zone']}, {s['parking_type']}) -> Now Available")

    # Arrivals: 1 to 2 cars arrive
    arrivals = random.sample(available_slots, min(len(available_slots), random.randint(1, 2))) if available_slots else []
    for s in arrivals:
        s["status"] = "Occupied"
        events.append(f"New vehicle parked in {s['id']} ({s['zone']}, {s['parking_type']}) -> Now Occupied")

    save_dataset(spaces)
    return spaces, events


def update_slot_status(slot_id, new_status):
    """Update status of a specific slot (Available, Occupied, Reserved)."""
    spaces = load_dataset()
    found = False
    for s in spaces:
        if s["id"].upper() == slot_id.upper():
            s["status"] = new_status
            found = True
            break
    if found:
        save_dataset(spaces)
    return found, spaces


def calculate_statistics(spaces=None):
    """Compute summary metrics for dashboard."""
    if spaces is None:
        spaces = load_dataset()

    total = len(spaces)
    available = sum(1 for s in spaces if s["status"] == "Available")
    occupied = sum(1 for s in spaces if s["status"] == "Occupied")
    reserved = sum(1 for s in spaces if s["status"] == "Reserved")
    occupancy_rate = round((occupied / total * 100), 1) if total > 0 else 0.0

    # Type breakdown
    type_stats = {
        "Regular": {"total": 0, "available": 0, "occupied": 0, "reserved": 0},
        "EV": {"total": 0, "available": 0, "occupied": 0, "reserved": 0},
        "Disabled": {"total": 0, "available": 0, "occupied": 0, "reserved": 0}
    }
    for s in spaces:
        ptype = s.get("parking_type", "Regular")
        if ptype in type_stats:
            type_stats[ptype]["total"] += 1
            status_lower = s["status"].lower()
            if status_lower == "available":
                type_stats[ptype]["available"] += 1
            elif status_lower == "occupied":
                type_stats[ptype]["occupied"] += 1
            elif status_lower == "reserved":
                type_stats[ptype]["reserved"] += 1

    return {
        "total_spaces": total,
        "available_spaces": available,
        "occupied_spaces": occupied,
        "reserved_spaces": reserved,
        "occupancy_percentage": occupancy_rate,
        "type_stats": type_stats
    }


if __name__ == "__main__":
    ensure_dataset()
    print("Dataset initialized successfully with", len(load_dataset()), "spaces.")
    print("Summary statistics:", calculate_statistics())
