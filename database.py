"""
PostgreSQL Database Models for TVS BTO Voice Agent
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://neondb_owner:npg_ryB1npPiv8bo@ep-noisy-morning-a4wbxrmk-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# ========== DATABASE MODELS ==========

class Customer(Base):
    """Customer information"""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True)
    phone_number = Column(String(15), unique=True, index=True)
    name = Column(String(100))
    email = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)


class Booking(Base):
    """Booking Service data"""
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True)
    booking_id = Column(String(50), unique=True, index=True)
    customer_phone = Column(String(15), index=True)
    customer_name = Column(String(100))
    vehicle_model = Column(String(100))
    booking_status = Column(String(50))  # pending, confirmed, cancelled
    booking_date = Column(DateTime)
    cancellation_date = Column(DateTime, nullable=True)
    cancellation_charge_percent = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Order(Base):
    """SAP & DMS Order data"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(String(50), unique=True, index=True)
    booking_id = Column(String(50), index=True)
    order_status = Column(String(50))  # order_received, order_confirmed, order_manufactured, order_packed, order_dispatched
    payment_status = Column(String(50))  # pending, completed, refunded
    payment_amount = Column(Float)
    invoice_number = Column(String(50), nullable=True)
    production_started = Column(DateTime, nullable=True)
    manufactured_date = Column(DateTime, nullable=True)
    packed_date = Column(DateTime, nullable=True)
    dispatched_date = Column(DateTime, nullable=True)
    expected_delivery_date = Column(DateTime, nullable=True)
    dealership_name = Column(String(200), nullable=True)
    dealership_location = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Conversation(Base):
    """Call logs and transcripts"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True)
    call_sid = Column(String(100), unique=True, index=True)
    customer_phone = Column(String(15), index=True)
    call_start = Column(DateTime, default=datetime.now)
    call_end = Column(DateTime, nullable=True)
    call_duration = Column(Integer, nullable=True)
    transcript = Column(JSON)
    intent = Column(String(50))
    resolved = Column(Boolean, default=False)
    escalated = Column(Boolean, default=False)
    escalated_to = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class Escalation(Base):
    """Escalation tracking"""
    __tablename__ = "escalations"
    
    id = Column(Integer, primary_key=True)
    call_sid = Column(String(100), index=True)
    booking_id = Column(String(50), index=True)
    escalation_type = Column(String(50))  # production_delay, cancellation_request, complex_query
    escalated_to = Column(String(100))
    description = Column(Text)
    status = Column(String(50), default="open")  # open, in_progress, resolved
    created_at = Column(DateTime, default=datetime.now)
    resolved_at = Column(DateTime, nullable=True)


# ========== DATABASE FUNCTIONS ==========

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created!")


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_customer_by_phone(phone: str):
    """Find customer by phone number"""
    db = SessionLocal()
    try:
        return db.query(Customer).filter(Customer.phone_number == phone).first()
    finally:
        db.close()


def get_booking_by_phone(phone: str):
    """Find booking by customer phone"""
    db = SessionLocal()
    try:
        return db.query(Booking).filter(Booking.customer_phone == phone).first()
    finally:
        db.close()


def get_order_by_booking_id(booking_id: str):
    """Get order details by booking ID"""
    db = SessionLocal()
    try:
        return db.query(Order).filter(Order.booking_id == booking_id).first()
    finally:
        db.close()


def save_conversation(call_sid: str, phone: str, transcript: dict, intent: str):
    """Save conversation to database (insert only)"""
    db = SessionLocal()
    try:
        # Check if already exists
        existing = db.query(Conversation).filter(Conversation.call_sid == call_sid).first()
        if existing:
            print(f"⚠️ Conversation already exists: {call_sid}")
            return existing
        
        conversation = Conversation(
            call_sid=call_sid,
            customer_phone=phone,
            transcript=transcript,
            intent=intent
        )
        db.add(conversation)
        db.commit()
        print(f"💾 Conversation saved: {call_sid}")
        return conversation
    except Exception as e:
        print(f"❌ Save error: {e}")
        db.rollback()
        return None
    finally:
        db.close()


def create_escalation(call_sid: str, booking_id: str, escalation_type: str, description: str, escalated_to: str):
    """Create escalation record"""
    db = SessionLocal()
    try:
        escalation = Escalation(
            call_sid=call_sid,
            booking_id=booking_id,
            escalation_type=escalation_type,
            escalated_to=escalated_to,
            description=description
        )
        db.add(escalation)
        db.commit()
        print(f"⚠️ Escalation created: {escalation_type}")
        return escalation
    finally:
        db.close()


def seed_sample_data():
    """Add sample data for testing"""
    db = SessionLocal()
    try:
        # Sample customer
        customer = Customer(
            phone_number="+919582350455",
            name="Rahul Kumar",
            email="rahul@example.com"
        )
        db.add(customer)
        
        # Sample booking
        booking = Booking(
            booking_id="BTO2025001",
            customer_phone="+919582350455",
            customer_name="Rahul Kumar",
            vehicle_model="TVS Apache RTR 160",
            booking_status="confirmed",
            booking_date=datetime(2025, 10, 1)
        )
        db.add(booking)
        
        # Sample order
        order = Order(
            order_id="ORD2025001",
            booking_id="BTO2025001",
            order_status="order_manufactured",
            payment_status="completed",
            payment_amount=50000.0,
            invoice_number="INV2025001",
            production_started=datetime(2025, 10, 5),
            manufactured_date=datetime(2025, 10, 20),
            expected_delivery_date=datetime(2025, 11, 2),
            dealership_name="TVS Showroom Delhi",
            dealership_location="Connaught Place, New Delhi"
        )
        db.add(order)
        
        db.commit()
        print("✅ Sample data added!")
        
    except Exception as e:
        print(f"⚠️ Sample data error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE SETUP")
    print("=" * 60)
    init_db()
    seed_sample_data()
    print("✅ Database ready!")
    print("=" * 60)