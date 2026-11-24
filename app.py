"""
app.py - Smart Parking Management Agent Web Application
======================================================
Flask Web Server and RESTful API backend for the Smart Parking Agent.
Connects the Intelligent Rule-Based Agent with the interactive frontend.
"""

import os
from flask import Flask, render_template, jsonify, request
import parking_data
from agent import SmartParkingAgent

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

# Initialize single global agent instance to retain decision history & metrics
parking_agent = SmartParkingAgent()


@app.route("/")
def index():
    """Renders the main interactive dashboard."""
    return render_template("index.html")


@app.route("/api/parking-spaces", methods=["GET"])
def get_parking_spaces():
    """
    Returns all parking slots, summary statistics, and optionally
    computes distances from given driver coordinates (?driver_x=0&driver_y=10).
    """
    spaces = parking_data.load_dataset()
    stats = parking_data.calculate_statistics(spaces)

    # Optional driver position for live distance annotation
    driver_x = request.args.get("driver_x", type=float)
    driver_y = request.args.get("driver_y", type=float)

    if driver_x is not None and driver_y is not None:
        for s in spaces:
            dist = parking_agent.calculate_euclidean_distance(driver_x, driver_y, s["x"], s["y"])
            s["distance"] = round(dist, 2)
    else:
        for s in spaces:
            # Default reference distance from Gate A (0, 10)
            dist = parking_agent.calculate_euclidean_distance(0.0, 10.0, s["x"], s["y"])
            s["distance"] = round(dist, 2)

    return jsonify({
        "success": True,
        "spaces": spaces,
        "statistics": stats
    })


@app.route("/api/recommend", methods=["POST"])
def recommend_parking():
    """
    Executes the intelligent agent decision algorithm.
    Request JSON:
      - driver_x: float (default 0.0)
      - driver_y: float (default 10.0)
      - parking_type: 'Regular' | 'EV' | 'Disabled' (default 'Regular')
      - max_distance: float (default 50.0)
    """
    data = request.get_json() or {}
    driver_x = float(data.get("driver_x", 0.0))
    driver_y = float(data.get("driver_y", 10.0))
    parking_type = str(data.get("parking_type", "Regular"))
    max_distance = float(data.get("max_distance", 50.0))

    spaces = parking_data.load_dataset()

    # Run rational agent decision pipeline
    result = parking_agent.evaluate_and_recommend(
        parking_spaces=spaces,
        driver_x=driver_x,
        driver_y=driver_y,
        preferred_type=parking_type,
        max_distance=max_distance
    )

    # Attach updated global agent metrics
    result["agent_metrics"] = parking_agent.get_agent_metrics()
    return jsonify(result)


@app.route("/api/slot/<slot_id>/toggle", methods=["POST"])
def toggle_slot_status(slot_id):
    """
    Cycles slot status: Available -> Occupied -> Reserved -> Available.
    Allows manual scenario testing during university presentations.
    """
    spaces = parking_data.load_dataset()
    cycle_order = {"Available": "Occupied", "Occupied": "Reserved", "Reserved": "Available"}
    
    found = False
    new_status = "Available"
    for s in spaces:
        if s["id"].upper() == slot_id.upper():
            curr = s.get("status", "Available")
            new_status = cycle_order.get(curr, "Available")
            s["status"] = new_status
            found = True
            break

    if found:
        parking_data.save_dataset(spaces)
        return jsonify({
            "success": True,
            "slot_id": slot_id.upper(),
            "new_status": new_status,
            "statistics": parking_data.calculate_statistics(spaces)
        })
    else:
        return jsonify({"success": False, "error": f"Slot {slot_id} not found"}), 404


@app.route("/api/slot/<slot_id>/set-status", methods=["POST"])
def set_slot_status(slot_id):
    """Explicitly set a slot's status (Available, Occupied, Reserved)."""
    data = request.get_json() or {}
    status = data.get("status", "Available")
    if status not in ["Available", "Occupied", "Reserved"]:
        return jsonify({"success": False, "error": "Invalid status"}), 400

    found, spaces = parking_data.update_slot_status(slot_id, status)
    if found:
        return jsonify({
            "success": True,
            "slot_id": slot_id.upper(),
            "new_status": status,
            "statistics": parking_data.calculate_statistics(spaces)
        })
    return jsonify({"success": False, "error": f"Slot {slot_id} not found"}), 404


@app.route("/api/slot/<slot_id>/park", methods=["POST"])
def park_in_slot(slot_id):
    """Simulates driver parking in the recommended slot (sets status to Occupied)."""
    found, spaces = parking_data.update_slot_status(slot_id, "Occupied")
    if found:
        return jsonify({
            "success": True,
            "message": f"Driver successfully parked in slot {slot_id}. Status updated to Occupied.",
            "statistics": parking_data.calculate_statistics(spaces)
        })
    return jsonify({"success": False, "error": f"Slot {slot_id} not found"}), 404


@app.route("/api/dataset/reset", methods=["POST"])
def reset_dataset():
    """Resets dataset to default baseline."""
    fresh_spaces = parking_data.reset_dataset()
    return jsonify({
        "success": True,
        "message": "Dataset reset to baseline successfully.",
        "spaces": fresh_spaces,
        "statistics": parking_data.calculate_statistics(fresh_spaces)
    })


@app.route("/api/dataset/randomize", methods=["POST"])
def randomize_dataset():
    """Randomizes lot occupancy."""
    rand_spaces = parking_data.randomize_dataset()
    return jsonify({
        "success": True,
        "message": "Parking space occupancy randomized.",
        "spaces": rand_spaces,
        "statistics": parking_data.calculate_statistics(rand_spaces)
    })


@app.route("/api/dataset/simulate-step", methods=["POST"])
def simulate_traffic_step():
    """Simulates a single tick of dynamic traffic arrivals and departures."""
    updated_spaces, events = parking_data.simulate_traffic_step()
    return jsonify({
        "success": True,
        "message": f"Simulation step completed ({len(events)} events).",
        "events": events,
        "spaces": updated_spaces,
        "statistics": parking_data.calculate_statistics(updated_spaces)
    })


@app.route("/api/agent/history", methods=["GET"])
def get_agent_history():
    """Returns the decision history log and cumulative metrics."""
    return jsonify({
        "success": True,
        "history": parking_agent.get_decision_history(),
        "metrics": parking_agent.get_agent_metrics()
    })


@app.route("/api/agent/peas", methods=["GET"])
def get_peas_description():
    """Returns formal PEAS representation and environment analysis."""
    return jsonify({
        "success": True,
        "peas": parking_agent.get_peas()
    })


if __name__ == "__main__":
    parking_data.ensure_dataset()
    print("Starting Smart Parking Management Agent on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
