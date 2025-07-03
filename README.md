# FlexiTime - Efficient Medical Appointment Scheduling

**Efficient appointment booking for individuals - fast, secure, and flexible**

## 📋 Overview

FlexiTime is a web application designed to revolutionize medical appointment scheduling by eliminating the frustration of long waiting times and complicated booking systems. Our solution addresses the fact that people spend an average of **374 days** of their lifetime waiting - time that could be better invested in family, career, or personal well-being.

## 🎯 Problem Statement

- **374 days** - Average lifetime spent waiting
- **7 hours per year** - Time spent on hold during phone calls in Germany
- **45% of patients** report that long phone waiting times and complicated booking systems are their biggest frustration when scheduling medical appointments

## 💡 Solution

FlexiTime provides a comprehensive platform that enables users to book appointments quickly and efficiently without long waiting times through:

- **Automated calls** - No more phone queues
- **Zero waiting times** - Instant booking capability  
- **Maximum flexibility** - Book appointments 24/7
- **Barrier-free access** - Accessible for all users including those with hearing impairments, language barriers, or social anxiety

## 🖥️ Application Screenshots

### Main Booking Interface

![Screenshot_FlexiTime_1](https://github.com/user-attachments/assets/9d3089b4-878a-46a0-bcfb-574153a506f3)

*Simple and intuitive appointment booking form with doctor selection, reason for visit, and flexible date/time options*

### User Profile Management
![Screenshot_FlexiTime_4](https://github.com/user-attachments/assets/e9a137e2-7418-4360-9b5e-2eb5ab12b628)

### Calendar
![2Screenshot_FlexiTime_1](https://github.com/user-attachments/assets/80e68e36-23bd-49b1-8b5f-8b0ed2c99093)

## 📞 Demo call with the AI agent

https://github.com/user-attachments/assets/0e06293f-f8d2-4b54-83df-559f6a9af71f


## 🏗️ Technical Architecture

### Frontend
- **Framework**: AngularJS
- **Design**: User-friendly interface with focus on accessibility
- **Responsive**: Optimized for all devices

### Backend
- **Architecture**: Docker Microservices
- **Cloud Platform**: AWS
- **AI Integration**: Claude 3.5 Haiku for intelligent appointment scheduling
- **Services**: EC2 for Docker connectivity and text-to-speech functionality

### Database
- Secure storage of user profiles and doctor information
- Automated calendar coordination
- Call protocol logging

## 🔌 REST API Documentation

```JSON
{
  "api_name": "Medical Appointment Scheduling API",
  "endpoints": {
    "DELETE /delete_doctor/<doctor_id>": "Delete a doctor from the system",
    "GET /get_task_call_protocol/<task_id>": "Get call protocol for specific task",
    "GET /get_task_results": "Get list of all task results",
    "GET /get_user_details/<user_id>": "Get user profile details by user ID",
    "GET /health": "Health check endpoint",
    "GET /list_all_doctors": "Get a list of all doctors in the system",
    "POST /add_doctor": "Add a new doctor to the system",
    "POST /schedule_call_task": "Schedule a new call task for appointment booking",
    "PUT /update_doctor": "Update an existing doctor's information",
    "PUT /update_profile": "Update user profile information"
  },
  "version": "1.0.0"
}
```

## 🎯 Target Audience

### Primary Market
- **DACH Region** (Germany, Austria, Switzerland)
- German-speaking individuals with internet access

### Inclusive Design For
- **Hearing-impaired individuals** - Visual interface eliminates phone communication barriers
- **People with migration background** - Multilingual support planned
- **Individuals with social anxiety** - Avoids stressful phone interactions
- **General population** - Anyone wanting to save time and avoid waiting

## 🚀 Future Vision

FlexiTime aims to expand beyond medical appointments to become a comprehensive booking platform for:

- **Automotive services** (workshops, inspections)
- **Government offices** (appointments with authorities)
- **Insurance consultations**
- **General service appointments**

### Planned Features
- **Multilingual support** with Claude Opus 4 integration
- **Automated calendar coordination**
- **Advanced call protocols**
- **Personal doctor database**
- **Mobile application**

*FlexiTime - Giving people back control over their time and creating a world where nobody loses time through appointment booking.*
