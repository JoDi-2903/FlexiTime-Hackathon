import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from flask import Flask, jsonify, request

app = Flask(__name__)

# In-memory storage
# TODO: Move to database when connection to it is established
tasks: Dict[str, Dict] = {}
call_protocols: Dict[str, List[Dict]] = {}
users: Dict[str, Dict] = {}
doctors: Dict[str, Dict] = {}


# TASK SPECIFIC ENDPOINTS
@app.route("/schedule_call_task", methods=["POST"])
def schedule_call_task():
    """
    Schedule a call task for appointment booking
    Expected JSON payload:
    {
        "user_id": "string",
        "doctor_id": "string",
        "appointment_reason": "string",
        "additional_remark": "string",
        "date": "string",
        "time_range_start": "string",
        "time_range_end": "string"
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = [
            "user_id",
            "doctor_id",
            "appointment_reason",
            "additional_remark",
            "date",
            "time_range_start",
            "time_range_end",
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
            "user_id": data["user_id"],
            "doctor_id": data["doctor_id"],
            "appointment_reason": data["appointment_reason"],
            "additional_remark": data["additional_remark"],
            "date": data["date"],
            "time_range_start": data["time_range_start"],
            "time_range_end": data["time_range_end"],
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


# DOCTOR AND USER MANAGEMENT ENDPOINTS
@app.route("/update_profile", methods=["PUT"])
def update_profile():
    """
    Update user profile information
    Expected JSON payload:
    {
        "user_id": "string",
        "first_name": "string",
        "surname": "string",
        "birth_date": "string",
        "insurance": "string"
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["user_id", "first_name", "surname", "birth_date", "insurance"]
        for field in required_fields:
            if field not in data:
                return (
                    jsonify({"error": f"Missing required field: {field}", "status": "error"}),
                    400,
                )

        user_id = data["user_id"]

        # Create user profile if it doesn't exist, otherwise update
        if user_id not in users:
            users[user_id] = {}

        # Update user information
        users[user_id].update(
            {
                "user_id": user_id,
                "first_name": data["first_name"],
                "surname": data["surname"],
                "birth_date": data["birth_date"],
                "insurance": data["insurance"],
                "updated_at": datetime.now().isoformat(),
            }
        )

        return jsonify({"status": "saved successfully", "user_id": user_id}), 200

    except Exception as e:
        return jsonify({"status": "error", "error": f"Internal server error: {str(e)}"}), 500


@app.route("/add_doctor", methods=["POST"])
def add_doctor():
    """
    Add a new doctor to the system
    Expected JSON payload:
    {
        "name": "string",
        "phone": "string",
        "opening_hours": "string",
        "profession": "string"
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["name", "phone", "opening_hours", "profession"]
        for field in required_fields:
            if field not in data:
                return (
                    jsonify({"error": f"Missing required field: {field}", "status": "error"}),
                    400,
                )

        # Generate unique doctor ID
        doctor_id = str(uuid.uuid4())

        # Create doctor entry
        doctor = {
            "doctor_id": doctor_id,
            "name": data["name"],
            "phone": data["phone"],
            "opening_hours": data["opening_hours"],
            "profession": data["profession"],
            "created_at": datetime.now().isoformat(),
        }

        # Store doctor
        # TODO: Replace with database storage
        doctors[doctor_id] = doctor

        return jsonify({"status": "saved successfully", "doctor_id": doctor_id}), 201

    except Exception as e:
        return jsonify({"status": "error", "error": f"Internal server error: {str(e)}"}), 500


@app.route("/update_doctor", methods=["PUT"])
def update_doctor():
    """
    Update an existing doctor's information
    Expected JSON payload:
    {
        "doctor_id": "string",
        "name": "string",
        "phone": "string",
        "opening_hours": "string",
        "profession": "string"
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["doctor_id", "name", "phone", "opening_hours", "profession"]
        for field in required_fields:
            if field not in data:
                return (
                    jsonify({"error": f"Missing required field: {field}", "status": "error"}),
                    400,
                )

        doctor_id = data["doctor_id"]

        # Check if doctor exists
        if doctor_id not in doctors:
            return jsonify({"error": "Doctor not found", "status": "error"}), 404

        # Update doctor information
        doctors[doctor_id].update(
            {
                "name": data["name"],
                "phone": data["phone"],
                "opening_hours": data["opening_hours"],
                "profession": data["profession"],
                "updated_at": datetime.now().isoformat(),
            }
        )

        return jsonify({"status": "saved successfully", "doctor_id": doctor_id}), 200

    except Exception as e:
        return jsonify({"status": "error", "error": f"Internal server error: {str(e)}"}), 500


@app.route("/delete_doctor/<doctor_id>", methods=["DELETE"])
def delete_doctor(doctor_id: str):
    """
    Delete a doctor from the system
    """
    try:
        # Check if doctor exists
        if doctor_id not in doctors:
            return jsonify({"error": "Doctor not found", "status": "error"}), 404

        # Remove doctor
        # TODO: Replace with database delete operation
        del doctors[doctor_id]

        return jsonify({"status": "saved successfully", "doctor_id": doctor_id}), 200

    except Exception as e:
        return jsonify({"status": "error", "error": f"Internal server error: {str(e)}"}), 500


@app.route("/list_all_doctors", methods=["GET"])
def list_all_doctors():
    """
    Get a list of all doctors in the system
    Returns: List of doctor information
    """
    try:
        doctor_list = []

        # TODO: Replace with database query to fetch doctors
        for doctor_id, doctor in doctors.items():
            doctor_info = {
                "doctor_id": doctor_id,
                "name": doctor["name"],
                "phone": doctor["phone"],
                "opening_hours": doctor["opening_hours"],
                "profession": doctor["profession"],
            }
            doctor_list.append(doctor_info)

        return jsonify({"doctors": doctor_list, "count": len(doctor_list)}), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


# HEALTH CHECK AND ROOT ENDPOINTS
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
