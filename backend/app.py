import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import psycopg2
from flask import Flask, jsonify, request
from psycopg2.extras import RealDictCursor

app = Flask(__name__)


# Database connection function
def get_db_connection():
    conn = psycopg2.connect(
        host="terminagent-db.cty0uqagcewj.us-west-2.rds.amazonaws.com",
        port=5432,
        dbname="postgres",
        user="postgres",
        password="2WiIo5_g2-c+",
        # Note: Credentials should be stored securely in environment variables for a production system
    )
    conn.autocommit = True
    return conn


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

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert task into database
        cursor.execute(
            """
            INSERT INTO tasks (
                task_id, user_id, doctor_id, appointment_reason, 
                additional_remark, appointment_date, time_range_start,
                time_range_end, status_code, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                task_id,
                data["user_id"],
                data["doctor_id"],
                data["appointment_reason"],
                data["additional_remark"],
                data["date"],
                data["time_range_start"],
                data["time_range_end"],
                "scheduled",
                datetime.now(),
            ),
        )

        cursor.close()
        conn.close()

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
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT task_id, status_code, booked_appointment
            FROM tasks
            """
        )
        results = cursor.fetchall()

        cursor.close()
        conn.close()

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
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # First check if task exists
        cursor.execute("SELECT status_code FROM tasks WHERE task_id = %s", (task_id,))
        task = cursor.fetchone()

        if not task:
            cursor.close()
            conn.close()
            return jsonify({"error": "Task not found", "task_id": task_id}), 404

        # Get call protocols for this task
        cursor.execute(
            """
            SELECT * FROM call_protocols 
            WHERE task_id = %s
            ORDER BY timestamp ASC
            """,
            (task_id,),
        )
        protocols = cursor.fetchall()

        cursor.close()
        conn.close()

        if not protocols:
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
                    "call_protocol": protocols,
                    "task_status": task["status_code"],
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
        required_fields = [
            "user_id",
            "first_name",
            "surname",
            "birth_date",
            "insurance",
        ]
        for field in required_fields:
            if field not in data:
                return (
                    jsonify(
                        {"error": f"Missing required field: {field}", "status": "error"}
                    ),
                    400,
                )

        user_id = data["user_id"]
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if user:
            # Update existing user
            cursor.execute(
                """
                UPDATE users
                SET first_name = %s, last_name = %s, date_of_birth = %s, insurance = %s
                WHERE id = %s
                """,
                (
                    data["first_name"],
                    data["surname"],
                    data["birth_date"],
                    data["insurance"],
                    user_id,
                ),
            )
        else:
            # Create new user
            cursor.execute(
                """
                INSERT INTO users (id, first_name, last_name, date_of_birth, insurance)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    data["first_name"],
                    data["surname"],
                    data["birth_date"],
                    data["insurance"],
                ),
            )

        cursor.close()
        conn.close()

        return jsonify({"status": "saved successfully", "user_id": user_id}), 200

    except Exception as e:
        return (
            jsonify({"status": "error", "error": f"Internal server error: {str(e)}"}),
            500,
        )


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
                    jsonify(
                        {"error": f"Missing required field: {field}", "status": "error"}
                    ),
                    400,
                )

        # Generate unique doctor ID
        doctor_id = str(uuid.uuid4())

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO doctors (id, name, phone_number, opening_hours, specialty)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                doctor_id,
                data["name"],
                data["phone"],
                data["opening_hours"],
                data["profession"],
            ),
        )

        cursor.close()
        conn.close()

        return jsonify({"status": "saved successfully", "doctor_id": doctor_id}), 201

    except Exception as e:
        return (
            jsonify({"status": "error", "error": f"Internal server error: {str(e)}"}),
            500,
        )


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
                    jsonify(
                        {"error": f"Missing required field: {field}", "status": "error"}
                    ),
                    400,
                )

        doctor_id = data["doctor_id"]

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if doctor exists
        cursor.execute("SELECT id FROM doctors WHERE id = %s", (doctor_id,))
        if cursor.fetchone() is None:
            cursor.close()
            conn.close()
            return jsonify({"error": "Doctor not found", "status": "error"}), 404

        # Update doctor information
        cursor.execute(
            """
            UPDATE doctors
            SET name = %s, phone_number = %s, opening_hours = %s, specialty = %s
            WHERE id = %s
            """,
            (
                data["name"],
                data["phone"],
                data["opening_hours"],
                data["profession"],
                doctor_id,
            ),
        )

        cursor.close()
        conn.close()

        return jsonify({"status": "saved successfully", "doctor_id": doctor_id}), 200

    except Exception as e:
        return (
            jsonify({"status": "error", "error": f"Internal server error: {str(e)}"}),
            500,
        )


@app.route("/delete_doctor/<doctor_id>", methods=["DELETE"])
def delete_doctor(doctor_id: str):
    """
    Delete a doctor from the system
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if doctor exists
        cursor.execute("SELECT id FROM doctors WHERE id = %s", (doctor_id,))
        if cursor.fetchone() is None:
            cursor.close()
            conn.close()
            return jsonify({"error": "Doctor not found", "status": "error"}), 404

        # Delete doctor
        cursor.execute("DELETE FROM doctors WHERE id = %s", (doctor_id,))

        cursor.close()
        conn.close()

        return jsonify({"status": "saved successfully", "doctor_id": doctor_id}), 200

    except Exception as e:
        return (
            jsonify({"status": "error", "error": f"Internal server error: {str(e)}"}),
            500,
        )


@app.route("/list_all_doctors", methods=["GET"])
def list_all_doctors():
    """
    Get a list of all doctors in the system
    Returns: List of doctor information
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            """
            SELECT id as doctor_id, name, phone_number as phone, opening_hours, specialty as profession
            FROM doctors
            """
        )
        doctors = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({"doctors": doctors, "count": len(doctors)}), 200

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


# HEALTH CHECK AND ROOT ENDPOINTS
@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Count active tasks
        cursor.execute("SELECT COUNT(*) FROM tasks")
        task_count = cursor.fetchone()[0]

        # Test database connection
        cursor.execute("SELECT 1")

        cursor.close()
        conn.close()

        return (
            jsonify(
                {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "active_tasks": task_count,
                    "database": "connected",
                }
            ),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "database": "disconnected",
                }
            ),
            500,
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
                    # Task specific endpoints
                    "POST /schedule_call_task": "Schedule a new call task for appointment booking",
                    "GET /get_task_results": "Get list of all task results",
                    "GET /get_task_call_protocol/<task_id>": "Get call protocol for specific task",
                    # Doctor and user management endpoints
                    "PUT /update_profile": "Update user profile information",
                    "POST /add_doctor": "Add a new doctor to the system",
                    "PUT /update_doctor": "Update an existing doctor's information",
                    "DELETE /delete_doctor/<doctor_id>": "Delete a doctor from the system",
                    "GET /list_all_doctors": "Get a list of all doctors in the system",
                    # Health check endpoint
                    "GET /health": "Health check endpoint",
                },
            }
        ),
        200,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
