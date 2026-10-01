# 🤖 AI Business Automation

AI-powered business automation system for managing customer inquiries, generating intelligent replies, and streamlining email communication.

## 📌 About the Project

AI Business Automation is a web application designed to help businesses manage customer communication more efficiently.

The system uses AI to generate personalized responses to customer inquiries while keeping a human in control before any response is sent.

The workflow is:

**Customer Inquiry → AI Generated Reply → Human Review → Approve / Edit / Reject → Email Sent**

This approach combines AI automation with human oversight.

---

## ✨ Key Features

### 🤖 AI-Powered Replies

Generate personalized customer responses using Google's Gemini AI.

The AI behavior can be customized based on:

- Company name
- Response language
- Response tone
- Custom AI instructions

### 📧 Gmail Integration

The system connects with Gmail to support customer communication.

It can:

- Read incoming customer messages
- Generate AI responses
- Send approved responses through Gmail

### 👤 Human Approval System

AI responses are not sent automatically.

The user can:

- Review the response
- Edit the response
- Approve the response
- Reject the response
- Delete the request

This provides control over AI-generated communication.

### 📊 Dashboard

The dashboard provides an overview of customer requests and their status.

It includes:

- Total requests
- Pending requests
- Approved requests
- Rejected requests
- Search
- Request filtering
- Customer conversation view

### ⚙️ AI Settings

The system includes a dedicated settings page where the business can configure:

- Company name
- Response language
- Response tone
- AI instructions

### 💾 Data Management

Customer requests and their statuses are stored using SQLite.

---

## 🛠️ Technologies

### Backend

- Python
- Flask
- SQLite

### AI

- Google Gemini API

### Email

- Gmail API
- Gmail SMTP

### Frontend

- HTML
- CSS
- JavaScript
- Jinja2

### Tools

- Git
- GitHub
- Visual Studio Code

---

## 🔄 How It Works

```text
Customer
   │
   ▼
Customer Inquiry
   │
   ▼
AI Business Automation
   │
   ▼
Gemini AI
   │
   ▼
Generated Reply
   │
   ▼
Human Review
   │
   ├── Edit
   ├── Reject
   └── Approve
          │
          ▼
       Gmail
          │
          ▼
       Customer
       /*******************************************


🔐 Security
Sensitive credentials are not included in the repository.

The following files are excluded from Git:

.env

token.json

Database files

OAuth credentials

Virtual environment

Environment variables are configured locally using .env.

A safe configuration template is provided through:

.env.example

Never publish API keys, Gmail App Passwords, OAuth secrets, or access tokens.
/******************************************************
🚀 Installation
1. Clone the repository
Bash

git clone https://github.com/weammmmm/AI_Business_Automation.git
cd AI_Business_Automation
2. Create a virtual environment
Bash

python -m venv venv
3. Activate the environment
Windows PowerShell:

PowerShell

venv\Scripts\Activate.ps1
4. Install dependencies
Bash

pip install -r requirements.txt
5. Configure environment variables
Create a .env file using .env.example as a reference.

Add your own Gemini and Gmail credentials.

6. Run the application
Bash

python app.py
Open the application in your browser:


http://127.0.0.1:5000
🎯 Project Goal
The goal of this project is to demonstrate how AI can be integrated into real-world business workflows to reduce repetitive communication tasks while maintaining human control over important customer interactions.

👩‍💻 Project Type
AI Automation + Web Application + Email Integration

Built as a practical portfolio project demonstrating:

AI integration

Backend development

Frontend development

API integration

Email automation

Database management

Human-in-the-loop AI workflows