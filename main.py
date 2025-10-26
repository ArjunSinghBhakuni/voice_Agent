"""
TVS BTO AI Voice Agent - Main FastAPI Server
Handles incoming calls, speech processing, and AI responses
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather
import openai
import os
from dotenv import load_dotenv
from datetime import datetime
import json

from business_logic import TVSBusinessLogic
from database import save_conversation, create_escalation, init_db

load_dotenv()

app = FastAPI()
business_logic = TVSBusinessLogic()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Store active conversations
conversations = {}

# Initialize DB on startup
@app.on_event("startup")
async def startup():
    init_db()
    print("✅ Database initialized!")


@app.post("/voice")
async def handle_incoming_call(request: Request):
    """Handle incoming Twilio call - Initial greeting"""
    
    form_data = await request.form()
    caller_number = form_data.get('From', 'Unknown')
    call_sid = form_data.get('CallSid')
    
    # Initialize conversation
    conversations[call_sid] = {
        'caller': caller_number,
        'customer_phone': None,  # Will be set after customer provides it
        'history': [],
        'start_time': datetime.now().isoformat(),
        'stage': 'phone_verification'  # Track conversation stage
    }
    
    print(f"📞 New call from: {caller_number} | SID: {call_sid}")
    
    response = VoiceResponse()
    
    # Greeting
    response.say(
        "Hello! Welcome to TVS vehicle booking support.",
        voice='Polly.Joanna',
        language='en-IN'
    )
    
    response.pause(length=1)
    
    # Ask for phone number
    gather = Gather(
        input='speech',
        action='/get-phone-number',
        method='POST',
        timeout=5,
        speech_timeout='3',
        language='en-IN'
    )
    
    gather.say(
        "To help you better, please provide your mobile number. Say your 10-digit number.",
        voice='Polly.Joanna'
    )
    response.append(gather)
    
    response.say("I didn't hear your number. Please call back. Goodbye!")
    
    return Response(content=str(response), media_type="application/xml")


@app.post("/get-phone-number")
async def get_phone_number(request: Request, SpeechResult: str = Form(None)):
    """Get customer's phone number"""
    
    form_data = await request.form()
    call_sid = form_data.get('CallSid')
    phone_speech = SpeechResult or ''
    
    print(f"🗣️ Customer said: {phone_speech}")
    
    response = VoiceResponse()
    
    if not phone_speech.strip():
        response.say("I'm sorry, I didn't catch your number. Please try again.", voice='Polly.Joanna')
        response.pause(length=1)
        gather = Gather(
            input='speech',
            action='/get-phone-number',
            method='POST',
            timeout=5,
            speech_timeout='3',
            language='en-IN'
        )
        gather.say("Please say your 10-digit mobile number.")
        response.append(gather)
        return Response(content=str(response), media_type="application/xml")
    
    # Extract phone number from speech
    customer_phone = extract_phone_number(phone_speech)
    
    if not customer_phone:
        response.say("I'm sorry, I couldn't understand the number. Let me try again.", voice='Polly.Joanna')
        response.pause(length=1)
        gather = Gather(
            input='speech',
            action='/get-phone-number',
            method='POST',
            timeout=5,
            speech_timeout='3',
            language='en-IN'
        )
        gather.say("Please say your 10-digit mobile number clearly.")
        response.append(gather)
        return Response(content=str(response), media_type="application/xml")
    
    # Format phone number
    if not customer_phone.startswith('+'):
        customer_phone = '+91' + customer_phone if len(customer_phone) == 10 else '+' + customer_phone
    
    print(f"✅ Customer phone: {customer_phone}")
    
    # Store in conversation
    if call_sid in conversations:
        conversations[call_sid]['customer_phone'] = customer_phone
        conversations[call_sid]['stage'] = 'asking_help'
        print(f"✅ Stored phone in conversation: {call_sid}")
    
    # IMPORTANT: Acknowledge and create pause
    response.say(
        f"Thank you! I have your number as {customer_phone}. Let me retrieve your booking details.",
        voice='Polly.Joanna',
        language='en-IN'
    )
    response.pause(length=2)
    
    # Create the Gather for next input - THIS IS KEY
    gather = Gather(
        num_digits=0,  # ← Accept any digits
        input='speech',
        action='/process-speech',
        method='POST',
        timeout=10,    # ← INCREASED from 6
        speech_timeout='5',  # ← INCREASED from 4
        language='en-IN',
        hints='status,delivery,cancel,where,when'
    )
    gather.say(
        "Now, how can I help you today? Ask about your vehicle status, delivery updates, or cancellation.",
        voice='Polly.Joanna'
    )
    response.append(gather)
    
    # Fallback if no speech heard
    response.say("I didn't hear your question. Please call back. Goodbye!", voice='Polly.Joanna')
    
    # IMPORTANT: Return with proper XML encoding
    return Response(
        content=str(response),
        media_type="application/xml",
        status_code=200
    )

