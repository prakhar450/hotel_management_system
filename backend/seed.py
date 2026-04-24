"""
Seed the database with demo data.
Run: python seed.py  (from backend/ with venv active)
Safe to run multiple times — clears existing data first.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from datetime import date, datetime, time, timezone, timedelta
from app.database import SessionLocal, engine
from app.models import (
    Guest, Room, EventSpace, InventoryItem,
    Booking, Event, Invoice, Payment, Lead,
)
import uuid

TODAY = date.today()
NOW = datetime.now(timezone.utc)


def clear(db):
    for model in [Payment, Invoice, Booking, Event, Lead, Guest, Room, EventSpace, InventoryItem]:
        db.query(model).delete()
    db.commit()


def seed_rooms(db):
    rooms = [
        Room(room_number="101", type="single",  floor=1, base_rate=2500,  status="available", amenities={"ac": True, "wifi": True}),
        Room(room_number="102", type="single",  floor=1, base_rate=2500,  status="available", amenities={"ac": True, "wifi": True}),
        Room(room_number="201", type="double",  floor=2, base_rate=4000,  status="available", amenities={"ac": True, "wifi": True, "tv": True}),
        Room(room_number="202", type="double",  floor=2, base_rate=4000,  status="occupied",  amenities={"ac": True, "wifi": True, "tv": True}),
        Room(room_number="203", type="double",  floor=2, base_rate=4000,  status="available", amenities={"ac": True, "wifi": True, "tv": True}),
        Room(room_number="301", type="deluxe",  floor=3, base_rate=6500,  status="available", amenities={"ac": True, "wifi": True, "tv": True, "bathtub": True}),
        Room(room_number="302", type="deluxe",  floor=3, base_rate=6500,  status="available", amenities={"ac": True, "wifi": True, "tv": True, "bathtub": True}),
        Room(room_number="401", type="suite",   floor=4, base_rate=12000, status="available", amenities={"ac": True, "wifi": True, "tv": True, "bathtub": True, "kitchenette": True}),
        Room(room_number="402", type="suite",   floor=4, base_rate=12000, status="maintenance", amenities={"ac": True, "wifi": True}),
        Room(room_number="501", type="suite",   floor=5, base_rate=15000, status="available", amenities={"ac": True, "wifi": True, "tv": True, "bathtub": True, "kitchenette": True, "balcony": True}),
    ]
    db.add_all(rooms)
    db.flush()
    return rooms


def seed_spaces(db):
    spaces = [
        EventSpace(name="Grand Ballroom", type="hall",    capacity=500, base_rate_per_day=150000, base_rate_per_slot=80000, setup_time_hours=4, teardown_time_hours=3, amenities={"ac": True, "stage": True, "av": True, "catering_kitchen": True}),
        EventSpace(name="Lawn A",         type="lawn",    capacity=300, base_rate_per_day=80000,  base_rate_per_slot=45000, setup_time_hours=3, teardown_time_hours=2, amenities={"lighting": True, "generator": True}),
        EventSpace(name="Rooftop Terrace",type="terrace", capacity=100, base_rate_per_day=40000,  base_rate_per_slot=25000, setup_time_hours=2, teardown_time_hours=1, amenities={"ac": False, "view": True, "bar_counter": True}),
    ]
    db.add_all(spaces)
    db.flush()
    return spaces


def seed_inventory(db):
    items = [
        InventoryItem(name="Banquet Chairs",    category="furniture", total_quantity=500, available_quantity=500, low_stock_threshold=50,  unit="pcs"),
        InventoryItem(name="Round Tables (6ft)", category="furniture", total_quantity=80,  available_quantity=80,  low_stock_threshold=10,  unit="pcs"),
        InventoryItem(name="Rectangular Tables", category="furniture", total_quantity=40,  available_quantity=40,  low_stock_threshold=5,   unit="pcs"),
        InventoryItem(name="White Chair Covers", category="linen",     total_quantity=500, available_quantity=500, low_stock_threshold=50,  unit="pcs"),
        InventoryItem(name="Table Cloths",       category="linen",     total_quantity=100, available_quantity=100, low_stock_threshold=15,  unit="pcs"),
        InventoryItem(name="Dinner Plates",      category="crockery",  total_quantity=600, available_quantity=600, low_stock_threshold=60,  unit="pcs"),
        InventoryItem(name="Dessert Plates",     category="crockery",  total_quantity=400, available_quantity=400, low_stock_threshold=40,  unit="pcs"),
        InventoryItem(name="Wine Glasses",       category="crockery",  total_quantity=400, available_quantity=400, low_stock_threshold=40,  unit="pcs"),
        InventoryItem(name="Water Glasses",      category="crockery",  total_quantity=600, available_quantity=600, low_stock_threshold=60,  unit="pcs"),
        InventoryItem(name="Projector (4K)",     category="av",        total_quantity=3,   available_quantity=3,   low_stock_threshold=1,   unit="units"),
        InventoryItem(name="Wireless Mic",       category="av",        total_quantity=8,   available_quantity=8,   low_stock_threshold=2,   unit="units"),
        InventoryItem(name="LED Stage Lights",   category="av",        total_quantity=20,  available_quantity=20,  low_stock_threshold=5,   unit="units"),
        InventoryItem(name="Flower Vases",       category="decor",     total_quantity=60,  available_quantity=60,  low_stock_threshold=10,  unit="pcs"),
        InventoryItem(name="Fairy Light Strings",category="decor",     total_quantity=50,  available_quantity=50,  low_stock_threshold=5,   unit="rolls"),
        InventoryItem(name="Extension Cords",    category="other",     total_quantity=30,  available_quantity=30,  low_stock_threshold=5,   unit="pcs"),
        InventoryItem(name="Portable Fans",      category="other",     total_quantity=15,  available_quantity=15,  low_stock_threshold=3,   unit="units"),
        InventoryItem(name="Candles",            category="decor",     total_quantity=200, available_quantity=12,  low_stock_threshold=30,  unit="pcs"),  # low stock!
        InventoryItem(name="Napkins (cloth)",    category="linen",     total_quantity=800, available_quantity=800, low_stock_threshold=100, unit="pcs"),
        InventoryItem(name="Serving Trays",      category="crockery",  total_quantity=40,  available_quantity=40,  low_stock_threshold=5,   unit="pcs"),
        InventoryItem(name="Podium",             category="furniture", total_quantity=2,   available_quantity=2,   low_stock_threshold=1,   unit="units"),
    ]
    db.add_all(items)
    db.flush()
    return items


def seed_guests(db):
    guests = [
        Guest(id=uuid.uuid4(), name="Rajesh Sharma",   phone="9810012345", email="rajesh@example.com",  nationality="Indian", id_type="aadhaar"),
        Guest(id=uuid.uuid4(), name="Priya Mehta",     phone="9820023456", email="priya@example.com",   nationality="Indian", id_type="passport"),
        Guest(id=uuid.uuid4(), name="Amit Gupta",      phone="9830034567", email="amit@example.com",    nationality="Indian", id_type="aadhaar"),
        Guest(id=uuid.uuid4(), name="Sunita Verma",    phone="9840045678", email="sunita@example.com",  nationality="Indian", id_type="dl"),
        Guest(id=uuid.uuid4(), name="Rohit Kapoor",    phone="9850056789", email="rohit@example.com",   nationality="Indian", id_type="aadhaar"),
    ]
    db.add_all(guests)
    db.flush()
    return guests


def seed_bookings(db, guests, rooms):
    room_map = {r.room_number: r for r in rooms}
    bookings = [
        Booking(
            id=uuid.uuid4(), guest_id=guests[0].id, room_id=room_map["201"].id,
            check_in=TODAY, check_out=TODAY + timedelta(days=2),
            status="checked_in", adults=2, source="phone",
            created_at=NOW, updated_at=NOW,
            actual_checkin=NOW,
        ),
        Booking(
            id=uuid.uuid4(), guest_id=guests[1].id, room_id=room_map["301"].id,
            check_in=TODAY + timedelta(days=1), check_out=TODAY + timedelta(days=4),
            status="confirmed", adults=2, children=1, source="online",
            created_at=NOW, updated_at=NOW,
        ),
        Booking(
            id=uuid.uuid4(), guest_id=guests[2].id, room_id=room_map["101"].id,
            check_in=TODAY + timedelta(days=3), check_out=TODAY + timedelta(days=5),
            status="confirmed", adults=1, source="walk_in",
            created_at=NOW, updated_at=NOW,
        ),
        Booking(
            id=uuid.uuid4(), guest_id=guests[3].id, room_id=room_map["401"].id,
            check_in=TODAY + timedelta(days=7), check_out=TODAY + timedelta(days=10),
            status="confirmed", adults=2, source="agent",
            special_requests="Late check-in after 10 PM", created_at=NOW, updated_at=NOW,
        ),
        Booking(
            id=uuid.uuid4(), guest_id=guests[4].id, room_id=room_map["501"].id,
            check_in=TODAY + timedelta(days=14), check_out=TODAY + timedelta(days=17),
            status="confirmed", adults=2, source="phone",
            created_at=NOW, updated_at=NOW,
        ),
    ]
    db.add_all(bookings)
    db.flush()
    return bookings


def seed_events(db, guests, spaces):
    space_map = {s.name: s for s in spaces}
    events = [
        Event(
            id=uuid.uuid4(), name="Sharma–Mehta Wedding", event_type="wedding",
            guest_id=guests[0].id, space_id=space_map["Grand Ballroom"].id,
            event_date=TODAY + timedelta(days=10),
            start_time=time(18, 0), end_time=time(23, 59),
            guest_count=400, status="confirmed",
            special_requirements="Vegetarian menu only. Flower décor in white and gold.",
            created_at=NOW, updated_at=NOW,
        ),
        Event(
            id=uuid.uuid4(), name="TechCorp Annual Meet", event_type="corporate",
            guest_id=guests[2].id, space_id=space_map["Rooftop Terrace"].id,
            event_date=TODAY + timedelta(days=5),
            start_time=time(9, 0), end_time=time(18, 0),
            guest_count=80, status="confirmed",
            created_at=NOW, updated_at=NOW,
        ),
    ]
    db.add_all(events)
    db.flush()
    return events


def seed_invoices(db, bookings, events):
    from app.utils.invoice_number import next_invoice_number

    invoices = []
    for booking in bookings:
        nights = (booking.check_out - booking.check_in).days
        rate = 4000  # simplified for seed
        subtotal = nights * rate
        tax = round(subtotal * 0.18, 2)
        inv = Invoice(
            id=uuid.uuid4(),
            invoice_number=next_invoice_number(db),
            booking_id=booking.id,
            subtotal=subtotal,
            tax_amount=tax,
            total_amount=subtotal + tax,
            status="sent",
            due_date=booking.check_out,
            line_items=[{"description": f"Room stay ({nights} nights)", "amount": subtotal}],
            created_at=NOW, updated_at=NOW,
        )
        db.add(inv)
        db.flush()  # flush each one so next_invoice_number sees it
        invoices.append(inv)
    return invoices


def seed_leads(db):
    leads = [
        Lead(id=uuid.uuid4(), name="Vikram Nair",    phone="9860067890", email="vikram@example.com",  event_type="wedding",   guest_count=250, budget_range="5-8L",  status="quoted",    source="instagram", created_at=NOW, updated_at=NOW),
        Lead(id=uuid.uuid4(), name="Deepa Krishnan", phone="9870078901", email="deepa@example.com",   event_type="birthday",  guest_count=80,  budget_range="1-2L",  status="contacted", source="referral",  created_at=NOW, updated_at=NOW),
        Lead(id=uuid.uuid4(), name="Sanjay Patel",   phone="9880089012", email="sanjay@example.com",  event_type="corporate", guest_count=150, budget_range="3-5L",  status="new",       source="website",   created_at=NOW, updated_at=NOW),
    ]
    db.add_all(leads)
    db.flush()
    return leads


def main():
    db = SessionLocal()
    try:
        print("Clearing existing data...")
        clear(db)

        print("Seeding rooms...")
        rooms = seed_rooms(db)

        print("Seeding event spaces...")
        spaces = seed_spaces(db)

        print("Seeding inventory...")
        seed_inventory(db)

        print("Seeding guests...")
        guests = seed_guests(db)

        print("Seeding bookings...")
        bookings = seed_bookings(db, guests, rooms)

        print("Seeding events...")
        seed_events(db, guests, spaces)

        print("Seeding invoices...")
        seed_invoices(db, bookings, [])

        print("Seeding leads...")
        seed_leads(db)

        db.commit()
        print("\nSeed complete.")
        print(f"  Rooms: {len(rooms)} | Spaces: 3 | Inventory: 20 items")
        print(f"  Guests: {len(guests)} | Bookings: {len(bookings)} | Events: 2 | Leads: 3")
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
