-- Database schema for the appointment management system
CREATE TABLE doctors
(
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    opening_hours VARCHAR(100),
    phone_number VARCHAR(20),
    specialty VARCHAR(100)
);

CREATE TABLE users
(
    id VARCHAR(36) PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE,
    insurance VARCHAR(100)
);

CREATE TABLE tasks
(
    task_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    doctor_id VARCHAR(36) REFERENCES doctors(id),
    appointment_reason TEXT NOT NULL,
    additional_remark TEXT,
    appointment_date DATE NOT NULL,
    time_range_start TIME NOT NULL,
    time_range_end TIME NOT NULL,
    status_code VARCHAR(50) DEFAULT 'scheduled',
    booked_appointment TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE call_protocols
(
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(36) REFERENCES tasks(task_id),
    speaker VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE call_logs
(
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(36) REFERENCES tasks(task_id),
    log_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50),
    log TEXT
);

-- Indexes for performance
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_doctor_id ON tasks(doctor_id);
CREATE INDEX idx_call_protocols_task_id ON call_protocols(task_id);
CREATE INDEX idx_call_logs_task_id ON call_logs(task_id);
