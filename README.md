# Intelligent Preventive Healthcare Decision Support System

An AI-powered preventive healthcare web application that helps users assess health risks, understand prediction results, monitor health trends, manage wellness goals, and receive personalized health guidance.

---

# Project Overview

The **Intelligent Preventive Healthcare Decision Support System** is designed to support early health risk identification and preventive healthcare decision-making using machine learning, rule-based analysis, and AI-driven explanations.

The system combines:

* Machine learning-based disease prediction
* Rule-based health risk assessment
* AI-powered chatbot and explanations
* Health monitoring and trend analysis
* Goal and task management
* Gamification and progress tracking
* Preventive healthcare reporting

The platform helps users identify possible health risks early and take preventive actions before conditions become severe.

---

# Key Features

## 1. Health Risk Prediction

Users can enter personal, medical, and lifestyle data to predict health risks.

### Input Parameters

* Age
* Gender
* BMI
* Blood glucose
* HbA1c
* Blood pressure
* Smoking history
* Activity level
* Sleep hours
* Stress level
* Diet type
* Work type
* Hypertension history
* Heart disease history

### Prediction Outputs

* Diabetes risk
* Heart disease risk
* Hypertension risk
* Obesity risk
* Metabolic syndrome risk
* Stroke risk
* Kidney disease risk
* Cholesterol disorder risk
* Overall cardiovascular risk
* Overall health score
* AI-generated explanation
* Personalized recommendations
* Downloadable report

---

## 2. Health Simulation

Users can test **“what-if” scenarios** by modifying health values and checking how risks change.

### Outputs

* Previous risk
* Updated risk
* Risk improvement or worsening
* Comparative analysis

---

## 3. User Profile Management

Displays structured personal, medical, and lifestyle information.

### Includes

* Personal details
* Health metrics
* Lifestyle data
* Medical conditions
* Health summary

---

## 4. Health Monitoring

Tracks health-related activities and metrics over time.

### Outputs

* Monitoring history
* Vital trends
* Health alerts
* Monitoring reports

---

## 5. AI Insights Engine

Generates meaningful insights by combining:

* Prediction results
* Monitoring data
* Behavioral data

### Outputs

* Insight summaries
* Key risk drivers
* Trend analysis
* Risk interaction analysis
* Behavioral impact analysis
* Actionable recommendations

---

## 6. Intelligent AI Chatbot

An AI-powered healthcare assistant that answers:

* Application-related questions
* General healthcare questions
* Personalized prediction-related questions

### Example Questions

* “Explain my prediction result”
* “Is my health condition improving?”
* “What precautions should I take?”

---

## 7. Goals Management

Allows users to create and manage preventive healthcare goals.

Examples:

* Improve sleep quality
* Increase physical activity
* Reduce sugar intake
* Maintain healthy BMI

---

## 8. Goals & Progress Tracking

Tracks user tasks, progress, and preventive healthcare improvements.

### Outputs

* Task completion rate
* Goal progress
* Projected health improvement

---

## 9. Behavior Logging

Stores and analyzes user health behaviors.

### Includes

* Sleep tracking
* Activity tracking
* Diet logging
* Medication tracking
* Lifestyle habits

---

## 10. Health Alerts

Generates alerts and warnings based on abnormal health conditions and monitoring data.

---

## 11. Gamification System

Improves user engagement using:

* Reward points
* Streak tracking
* Achievement badges

---

## 12. PDF Health Report Generation

Users can download professionally styled preventive healthcare reports.

---

# Diseases Covered

The system currently supports prediction and risk analysis for:

1. Diabetes
2. Prediabetes
3. Hypertension
4. Heart Disease
5. Obesity
6. Metabolic Syndrome
7. Stroke Risk
8. Chronic Kidney Disease Risk
9. Cholesterol Disorder Risk
10. Overall Cardiovascular Disease Risk

---

# Machine Learning Models

## Models Used

The project uses **RandomForestClassifier** models for:

* Diabetes prediction
* Heart disease prediction
* Hypertension prediction

---

## Why Random Forest?

Random Forest was selected because it:

* Performs well on structured healthcare datasets
* Handles nonlinear relationships effectively
* Supports both numerical and categorical features
* Provides stable and reliable performance
* Is practical for MVP deployment

---

## Why Not Other Models?

### Logistic Regression

* Simpler but may not capture nonlinear patterns effectively

### Deep Learning

* Unnecessary for structured tabular healthcare data

### XGBoost / LightGBM

* Powerful alternatives, but Random Forest provides a simpler and more interpretable setup for this project

---

# AI Integration

The project supports multiple AI providers:

* OpenAI
* Gemini
* xAI / Grok

These are used for:

* Chatbot responses
* AI-generated explanations
* Personalized recommendations
* Insight generation

---

# Tech Stack

## Frontend

* Next.js
* React
* TypeScript
* Tailwind CSS
* Recharts

## Backend

* FastAPI
* SQLAlchemy
* Pydantic
* Uvicorn

## Machine Learning & Data Processing

* scikit-learn
* pandas
* numpy
* SHAP
* matplotlib
* joblib

## Database

* SQLite (local development)
* PostgreSQL (deployment)

## PDF Reporting

* ReportLab

---

# Authentication

The system includes:

* User signup
* User login
* JWT-based authentication

---

# Dataset Split

The machine learning dataset is divided using stratified splitting:

* 80% Training Data
* 20% Testing Data

This helps maintain balanced class distribution.

---

# Project Workflow

1. User signs up and logs in
2. User enters health and lifestyle data
3. The system predicts multiple disease risks
4. Rule-based scoring analyzes the prediction results
5. AI generates explanations and recommendations
6. Insights, goals, and tasks are generated
7. Users monitor progress over time
8. Reports can be downloaded for review

---

# Project Structure

```bash
PROJECT_PHASE-2_UPDATED/
│
├── backend/
│   ├── routes/
│   ├── services/
│   ├── db/
│   ├── model/
│   ├── utils/
│   ├── schemas/
│   └── app.py
│
├── frontend/
│   ├── pages/
│   ├── components/
│   ├── services/
│   ├── styles/
│   └── context/
│
├── render.yaml
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── README.md
```

---

# Deployment

The project is prepared for deployment using Render.

## Render Services

* Frontend web service
* Backend web service
* PostgreSQL database

### Deployment Files

* `render.yaml`
* `RENDER_DEPLOY.md`

---

# Future Enhancements

* Wearable device integration
* Advanced personalized recommendations
* Enhanced gamification features
* Doctor-facing analytics dashboard
* Email and notification automation
* Advanced trend forecasting models

---

# Author

Developed as an AI-based Preventive Healthcare Decision Support System project for academic and educational purposes.

---

# License

This project is intended for academic, educational, and demonstration purposes unless otherwise specified.
