"""Parlant tools for healthcare assistant."""

from datetime import datetime


async def get_upcoming_slots(context: dict) -> dict:
    """Simulate fetching available appointment times."""
    # In real implementation, this would query a database or API
    return {
        "data": ["Monday 10 AM", "Tuesday 2 PM", "Wednesday 1 PM"],
        "status": "success",
    }


async def get_later_slots(context: dict) -> dict:
    """Simulate fetching later available appointment times."""
    # In real implementation, this would query a database or API
    return {
        "data": ["November 3, 11:30 AM", "November 12, 3 PM"],
        "status": "success",
    }


async def schedule_appointment(context: dict, appointment_datetime: str) -> dict:
    """Simulate scheduling an appointment."""
    # In real implementation, this would create an appointment in a database
    return {
        "data": f"Appointment scheduled for {appointment_datetime}",
        "status": "success",
    }


async def get_lab_results(context: dict) -> dict:
    """Simulate fetching lab results for a patient."""
    # In real implementation, this would query a database using customer_id from context
    customer_id = context.get("user_id", "unknown")
    
    # Mock lab results
    mock_results = {
        "report": "Complete Blood Count (CBC) - All values within normal range",
        "prognosis": "Normal",
    }
    
    return {
        "data": mock_results,
        "status": "success",
    }

