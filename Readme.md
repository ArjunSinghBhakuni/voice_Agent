# 🤖 TVS BTO AI Voice Agent

> **Intelligent Voice-Powered Customer Service for TVS Built-to-Order (BTO) Vehicles**

A production-ready AI voice agent that handles customer inquiries about vehicle bookings, delivery status, and cancellations through natural language conversation.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Agent](#running-the-agent)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)
- [Future Enhancements](#future-enhancements)

---

## 🎯 Overview

The TVS BTO AI Voice Agent is an automated customer service solution that:

- ✅ **Receives phone calls** from customers
- ✅ **Verifies identity** through phone number verification
- ✅ **Understands natural language** queries about vehicle bookings
- ✅ **Retrieves real-time data** from PostgreSQL database
- ✅ **Provides instant responses** about vehicle status, delivery, and cancellations
- ✅ **Escalates complex issues** to human support teams
- ✅ **Logs all interactions** for compliance and analysis

### 🎬 System Demo Flow

```
📞 Customer calls +1-978-723-7477
    ↓
🤖 AI: "Welcome to TVS support"
    ↓
👤 Customer: "9633717592" (provides phone)
    ↓
🤖 AI: "Let me retrieve your details..." ⏱️
    ↓
👤 Customer: "Where is my vehicle?"
    ↓
🤖 AI: "Your Apache RTR 310 is dispatched to Chennai dealership"
    ↓
👤 Customer: "When will it arrive?"
    ↓
🤖 AI: "Expected delivery by November 2, 2025"
    ↓
👤 Customer: "Thanks, bye"
    ↓
🤖 AI: "Thank you for choosing TVS. Goodbye!"
    ↓
📊 Call logged ✅
```

---

## ✨ Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Phone Verification** | Extract and verify 10-digit Indian phone numbers |
| **Vehicle Status** | Real-time lookup of vehicle manufacturing status |
| **Delivery Tracking** | Provide delivery dates, dealership info, and tracking updates |
| **Cancellation Processing** | Calculate refunds, determine charges based on order stage |
| **Smart Escalation** | Automatically route complex queries to support teams |
| **Conversation Memory** | Maintain context across multiple exchanges |
| **Multi-language** | Indian English with Polly voice synthesis |
| **Call Logging** | Complete audit trail of all interactions |
| **Error Recovery** | Graceful handling of misunderstood inputs |

### Advanced Features

- 🧠 **Intent Classification** - Hybrid AI + keyword matching
- 📊 **Real-time Database Queries** - PostgreSQL with LangChain SQL utilities
- 🔄 **Automatic Retry Logic** - Connection pooling and resilience
- 📱 **Natural Speech Recognition** - Twilio speech-to-text with hints
- 🔊 **Interactive Responses** - Loading messages, thinking pauses, natural flow
- 💾 **Persistent Storage** - All conversations stored for analytics

---

## 🏗️ Architecture

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────────┐
│                      CUSTOMER                                   │
│                   (Any Location)                                │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ 📞 Phone Call
                       ↓
        ┌──────────────────────────────┐
        │   TWILIO INFRASTRUCTURE      │
        │  • Call Routing              │
        │  • Speech-to-Text            │
        │  • Text-to-Speech (TTS)      │
        └──────────────┬───────────────┘
                       │
                       │ HTTPS (ngrok tunnel)
                       ↓
        ┌──────────────────────────────────────────┐
        │      FASTAPI SERVER (Port 8000)          │
        │  ┌────────────────────────────────────┐  │
        │  │ /voice - Initial greeting          │  │
        │  │ /get-phone-number - Verify phone   │  │
        │  │ /process-speech - Handle queries   │  │
        │  │ /call-status - Track completion    │  │
        │  └────────────────────────────────────┘  │
        └──────────┬──────────────────────────────┘
                   │
        ┌──────────┴──────────┬─────────────┐
        ↓                     ↓             ↓
    ┌─────────┐         ┌──────────┐   ┌──────────┐
    │ BUSINESS│         │ LANGCHAIN│   │DATABASE  │
    │ LOGIC   │         │ AGENT    │   │POSTGRES  │
    │         │         │          │   │          │
    │• Intent │         │• SQL     │   │• Bookings│
    │  Detect │         │  Queries │   │• Orders  │
    │• Response│        │• Results │   │• Users   │
    │  Gen    │         │  Parse   │   │• Calls   │
    └─────────┘         └──────────┘   └──────────┘
```

### Data Flow

```
Customer Input
    ↓
Speech-to-Text (Twilio)
    ↓
Extract Phone Number
    ↓
Store in Memory
    ↓
Classify Intent (If-Else + Optional AI)
    ↓
Query Database (LangChain SQL)
    ↓
Parse Results
    ↓
Generate Response (Business Logic)
    ↓
Save to Database
    ↓
Text-to-Speech (Polly)
    ↓
Send to Customer
    ↓
Listen for Next Input
    ↓
Repeat or End Call
```

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Voice API** | Twilio | Call handling, speech-to-text, text-to-speech |
| **Web Framework** | FastAPI | REST API server, webhooks |
| **Database** | PostgreSQL (Neon) | Store bookings, orders, conversations |
| **SQL AI** | LangChain | Intelligent SQL query generation |
| **LLM** | OpenAI GPT-3.5 | Optional: Smart intent classification |
| **TTS Voice** | Amazon Polly | Natural voice synthesis |
| **ORM** | SQLAlchemy | Database abstraction layer |
| **Deployment** | Uvicorn | ASGI server |
| **Tunneling** | ngrok | Local development webhook exposure |
| **Language** | Python 3.9+ | Backend programming |

---

## 📁 Project Structure

```
tvs-voice-agent/
│
├── main.py                      # FastAPI server & Twilio webhooks
├── business_logic.py            # Intent detection & response generation
├── langchain_agent.py           # SQL query execution & data retrieval
├── database.py                  # SQLAlchemy models & database functions
├── call_me.py                   # Test script to trigger calls
│
├── requirements.txt             # Python dependencies
├── .env                        # Environment variables (secrets)
├── .env.template               # Template for .env file
│
├── README.md                   # This file
├── SETUP_GUIDE.md              # Detailed setup instructions
├── SYSTEM_SUMMARY.md           # Complete system flow documentation
│
└── logs/
    └── calls.log               # Call logs (auto-generated)
```

---

## 💾 Database Schema

### Key Tables

```sql
-- Users (Customer Information)
users:
  id (UUID)
  full_name (VARCHAR)
  email (VARCHAR)
  phone_e164 (VARCHAR) ← Customer phone number

-- Bookings (BTO Vehicle Orders)
bookings:
  id (UUID)
  booking_public_id (VARCHAR)
  user_id (FK)
  vehicle_name (VARCHAR)
  order_status (ENUM)
  booking_date (TIMESTAMP)
  is_cancelled (BOOLEAN)

-- Orders (Manufacturing & Delivery)
orders:
  id (UUID)
  booking_id (FK)
  order_status (ENUM): order_received, order_confirmed, 
                        order_manufactured, order_packed,
                        order_dispatched, at_dealership
  payment_amount (NUMERIC)
  expected_delivery_date (TIMESTAMP)
  dealership_name (VARCHAR)

-- Call Logs (Interaction Records)
conversations:
  id (UUID)
  call_sid (VARCHAR) ← Twilio call ID
  customer_phone (VARCHAR)
  transcript (JSON)
  intent (VARCHAR)
  created_at (TIMESTAMP)
```

---

## 🚀 Installation

### Prerequisites

- Python 3.9 or higher
- PostgreSQL 12+ (or Neon cloud database)
- Twilio account with phone number
- OpenAI API key (for AI intent classification - optional)
- ngrok (for local testing)

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/tvs-voice-agent.git
cd tvs-voice-agent
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Setup Environment Variables

```bash
cp .env.template .env
# Edit .env with your credentials
```

See [Configuration](#configuration) section below.

---

## ⚙️ Configuration

### Create `.env` File

```bash
# ========== TWILIO CONFIGURATION ==========
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1-978-723-7477

# ========== YOUR PHONE NUMBER ==========
YOUR_PHONE_NUMBER=+919582350455

# ========== DATABASE CONFIGURATION ==========
# Option 1: Neon (Cloud PostgreSQL)
DATABASE_URL=postgresql://username:password@ep-xxxxx.us-east-1.aws.neon.tech/dbname?sslmode=require

# Option 2: Local PostgreSQL
# DATABASE_URL=postgresql://postgres:password@localhost:5432/tvs_bto

# ========== OPENAI CONFIGURATION ==========
OPENAI_API_KEY=sk-your-openai-key-here

# ========== NGROK CONFIGURATION ==========
# Get this after running: ngrok http 8000
NGROK_URL=https://abc123def456.ngrok.io

# ========== OPTIONAL ==========
ENVIRONMENT=development  # development, staging, production
DEBUG=True              # Enable debug logging
```

### Get Your Credentials

#### Twilio Setup
1. Go to [console.twilio.com](https://console.twilio.com)
2. Copy **Account SID** and **Auth Token**
3. Get a phone number or use existing one
4. Update `.env`

#### OpenAI Setup (Optional)
1. Go to [platform.openai.com](https://platform.openai.com/api-keys)
2. Create new API key
3. Add to `.env` as `OPENAI_API_KEY`

#### Database Setup
```bash
# Option A: Use Docker for PostgreSQL
docker run --name tvs_db \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=tvs_bto \
  -p 5432:5432 -d postgres:15

# Option B: Use Neon (Recommended for production)
# Sign up at: https://neon.tech
```

---

## 🏃 Running the Agent

### Terminal 1: Start ngrok (Tunnel)

```bash
ngrok http 8000
```

**Output:**
```
Forwarding                    https://abc123def456.ngrok.io -> http://localhost:8000
```

Copy the `https://abc123def456.ngrok.io` URL.

### Terminal 2: Update Twilio Webhook

1. Go to [console.twilio.com](https://console.twilio.com)
2. **Manage** → **Phone Numbers** → Select your number
3. Under **Voice & Fax**:
   - **A Call Comes In:** `https://abc123def456.ngrok.io/voice`
   - **Status Callbacks URL:** `https://abc123def456.ngrok.io/call-status`
4. Click **Save**

### Terminal 3: Start FastAPI Server

```bash
python main.py
```

**Expected Output:**
```
============================================================
🚀 TVS BTO AI VOICE AGENT STARTING
============================================================

✅ Database initialized!
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Terminal 4: Make a Test Call

```bash
python call_me.py call
```

**Your phone will ring!** Answer and follow the prompts.

---

## 📱 API Endpoints

### Voice Call Handling

#### `POST /voice`
**Incoming call webhook from Twilio**

Request (from Twilio):
```
From: +19787237477
CallSid: CAxxxxxxxxxxxx
```

Response:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Joanna">Hello! Welcome to TVS vehicle booking support.</Say>
  <Gather action="/get-phone-number" timeout="5" language="en-IN">
    <Say>Please provide your 10-digit mobile number.</Say>
  </Gather>
</Response>
```

---

#### `POST /get-phone-number`
**Process customer phone number**

Request (from Twilio):
```
SpeechResult: "963371 7592"
CallSid: CAxxxxxxxxxxxx
```

Response:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>Thank you! Let me retrieve your booking details.</Say>
  <Gather action="/process-speech" timeout="10" language="en-IN">
    <Say>How can I help you today?</Say>
  </Gather>
</Response>
```

---

#### `POST /process-speech`
**Process customer query and generate AI response**

Request (from Twilio):
```
SpeechResult: "Where is my vehicle?"
CallSid: CAxxxxxxxxxxxx
```

Processing:
1. Extract phone from session memory
2. Classify intent (status/delivery/cancel)
3. Query database
4. Generate response
5. Log conversation

Response:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>Your Apache RTR 310 is dispatched to Chennai dealership...</Say>
  <Gather action="/process-speech" timeout="10">
    <Say>Is there anything else?</Say>
  </Gather>
</Response>
```

---

#### `POST /call-status`
**Track call completion**

Request (from Twilio):
```
CallSid: CAxxxxxxxxxxxx
CallStatus: completed
```

Response:
```
OK
```

---

### Monitoring

#### `GET /`
Check if server is running

Response:
```json
{
  "status": "🤖 TVS BTO Voice Agent Running",
  "active_calls": 2
}
```

#### `GET /stats`
View active calls and statistics

Response:
```json
{
  "active_calls": 2,
  "details": [
    {
      "call_sid": "CAxxxx",
      "caller": "+19787237477",
      "customer_phone": "+919633717592",
      "messages": 4,
      "stage": "asking_help",
      "duration_seconds": 45
    }
  ]
}
```

---

## 💬 Usage Examples

### Example 1: Check Vehicle Status

```
🤖 Agent: "How can I help you?"

👤 Customer: "Where is my vehicle?"

🤖 Agent: "Your Apache RTR 310 is dispatched to S V AUTOMOTIVES 
          in Chennai. Expected delivery by November 2, 2025. 
          Is there anything else?"

👤 Customer: "No thanks"

🤖 Agent: "Thank you for choosing TVS. Goodbye!"
```

---

### Example 2: Check Delivery Details

```
🤖 Agent: "How can I help you?"

👤 Customer: "When will my bike be delivered?"

🤖 Agent: "Your Apache RTR 310 will arrive at S V AUTOMOTIVES 
          in Chennai. You'll receive an SMS with exact arrival date."

👤 Customer: "Great, thanks"

🤖 Agent: "Thank you for choosing TVS. Goodbye!"
```

---

### Example 3: Cancellation Request

```
🤖 Agent: "How can I help you?"

👤 Customer: "I want to cancel my booking"

🤖 Agent: "Your booking is at order confirmed stage. 
          A 25% cancellation charge of ₹12,500 applies. 
          Refund will be ₹37,500. Should I proceed?"

👤 Customer: "Yes"

🤖 Agent: "Great! Your cancellation is being processed. 
          You'll receive a confirmation SMS shortly."

👤 Customer: "Thank you"

🤖 Agent: "Thank you for choosing TVS. Goodbye!"
```

---

## 🔧 Troubleshooting

### Issue 1: Call Ends Immediately

**Problem:** Call hangs up right after phone verification.

**Solution:**
```python
# In main.py, check /get-phone-number endpoint
# Make sure Gather is properly appended:
gather = Gather(
    input='speech',
    action='/process-speech',
    method='POST',
    timeout=10,  # ← Increase timeout
    speech_timeout='5'
)
response.append(gather)  # ← Don't forget this!
```

---

### Issue 2: Database Connection Error

**Problem:** `SSL connection has been closed unexpectedly`

**Solution:**
```bash
# Update connection string
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require&connect_timeout=10

# Restart server
python main.py
```

---

### Issue 3: Twilio Webhook 502 Error

**Problem:** `Twilio was unable to fetch content from webhook`

**Solution:**
```python
# Ensure all responses have Content-Type
return Response(
    content=str(response),
    media_type="application/xml",  # ← Add this
    status_code=200
)
```

---

### Issue 4: Speech Not Recognized

**Problem:** Customer speech is not being understood.

**Solution:**
```python
# Add speech hints to Gather:
gather = Gather(
    input='speech',
    action='/process-speech',
    hints='status,delivery,cancel,when,where',  # ← Add hints
    language='en-IN'
)
```

---

## 📊 Monitoring & Logging

### View Call Logs

```bash
# Check terminal output
tail -f logs/calls.log

# Or query database
SELECT * FROM conversations 
ORDER BY created_at DESC 
LIMIT 10;
```

### Monitor Performance

```bash
# Check stats endpoint
curl http://localhost:8000/stats

# Monitor database connections
SELECT datname, usename, state, count(*) 
FROM pg_stat_activity 
GROUP BY datname, usename, state;
```

---

## 🚀 Deployment

### Deploy to Production

#### Option 1: Heroku

```bash
# Create Heroku app
heroku create tvs-voice-agent

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:standard-0

# Deploy
git push heroku main

# Set environment variables
heroku config:set TWILIO_ACCOUNT_SID=xxxxx
heroku config:set TWILIO_AUTH_TOKEN=xxxxx
# ... etc
```

#### Option 2: AWS Lambda

```bash
# Package application
pip install -r requirements.txt -t package/
cd package && zip -r ../deployment.zip . && cd ..
zip deployment.zip main.py business_logic.py langchain_agent.py database.py

# Upload to Lambda
aws lambda create-function --function-name tvs-voice-agent \
  --runtime python3.9 \
  --handler main.lambda_handler \
  --zip-file fileb://deployment.zip
```

#### Option 3: Docker

```bash
# Build image
docker build -t tvs-voice-agent .

# Run container
docker run -p 8000:8000 \
  -e TWILIO_ACCOUNT_SID=xxxxx \
  -e DATABASE_URL=xxxxx \
  tvs-voice-agent
```

---

## 📈 Metrics & KPIs

### Track These Metrics

```python
# In database or monitoring dashboard
- Total calls: COUNT(*)
- Successful resolutions: WHERE resolved=true
- Avg duration: AVG(duration)
- Resolution rate: (resolved / total) * 100
- Most common intent: SELECT intent, COUNT(*) GROUP BY intent
- Escalation rate: (escalated / total) * 100
```

---

## 🔮 Future Enhancements

- [ ] Multi-language support (Hindi, Tamil, Kannada)
- [ ] Outbound calls for delivery notifications
- [ ] WhatsApp integration
- [ ] SMS fallback for missed calls
- [ ] Sentiment analysis (detect angry customers)
- [ ] Payment processing integration
- [ ] Vehicle specifications lookup
- [ ] Test drive booking
- [ ] Warranty information
- [ ] Service center locator
- [ ] ML-based intent classification
- [ ] A/B testing of responses

---

## 📞 Support & Contact

For issues or questions:

- 📧 Email: support@tvs.com
- 📱 Phone: +91-XXXX-XXXX-XXXX
- 🐛 Report bugs: [GitHub Issues](https://github.com/tvs/voice-agent/issues)
- 💬 Discord: [Community](https://discord.gg/tvs)

---

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

---

## 🙏 Acknowledgments

- Twilio for voice infrastructure
- OpenAI for language models
- PostgreSQL for data storage
- LangChain for SQL intelligence
- FastAPI for web framework

---

**Made with ❤️ for TVS Customer Service**

Last Updated: October 26, 2025#