@app.post("/process-speech")
async def process_speech(
    request: Request,
    SpeechResult: str = Form(None),
    Digits: str = Form(None),
    CallSid: str = Form(None)
):
    """Process customer speech using AI and business logic"""
    
    form_data = await request.form()
    call_sid = form_data.get('CallSid')
    user_speech = SpeechResult or ''
    
    print(f"🗣️ Customer: {user_speech}")
    print(f"⏱️ Processing speech...")
    
    response = VoiceResponse()
    
    # Validate session
    if call_sid not in conversations:
        print(f"❌ Session not found: {call_sid}")
        response.say("Session expired. Please call back.")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")
    
    customer_phone = conversations[call_sid].get('customer_phone')
    
    if not customer_phone:
        response.say("I need to verify your phone number first.")
        gather = Gather(
            input='speech',
            action='/get-phone-number',
            method='POST',
            timeout=5
        )
        gather.say("Please say your 10-digit mobile number.")
        response.append(gather)
        return Response(content=str(response), media_type="application/xml")
    
    if not user_speech.strip():
        response.say("I'm sorry, I didn't catch that. Please speak clearly.", voice='Polly.Joanna')
        response.pause(length=1)
        gather = Gather(
            input='speech',
            action='/process-speech',
            method='POST',
            timeout=10,
            speech_timeout='5',
            language='en-IN'
        )
        gather.say("What would you like to know?")
        response.append(gather)
        return Response(content=str(response), media_type="application/xml")
    
    # Get conversation history
    history = conversations[call_sid]['history']
    
    try:
        print(f"🤔 Generating response...")
        
        # Get AI response with timeout
        ai_response = business_logic.generate_response(
            phone_number=customer_phone,
            user_message=user_speech,
            call_sid=call_sid,
            conversation_history=history
        )
        
        print(f"🤖 Agent: {ai_response[:100]}...")  # Log first 100 chars
        
    except Exception as e:
        print(f"❌ Error generating response: {e}")
        ai_response = "I'm having trouble processing your request. Please try again."
    
    # Add to history
    history.append({"role": "user", "content": user_speech})
    history.append({"role": "assistant", "content": ai_response})
    
    # Save conversation
    try:
        save_or_update_conversation(
            call_sid=call_sid,
            phone=customer_phone,
            transcript={"messages": history},
            intent=business_logic.classify_intent(user_speech)
        )
    except Exception as e:
        print(f"⚠️ DB save error: {e}")
    
    # Speak response with pause
    response.pause(length=0.5)
    response.say(ai_response, voice='Polly.Joanna', language='en-IN')
    response.pause(length=0.5)
    
    # Check if should end call
    if should_end_call(user_speech):
        response.say("Thank you for choosing TVS. Goodbye!", voice='Polly.Joanna')
        response.hangup()
    else:
        # Continue conversation with proper Gather
        response.pause(length=1)
        gather = Gather(
            input='speech',
            action='/process-speech',
            method='POST',
            timeout=10,
            speech_timeout='5',
            language='en-IN',
            hints='delivery,status,cancel,when,where'
        )
        gather.say("Is there anything else I can help you with?", voice='Polly.Joanna')
        response.append(gather)
        
        # Fallback
        response.say("I didn't hear your response. Thank you for calling. Goodbye!", voice='Polly.Joanna')
    
    return Response(
        content=str(response),
        media_type="application/xml",
        status_code=200
    )

@app.post("/call-status")
async def call_status(request: Request):
    """Track call completion"""
    
    try:
        form_data = await request.form()
        call_sid = form_data.get('CallSid')
        status = form_data.get('CallStatus')
        
        print(f"📊 Call {call_sid} status: {status}")
        
        if status == 'completed' and call_sid in conversations:
            messages = len(conversations[call_sid]['history'])
            print(f"✅ Call ended. Total exchanges: {messages}")
            # Optional: Clean up conversation
            # del conversations[call_sid]
        
        # Return proper response with Content-Type
        return Response(
            content="OK",
            media_type="text/plain",
            status_code=200
        )
    
    except Exception as e:
        print(f"❌ Error in call_status: {e}")
        return Response(
            content="ERROR",
            media_type="text/plain",
            status_code=500
        )

@app.get("/")
async def root():
    return {
        "status": "🤖 TVS BTO Voice Agent Running",
        "active_calls": len(conversations)
    }


@app.get("/stats")
async def stats():
    return {
        "active_calls": len(conversations),
        "details": [
            {
                "call_sid": sid,
                "caller": conv['caller'],
                "customer_phone": conv.get('customer_phone'),
                "messages": len(conv['history']),
                "stage": conv.get('stage')
            }
            for sid, conv in conversations.items()
        ]
    }


def extract_phone_number(speech: str) -> str:
    """Extract phone number from speech"""
    
    # Remove spaces and common words
    speech = speech.lower().replace(" ", "").replace("nine", "9").replace("eight", "8").replace("seven", "7").replace("six", "6").replace("five", "5").replace("four", "4").replace("three", "3").replace("two", "2").replace("one", "1").replace("zero", "0").replace("oh", "0")
    
    # Extract only digits
    phone = ''.join(filter(str.isdigit, speech))
    
    # Validate length (10 digits for Indian numbers)
    if len(phone) == 10 or len(phone) == 12:
        return phone[-10:]  # Take last 10 digits
    
    return None


def save_or_update_conversation(call_sid: str, phone: str, transcript: dict, intent: str):
    """Save or update conversation (avoid duplicates)"""
    
    from database import SessionLocal, Conversation
    
    db = SessionLocal()
    try:
        # Check if conversation exists
        existing = db.query(Conversation).filter(Conversation.call_sid == call_sid).first()
        
        if existing:
            # Update existing
            existing.transcript = transcript
            existing.intent = intent
            db.commit()
            print(f"💾 Conversation updated: {call_sid}")
        else:
            # Insert new
            save_conversation(call_sid, phone, transcript, intent)
    finally:
        db.close()


def should_end_call(user_speech: str) -> bool:
    """Check if customer wants to end call"""
    
    end_phrases = ['goodbye', 'bye', 'thank you', 'thanks', 'that\'s all', 'nothing else']
    return any(phrase in user_speech.lower() for phrase in end_phrases)


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚀 TVS BTO AI VOICE AGENT STARTING")
    print("=" * 60)
    print("\n📍 Setup Instructions:")
    print("1. Run: ngrok http 8000")
    print("2. Update .env with ngrok URL")
    print("3. Set Twilio webhook to: https://your-ngrok-url/voice")
    print("\n🎯 Server: http://localhost:8000")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)