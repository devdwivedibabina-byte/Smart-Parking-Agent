"""
agent.py - Intelligent Parking Management Agent
===============================================
Implements a Goal-Based & Utility-Based Rational Agent for parking space allocation.

Artificial Intelligence Concepts Demonstrated:
----------------------------------------------
1. PEAS Formalization:
   - Performance Measure: Minimize driver walking distance, minimize search time,
     maximize allocation success, avoid recommending occupied/reserved slots.
   - Environment: Discrete 2D parking lot coordinates, dynamic slot occupancies,
     heterogeneous slot types (Regular, EV, Disabled).
   - Actuators: UI recommendation highlight, route distance computation,
     slot reservation lock, audible/visual driver guidance.
   - Sensors: IoT ultrasonic/magnetic parking sensors, driver GPS/entrance coordinates,
     driver preference selector, max walking distance constraint.

2. Rational Agent Behavior:
   For each possible percept sequence, a rational agent selects an action that is
   expected to maximize its performance measure, given the evidence provided by the
   percept sequence and whatever built-in knowledge the agent has.

3. Utility Function:
   U(slot) = - Euclidean_Distance(driver, slot)
   Subject to:
     slot.status == 'Available'
     slot.parking_type == driver.preferred_type
     Euclidean_Distance(driver, slot) <= max_distance
"""

import math
from datetime import datetime


