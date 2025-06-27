import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from flask import Flask, jsonify, request

app = Flask(__name__)

# In-memory storage for tasks and protocols
# TODO: Move to database when connection to it is established
tasks: Dict[str, Dict] = {}
call_protocols: Dict[str, List[Dict]] = {}


@app.route("/schedule_call_task", methods=["POST"])
def schedule_call_task():
    """
    Schedule a call task for appointment booking
    Expected JSON payload:
    {
        "doctor_id": "string",
        "user_id": "string",
        "appointment_type": "string",
        "reason": "string",
        "free_time_range_for_appointment": "string"
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = [
            "doctor_id",
            "user_id",
            "appointment_type",
            "reason",
            "free_time_range_for_appointment",
        ]
        for field in required_fields:
            if field not in data:
                return (
                    jsonify(
                        {
                            "error": f"Missing required field: {field}",
                            "status": "failed",
                        }
                    ),
                    400,
                )

        # Generate unique task ID
        task_id = str(uuid.uuid4())

        # Create task entry
        task = {
            "task_id": task_id,
            "doctor_id": data["doctor_id"],
            "user_id": data["user_id"],
            "appointment_type": data["appointment_type"],
            "reason": data["reason"],
            "free_time_range_for_appointment": data["free_time_range_for_appointment"],
            "status_code": "scheduled",
            "booked_appointment": None,
            "created_at": datetime.now().isoformat(),
        }

        # Store task
        # TODO: Replace with database storage
        tasks[task_id] = task

        return (
            jsonify(
                {
                    "message": "Task scheduled successfully",
                    "task_id": task_id,
                    "status": "scheduled",
                }
            ),
            201,
        )

    except Exception as e:
        return (
            jsonify({"error": f"Internal server error: {str(e)}", "status": "failed"}),
            500,
        )


@app.route("/get_task_results", methods=["GET"])
def get_task_results():
    """
    Get list of all task results
    Returns: List of [task_id, status_code, booked_appointment (optional)]
    """
    try:
        results = []

        # TODO: Replace with database query to fetch tasks
        for task_id, task in tasks.items():
            result = {
                "task_id": task_id,
                "status_code": task["status_code"],
                "booked_appointment": task.get("booked_appointment"),
            }
            results.append(result)

        return jsonify({"results": results, "total_count": len(results)}), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route("/get_task_call_protocol/<task_id>", methods=["GET"])
def get_task_call_protocol(task_id: str):
    """
    Get call protocol for a specific task
    Returns: Chat protocol of the call between AI-agent and medical assistant
    """
    try:
        # TODO: Replace with database query to fetch call protocols
        if task_id not in tasks:
            return jsonify({"error": "Task not found", "task_id": task_id}), 404

        if task_id not in call_protocols:
            return (
                jsonify(
                    {
                        "error": "Call protocol not available for this task",
                        "task_id": task_id,
                    }
                ),
                404,
            )

        return (
            jsonify(
                {
                    "task_id": task_id,
                    "call_protocol": call_protocols[task_id],
                    "task_status": tasks[task_id]["status_code"],
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return (
        jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "active_tasks": len(tasks),
            }
        ),
        200,
    )


@app.route("/", methods=["GET"])
def root():
    """API documentation"""
    return (
        jsonify(
            {
                "api_name": "Medical Appointment Scheduling API",
                "version": "1.0.0",
                "endpoints": {
                    "POST /schedule_call_task": "Schedule a new call task for appointment booking",
                    "GET /get_task_results": "Get list of all task results",
                    "GET /get_task_call_protocol/<task_id>": "Get call protocol for specific task",
                    "GET /health": "Health check endpoint",
                },
            }
        ),
        200,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
