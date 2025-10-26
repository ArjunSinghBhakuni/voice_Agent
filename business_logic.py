"""
TVS BTO Business Logic - IMPROVED with better intent detection
"""

from langchain_agent import TVSBTOAgent
from database import save_conversation, create_escalation
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class TVSBusinessLogic:
    """Business logic handler for TVS BTO voice agent - IMPROVED"""
    
    def __init__(self):
        self.agent = TVSBTOAgent()
    
    def classify_intent(self, user_message: str) -> str:
        """Hybrid: Fast if-else + Smart AI fallback"""
        
        user_lower = user_message.lower()
        
        # FAST PATH: Keywords (99% of cases)
        if 'cancel' in user_lower or 'refund' in user_lower:
            return 'cancellation'
        
        if any(w in user_lower for w in ['delivery', 'when', 'arrive', 'dispatch', 'track']):
            return 'delivery'
        
        if any(w in user_lower for w in ['status', 'where', 'update', 'progress', 'vehicle', 'bike']):
            return 'status'
        
        # SLOW PATH: AI for edge cases (1% of cases)
        print(f"⚠️ Unclear intent, using AI: {user_message}")
        return self._classify_with_ai(user_message)

    def _classify_with_ai(self, user_message: str) -> str:
        """Use GPT-3.5 for unclear cases only"""
        
        try:
            import openai
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "Classify as: cancellation, delivery, or status. One word only."
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                temperature=0,
                max_tokens=5,
                timeout=2
            )
            
            result = response.choices[0].message.content.strip().lower()
            print(f"🤖 AI classified: {result}")
            
            for intent in ['cancellation', 'delivery', 'status']:
                if intent in result:
                    return intent
            
            return 'status'  # Default
        
        except Exception as e:
            print(f"⚠️ AI failed: {e}, defaulting to status")
            return 'status'
    
    def handle_status_check(self, phone_number: str) -> dict:
        """Handle vehicle status inquiry"""
        
        result = self.agent.get_booking_by_phone(phone_number)
        
        if not result['success']:
            return {
                "success": False,
                "message": "I couldn't find a booking under this phone number. Would you like to provide a different phone number or booking ID?"
            }
        
        booking_data = result.get('booking', {})
        vehicle_name = booking_data.get('vehicle_name', 'Your vehicle')
        order_status = booking_data.get('order_status', 'processing')
        status_message = self._map_order_status(order_status)
        color = booking_data.get('color', '')
        model = booking_data.get('model_variant', '')
        
        # Build rich response
        response = f"""Great! Your {color} {vehicle_name} {model} is {status_message}. 
        Your current status is {order_status.replace('_', ' ').title()}. 
        Would you like to know delivery details or anything else?"""
        
        return {
            "success": True,
            "message": response,
            "intent": "status",
            "data": booking_data
        }
    
    def handle_delivery_update(self, phone_number: str) -> dict:
        """Handle delivery/tracking inquiry"""
        
        result = self.agent.get_booking_by_phone(phone_number)
        
        if not result['success']:
            return {
                "success": False,
                "message": "I couldn't find your booking. Please verify your phone number."
            }
        
        booking_data = result.get('booking', {})
        dealership = booking_data.get('dealership_name', 'your dealership')
        city = booking_data.get('city', '')
        vehicle_name = booking_data.get('vehicle_name', 'Your vehicle')
        order_status = booking_data.get('order_status', '')
        
        # Smart response based on status
        if order_status == 'at_dealership':
            response = f"""{vehicle_name} has arrived at {dealership} in {city}. 
            It's ready for you to collect. Please visit the showroom during business hours."""
        elif order_status == 'order_dispatched':
            response = f"""{vehicle_name} is on the way to {dealership} in {city}. 
            You will receive an SMS with exact arrival date. Keep an eye on your inbox."""
        else:
            response = f"""{vehicle_name} will be delivered to {dealership} in {city}. 
            You'll get SMS updates as it progresses."""
        
        return {
            "success": True,
            "message": response,
            "intent": "delivery",
            "data": booking_data
        }
    
    def handle_cancellation_request(self, phone_number: str, call_sid: str) -> dict:
        """Handle cancellation request"""
        
        result = self.agent.get_cancellation_info(phone_number)
        
        if not result['success']:
            return {
                "success": False,
                "message": "I couldn't process your cancellation. Please contact support."
            }
        
        cancel_info = result.get('cancellation_info', {})
        booking_id = result.get('booking_id')
        charge_percent = cancel_info.get('fee_pct', 0)
        refund_amount = cancel_info.get('refund_amount', 0)
        fee_amount = cancel_info.get('fee_amount', 0)
        order_status = cancel_info.get('order_status', '')
        
        # Smart message based on charge
        if charge_percent == 0:
            response = f"""Good news! Your booking is in early stage. 
            You qualify for full refund of ₹{int(refund_amount)}. 
            Your cancellation will be processed within 5 business days."""
            action = "processed"
        
        elif charge_percent < 100:
            response = f"""Your booking is at {order_status.replace('_', ' ')} stage. 
            A {int(charge_percent)}% cancellation fee of ₹{int(fee_amount)} applies. 
            You'll receive ₹{int(refund_amount)} back. Should I proceed?"""
            action = "pending_confirmation"
        
        else:  # 100% charge
            response = f"""Unfortunately, your vehicle has already been dispatched. 
            Cancellation is not possible at this stage. 
            Would you like to know more about your delivery instead?"""
            action = "not_eligible"
        
        if action == "pending_confirmation":
            create_escalation(
                call_sid=call_sid,
                booking_id=booking_id,
                escalation_type="cancellation_request",
                description=f"Customer cancellation with {charge_percent}% charge",
                escalated_to="Finance Team"
            )
        
        return {
            "success": True,
            "message": response,
            "intent": "cancellation",
            "action": action,
            "cancellation_info": cancel_info
        }
    
    def handle_rejection(self, context: str) -> str:
        """Handle when customer says NO/DON'T WANT"""
        
        if 'cancellation' in context or 'cancel' in context:
            return "No problem! Your booking remains active. Is there anything else I can help you with?"
        
        return "Okay, no problem. Is there anything else I can help you with?"
    
    def handle_affirmation(self, context: str) -> str:
        """Handle when customer says YES/OKAY"""
        
        if 'cancellation' in context:
            return "Great! Your cancellation is being processed. You'll receive a confirmation SMS shortly."
        
        return "Perfect! I'm here to help. What would you like to know?"
    
    def should_escalate_to_human(self, user_message: str, conversation_history: list) -> bool:
        """IMPROVED: Only escalate for REAL complex issues, not casual NO"""
        
        user_lower = user_message.lower()
        
        # NEVER escalate for goodbye/thanks (fixed in generate_response)
        end_phrases = ['bye', 'goodbye', 'thank you', 'thanks', "that's all", 'nothing else']
        if any(phrase in user_lower for phrase in end_phrases):
            return False
        
        # NEVER escalate just because they said "no"
        if user_lower.strip() in ['no', 'nope', 'no thanks']:
            return False
        
        # Only escalate for EXPLICIT requests
        explicit_escalation = ['human', 'agent', 'manager', 'supervisor', 'speak to', 'connect me', 'call back']
        if any(word in user_lower for word in explicit_escalation):
            return True
        
        # Complex issues after multiple attempts
        if len(conversation_history) > 7:
            return True
        
        # Real problems
        problem_words = ['warranty', 'accident', 'damage', 'defect', 'broken', 'not working', 'issue', 'problem']
        if any(word in user_lower for word in problem_words):
            return True
        
        return False
    
    def generate_response(self, phone_number: str, user_message: str, call_sid: str, conversation_history: list) -> str:
        """IMPROVED: Better context-aware responses"""
        
        user_lower = user_message.lower()
        
        # FIRST: Check for end-of-call phrases
        end_phrases = ['bye', 'goodbye', 'thank you', 'thanks', "that's all", 'nothing else', 'no thanks']
        if any(phrase in user_lower for phrase in end_phrases):
            return "Thank you for choosing TVS. Goodbye!"
        
        # Classify intent
        intent = self.classify_intent(user_message)
        
        # HANDLE SPECIAL INTENTS FIRST
        if intent == 'reject_cancellation':
            return self.handle_rejection('cancellation')
        
        elif intent == 'negation':
            context = ' '.join([msg.get('content', '') for msg in conversation_history[-2:]])
            return self.handle_rejection(context)
        
        elif intent == 'affirmation':
            context = ' '.join([msg.get('content', '') for msg in conversation_history[-2:]])
            return self.handle_affirmation(context)
        
        # THEN: Check for escalation
        if self.should_escalate_to_human(user_message, conversation_history):
            create_escalation(
                call_sid=call_sid,
                booking_id="ESCALATED",
                escalation_type="explicit_request",
                description=user_message,
                escalated_to="Support Team"
            )
            return "I understand. Let me connect you to one of our support specialists right away."
        
        # HANDLE MAIN INTENTS
        if intent == 'status':
            result = self.handle_status_check(phone_number)
            return result['message']
        
        elif intent == 'delivery':
            result = self.handle_delivery_update(phone_number)
            return result['message']
        
        elif intent == 'cancellation':
            result = self.handle_cancellation_request(phone_number, call_sid)
            return result['message']
        
        elif intent == 'unknown':
            return "I'm sorry, I didn't quite understand. Could you please rephrase? You can ask about status, delivery, or cancellation."
        
        return "How can I help you with your vehicle booking?"
    
    def _map_order_status(self, order_status: str) -> str:
        """Convert order status to human-readable message"""
        
        status_map = {
            'order_received': 'received and being processed',
            'order_confirmed': 'confirmed and production will begin soon',
            'order_manufactured': 'manufactured and being prepared',
            'order_packed': 'packed and ready for dispatch',
            'order_dispatched': 'dispatched and on the way',
            'at_dealership': 'ready for collection at your dealership'
        }
        
        return status_map.get(order_status, 'being processed')