class SmartParkingAgent:
    """
    An intelligent rule-based rational agent that allocates optimal parking spaces
    based on driver location, vehicle constraints, and environmental telemetry.
    """

    def __init__(self):
        # Academic PEAS Specification Definition
        self.peas_description = {
            "performance_measure": [
                "Minimize driver walking distance from vehicle to destination/entrance",
                "Minimize parking search time and environmental carbon footprint",
                "Maximize successful allocation rate (100% collision-free)",
                "Strictly avoid recommending Occupied or Reserved parking bays"
            ],
            "environment": [
                "Parking facility divided into Zone A, Zone B, and Zone C",
                "Grid coordinates (X, Y in meters) for bays and access gates",
                "Dynamic occupancy states (Available, Occupied, Reserved)",
                "Heterogeneous parking bay types: Regular, EV Charging, Disabled / Accessible",
                "Stochastic vehicle arrivals and departures over time"
            ],
            "actuators": [
                "Visual recommendation badge and spotlight on interactive lot map",
                "Turn-by-turn distance and walking time calculation display",
                "Automated slot status update (Reserve / Occupy trigger)",
                "Rational reasoning breakdown and candidate alternative display"
            ],
            "sensors": [
                "Simulated IoT presence sensors (telemetry of slot availability)",
                "Driver location sensor (Entrance Gate coordinates X, Y)",
                "Driver vehicle preference filter (Regular, EV, Disabled)",
                "Driver walking endurance threshold (Maximum Distance in meters)"
            ],
            "environment_properties": {
                "observability": "Fully Observable (IoT sensors provide complete state telemetry)",
                "determinism": "Deterministic decision-making given static snapshot (Stochastic traffic)",
                "episodic": "Episodic (Each recommendation episode evaluates the current percept state)",
                "static_dynamic": "Dynamic (Parking slot availability changes in real-time)",
                "discrete_continuous": "Discrete parking spaces with Continuous metric coordinates",
                "agent_type": "Utility-based Rational Agent (Maximizes proximity utility)"
            }
        }

        # Internal agent memory & decision audit logs
        self.decision_history = []
        self.successful_recommendations = 0
        self.total_recommendation_requests = 0

    @staticmethod
    def calculate_euclidean_distance(x1, y1, x2, y2):
        """
        Calculates the 2D Euclidean distance between two points:
        Distance = sqrt((x2 - x1)^2 + (y2 - y1)^2)
        """
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def perceive(self, parking_spaces, driver_x, driver_y, preferred_type, max_distance):
        """
        Percept formulation: Ingests environment telemetry and driver requirements.
        Returns a structured percept dictionary.
        """
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "driver_location": {"x": float(driver_x), "y": float(driver_y)},
            "preferred_type": str(preferred_type),
            "max_distance": float(max_distance),
            "total_spaces_in_env": len(parking_spaces)
        }

    def evaluate_and_recommend(self, parking_spaces, driver_x, driver_y, preferred_type="Regular", max_distance=50.0):
        """
        Main Rational Decision-Making Pipeline:
        
        Step 1: Receive driver location & preferences (Sensors).
        Step 2: Collect real-time parking space telemetry.
        Step 3: Filter out Occupied and Reserved spaces.
        Step 4: Filter by vehicle parking type (Regular / EV / Disabled).
        Step 5: Compute Euclidean distance for all eligible candidates.
        Step 6: Filter out spaces exceeding the maximum walking distance.
        Step 7: Utility evaluation: Select minimum distance candidate.
                Tie-breaking rule: Select lower slot ID (e.g., P01 < P05).
        Step 8: Construct rational explanation and secondary alternatives.
        """
        self.total_recommendation_requests += 1
        percept = self.perceive(parking_spaces, driver_x, driver_y, preferred_type, max_distance)

        # -------------------------------------------------------------
        # Step 1 & 2: Environment Analysis
        # -------------------------------------------------------------
        total_slots = len(parking_spaces)
        available_slots = []
        occupied_count = 0
        reserved_count = 0

        for space in parking_spaces:
            status = space.get("status", "Available")
            if status == "Occupied":
                occupied_count += 1
            elif status == "Reserved":
                reserved_count += 1
            elif status == "Available":
                available_slots.append(space)

        # -------------------------------------------------------------
        # Step 3: Filter by Vehicle Parking Type
        # -------------------------------------------------------------
        type_matched_slots = []
        type_mismatched_count = 0

        for space in available_slots:
            slot_type = space.get("parking_type", "Regular")
            # Exact type matching for safety and accessibility compliance
            if preferred_type.lower() == "all" or slot_type.lower() == preferred_type.lower():
                type_matched_slots.append(space)
            else:
                type_mismatched_count += 1

        # -------------------------------------------------------------
        # Step 4: Distance Metric Calculation (Euclidean Distance)
        # -------------------------------------------------------------
        candidate_evaluations = []
        for space in type_matched_slots:
            dist = self.calculate_euclidean_distance(
                percept["driver_location"]["x"],
                percept["driver_location"]["y"],
                space["x"],
                space["y"]
            )
            candidate_evaluations.append({
                "id": space["id"],
                "slot_number": space["slot_number"],
                "zone": space["zone"],
                "x": space["x"],
                "y": space["y"],
                "parking_type": space["parking_type"],
                "status": space["status"],
                "hourly_rate": space.get("hourly_rate", 2.50),
                "features": space.get("features", "Standard Bay"),
                "distance": round(dist, 2)
            })

        # Sort candidate spaces by distance (ascending);
        # Tie-breaker: alphabetical/numerical slot ID (e.g., P02 before P05)
        candidate_evaluations.sort(key=lambda s: (s["distance"], s["id"]))

        # -------------------------------------------------------------
        # Step 5: Filter by Maximum Walking Distance Constraint
        # -------------------------------------------------------------
        distance_exceeded_count = 0
        valid_candidates = []

        for candidate in candidate_evaluations:
            if candidate["distance"] <= percept["max_distance"]:
                valid_candidates.append(candidate)
            else:
                distance_exceeded_count += 1

        # -------------------------------------------------------------
        # Step 6 & 7: Rational Decision Selection & Justification
        # -------------------------------------------------------------
        decision_result = {
            "success": False,
            "recommended_slot": None,
            "alternative_slots": [],
            "percept": percept,
            "statistics": {
                "total_spaces": total_slots,
                "available_spaces": len(available_slots),
                "occupied_spaces": occupied_count,
                "reserved_spaces": reserved_count,
                "type_matched_available": len(type_matched_slots),
                "distance_compliant_candidates": len(valid_candidates),
                "eliminated_due_to_occupancy": occupied_count + reserved_count,
                "eliminated_due_to_type": type_mismatched_count,
                "eliminated_due_to_distance": distance_exceeded_count
            },
            "reasoning_steps": [],
            "rational_explanation": "",
            "estimated_walking_time_min": 0.0
        }

        # Build step-by-step reasoning narrative for AI viva demonstration
        reasoning = [
            f"Sensors registered driver location at ({percept['driver_location']['x']:.1f}m, {percept['driver_location']['y']:.1f}m) with preference: '{preferred_type}' and max walking distance: {max_distance}m.",
            f"Total parking bays in environment: {total_slots}. Filtered out {occupied_count} Occupied and {reserved_count} Reserved bays.",
            f"Evaluated {len(available_slots)} available bays. {len(type_matched_slots)} match requested vehicle type '{preferred_type}'.",
            f"Applied 2D Euclidean Distance formula: d = sqrt((x2-x1)^2 + (y2-y1)^2) from driver coordinates to each candidate."
        ]

        if valid_candidates:
            # Optimal rational choice: Candidate with minimum distance
            best_slot = valid_candidates[0]
            # Walking speed estimation: Average human walking speed ~ 1.3 m/s (approx 78 m/min)
            est_walk_min = round(best_slot["distance"] / 78.0, 1)
            if est_walk_min < 0.2:
                est_walk_min = 0.2

            decision_result["success"] = True
            decision_result["recommended_slot"] = best_slot
            # Provide up to 2 alternative backup options
            decision_result["alternative_slots"] = valid_candidates[1:3]
            decision_result["estimated_walking_time_min"] = est_walk_min

            reasoning.append(
                f"Filtered candidates exceeding {max_distance}m walking constraint (eliminated {distance_exceeded_count} spaces)."
            )
            reasoning.append(
                f"Optimal rational choice: Slot '{best_slot['id']}' in {best_slot['zone']} at minimum Euclidean distance of {best_slot['distance']}m."
            )
            if len(valid_candidates) > 1 and valid_candidates[0]["distance"] == valid_candidates[1]["distance"]:
                reasoning.append(
                    f"Tie-breaking rule triggered: Slots '{valid_candidates[0]['id']}' and '{valid_candidates[1]['id']}' have identical distance. Selected '{best_slot['id']}' by alphanumeric order."
                )

            decision_result["rational_explanation"] = (
                f"Slot {best_slot['id']} is the rational optimal selection. It satisfies all constraints: "
                f"it is currently Available, matches vehicle type '{best_slot['parking_type']}', "
                f"and minimizes the driver's walking distance to {best_slot['distance']}m "
                f"(~{est_walk_min} min walk). No other available {preferred_type} bay offers lower proximity cost."
            )

            self.successful_recommendations += 1

        else:
            # Failure / Unavailability recovery reasoning
            reasoning.append(
                f"Zero spaces met all constraints simultaneously within the {max_distance}m distance threshold."
            )

            # Suggest relaxation advice
            if candidate_evaluations:
                nearest_unreachable = candidate_evaluations[0]
                excess_dist = round(nearest_unreachable["distance"] - max_distance, 1)
                decision_result["rational_explanation"] = (
                    f"No suitable '{preferred_type}' parking space found within your maximum distance of {max_distance}m. "
                    f"The nearest available '{preferred_type}' bay is {nearest_unreachable['id']} located {nearest_unreachable['distance']}m away "
                    f"({excess_dist}m beyond your limit). Recommendation: Increase your maximum walking distance or consider other zones."
                )
                decision_result["alternative_slots"] = candidate_evaluations[:2]
            else:
                decision_result["rational_explanation"] = (
                    f"No available '{preferred_type}' parking bays exist in the entire facility. "
                    f"All spaces of this type are currently Occupied or Reserved. "
                    f"Recommendation: Wait for a spot to become available or select an alternative parking type."
                )

        decision_result["reasoning_steps"] = reasoning

        # Append to agent decision history log
        log_entry = {
            "id": len(self.decision_history) + 1,
            "timestamp": percept["timestamp"],
            "driver_location": f"({percept['driver_location']['x']:.1f}, {percept['driver_location']['y']:.1f})",
            "preference": preferred_type,
            "max_distance": f"{max_distance}m",
            "recommended_slot": decision_result["recommended_slot"]["id"] if decision_result["success"] else "None",
            "distance": f"{decision_result['recommended_slot']['distance']}m" if decision_result["success"] else "N/A",
            "status": "Success" if decision_result["success"] else "Failed (No Feasible Slot)",
            "summary": decision_result["rational_explanation"]
        }
        self.decision_history.insert(0, log_entry)  # Most recent first
        # Keep last 50 decisions
        if len(self.decision_history) > 50:
            self.decision_history.pop()

        return decision_result

    def get_decision_history(self):
        """Returns the logged decision history."""
        return self.decision_history

    def get_peas(self):
        """Returns the formal PEAS representation dictionary."""
        return self.peas_description

    def get_agent_metrics(self):
        """Returns performance metrics for the agent."""
        success_rate = (
            round((self.successful_recommendations / self.total_recommendation_requests * 100), 1)
            if self.total_recommendation_requests > 0 else 100.0
        )
        return {
            "total_recommendations": self.total_recommendation_requests,
            "successful_recommendations": self.successful_recommendations,
            "success_rate_percent": success_rate,
            "history_count": len(self.decision_history)
        }


# Quick standalone validation test
if __name__ == "__main__":
    from parking_data import load_dataset
    agent = SmartParkingAgent()
    spaces = load_dataset()
    res = agent.evaluate_and_recommend(spaces, driver_x=0.0, driver_y=10.0, preferred_type="Regular", max_distance=30.0)
    print("Recommendation Test:")
    print("Success:", res["success"])
    if res["success"]:
        print("Recommended Slot:", res["recommended_slot"]["id"], "Distance:", res["recommended_slot"]["distance"])
        print("Reasoning:", res["rational_explanation"])
