"""
SQLAlchemy Agent for TVS BTO using Real Database Schema
Direct SQL queries without LangChain complications
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import Pool

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/tvs_bto"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class TVSBTOAgent:
    """Agent for TVS BTO queries using real schema"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    
    def get_booking_by_phone(self, phone_number: str) -> dict:
        """Get booking info by customer phone number"""
        
        try:
            db = SessionLocal()
            
            # Query using the booking_summary view or direct query
            query = text("""
                SELECT
                    b.id,
                    b.booking_public_id,
                    u.full_name,
                    u.phone_e164,
                    b.vehicle_name,
                    b.model_variant,
                    b.color,
                    b.booking_status,
                    b.order_status,
                    b.is_cancelled,
                    d.name as dealership_name,
                    d.city,
                    b.booking_date,
                    b.order_received_at
                FROM bookings b
                LEFT JOIN users u ON u.id = b.user_id
                LEFT JOIN dealerships d ON d.id = b.dealership_id
                WHERE u.phone_e164 = :phone
                AND b.is_cancelled = false
                ORDER BY b.booking_date DESC
                LIMIT 1
            """)
            
            result = db.execute(query, {"phone": phone_number}).fetchone()
            
            if not result:
                db.close()
                return {"success": False, "error": "Booking not found"}
            
            # Convert row to dict
            booking_data = {
                'id': result[0],
                'booking_id': result[1],
                'customer_name': result[2],
                'customer_phone': result[3],
                'vehicle_name': result[4],
                'model_variant': result[5],
                'color': result[6],
                'booking_status': result[7],
                'order_status': result[8],
                'is_cancelled': result[9],
                'dealership_name': result[10],
                'city': result[11],
                'booking_date': str(result[12]) if result[12] else None,
                'order_received_at': str(result[13]) if result[13] else None
            }
            
            db.close()
            print(f"✅ Found booking: {booking_data['booking_id']}")
            
            return {
                "success": True,
                "booking": booking_data,
                "booking_id": result[1]
            }
        
        except Exception as e:
            print(f"❌ Query error: {e}")
            try:
                db.close()
            except:
                pass
            return {"success": False, "error": str(e)}
    
    
    def get_cancellation_info(self, phone_number: str) -> dict:
        """Get cancellation eligibility and charges"""
        
        try:
            db = SessionLocal()
            
            # Get booking and cancellation info
            query = text("""
                SELECT
                    b.id,
                    b.booking_public_id,
                    b.order_status,
                    b.booking_date,
                    COALESCE(c.fee_pct, 0) as fee_pct,
                    COALESCE(c.fee_amount, 0) as fee_amount,
                    COALESCE(c.refund_amount, 0) as refund_amount
                FROM bookings b
                LEFT JOIN users u ON u.id = b.user_id
                LEFT JOIN cancellations c ON c.booking_id = b.id
                WHERE u.phone_e164 = :phone
                AND b.is_cancelled = false
                ORDER BY b.booking_date DESC
                LIMIT 1
            """)
            
            result = db.execute(query, {"phone": phone_number}).fetchone()
            db.close()
            
            if not result:
                return {"success": False, "error": "Booking not found"}
            
            # If no cancellation exists, calculate charges based on order_status
            booking_id = result[1]
            order_status = result[2]
            fee_pct = result[4]
            
            if fee_pct == 0:
                # Calculate based on order status
                charge_map = {
                    'order_received': 0,
                    'order_confirmed': 25,
                    'order_manufactured': 50,
                    'order_packed': 75,
                    'order_dispatched': 100,
                    'at_dealership': 100
                }
                fee_pct = charge_map.get(order_status, 0)
            
            # Assume 50000 as base amount (you can fetch from invoices table if available)
            base_amount = 50000
            fee_amount = base_amount * (fee_pct / 100)
            refund_amount = base_amount - fee_amount
            
            cancel_info = {
                'booking_id': booking_id,
                'order_status': order_status,
                'fee_pct': fee_pct,
                'fee_amount': fee_amount,
                'refund_amount': refund_amount
            }
            
            print(f"✅ Cancellation info: {fee_pct}% charge, ₹{refund_amount} refund")
            
            return {
                "success": True,
                "booking_id": booking_id,
                "cancellation_info": cancel_info
            }
        
        except Exception as e:
            print(f"❌ Cancellation query error: {e}")
            return {"success": False, "error": str(e)}
    
    
    def get_order_history(self, phone_number: str) -> dict:
        """Get order status timeline"""
        
        try:
            db = SessionLocal()
            
            # Get order history
            query = text("""
                SELECT
                    osh.status,
                    osh.updated_on,
                    osh.comment
                FROM order_status_history osh
                JOIN bookings b ON b.id = osh.booking_id
                JOIN users u ON u.id = b.user_id
                WHERE u.phone_e164 = :phone
                ORDER BY osh.updated_on DESC
                LIMIT 10
            """)
            
            results = db.execute(query, {"phone": phone_number}).fetchall()
            db.close()
            
            history = [
                {
                    'status': row[0],
                    'timestamp': str(row[1]),
                    'comment': row[2]
                }
                for row in results
            ]
            
            return {
                "success": True,
                "history": history
            }
        
        except Exception as e:
            print(f"❌ History query error: {e}")
            return {"success": False, "error": str(e)}
    
    
    def log_call(self, phone_number: str, intent: str, outcome: str, call_id: str = None) -> dict:
        """Log call interaction"""
        
        try:
            db = SessionLocal()
            
            # Get user and booking
            user_query = text("SELECT id FROM users WHERE phone_e164 = :phone LIMIT 1")
            user_result = db.execute(user_query, {"phone": phone_number}).fetchone()
            
            if not user_result:
                db.close()
                return {"success": False, "error": "User not found"}
            
            user_id = user_result[0]
            
            # Get booking
            booking_query = text("""
                SELECT id FROM bookings 
                WHERE user_id = :user_id 
                AND is_cancelled = false
                ORDER BY booking_date DESC
                LIMIT 1
            """)
            booking_result = db.execute(booking_query, {"user_id": user_id}).fetchone()
            booking_id = booking_result[0] if booking_result else None
            
            # Insert call log
            insert_query = text("""
                INSERT INTO call_logs (call_id, booking_id, user_id, from_number, intent, outcome, started_at)
                VALUES (:call_id, :booking_id, :user_id, :phone, :intent, :outcome, NOW())
                RETURNING id
            """)
            
            db.execute(insert_query, {
                'call_id': call_id,
                'booking_id': booking_id,
                'user_id': user_id,
                'phone': phone_number,
                'intent': intent,
                'outcome': outcome
            })
            db.commit()
            db.close()
            
            print(f"✅ Call logged: {intent} - {outcome}")
            return {"success": True}
        
        except Exception as e:
            print(f"❌ Call logging error: {e}")
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    agent = TVSBTOAgent()
    
    # Test queries
    print("Testing with sample phone numbers...")
    
    result = agent.get_booking_by_phone("+919633717592")
    print(f"Booking: {result}")
    
    result = agent.get_cancellation_info("+919633717592")
    print(f"Cancellation: {result}")
    
    result = agent.get_order_history("+919633717592")
    print(f"History: {result}")