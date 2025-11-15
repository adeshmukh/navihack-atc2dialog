"""Healthcare agent implementation using Parlant framework."""

import logging

logger = logging.getLogger(__name__)


async def handle_message(user_message: str, context: dict) -> str:
    """
    Handle user messages for healthcare assistant.
    
    This is a simplified implementation inspired by Parlant's healthcare example.
    In a full implementation, this would integrate with Parlant's server and journeys.
    """
    message_lower = user_message.lower().strip()
    
    # Journey 1: Schedule Appointment
    if any(
        keyword in message_lower
        for keyword in ["schedule", "appointment", "book", "appointment time"]
    ):
        return await _handle_scheduling(user_message, context)
    
    # Journey 2: Lab Results
    if any(
        keyword in message_lower
        for keyword in ["lab results", "test results", "lab report", "results"]
    ):
        return await _handle_lab_results(user_message, context)
    
    # Global guidelines
    if "insurance" in message_lower:
        return (
            "We accept most major insurance providers including Blue Cross Blue Shield, "
            "Aetna, and UnitedHealthcare. For specific coverage details, please call our "
            "office at +1-234-567-8900 during office hours (Monday to Friday, 9 AM to 5 PM)."
        )
    
    if any(keyword in message_lower for keyword in ["human", "agent", "speak to", "talk to"]):
        return (
            "I understand you'd like to speak with someone. Please call our office "
            "at +1-234-567-8900 during office hours (Monday to Friday, 9 AM to 5 PM), "
            "and our staff will be happy to assist you."
        )
    
    if "urgent" in message_lower or "emergency" in message_lower:
        return (
            "If this is a medical emergency, please call 911 immediately. "
            "For urgent matters, please call our office at +1-234-567-8900 right away."
        )
    
    # Default empathetic response
    return (
        "I'm here to help you with scheduling appointments or retrieving lab results. "
        "How can I assist you today? You can say things like 'I need to schedule an appointment' "
        "or 'Did my lab results come in?'"
    )


async def _handle_scheduling(user_message: str, context: dict) -> str:
    """Handle appointment scheduling journey."""
    from .tools import get_upcoming_slots, get_later_slots, schedule_appointment
    
    message_lower = user_message.lower()
    
    # Get or initialize scheduling state in session
    import chainlit as cl
    scheduling_state = cl.user_session.get("healthcare_scheduling_state", {})
    
    # Determine reason for visit
    if "reason" not in scheduling_state:
        scheduling_state["reason"] = "general"
        cl.user_session.set("healthcare_scheduling_state", scheduling_state)
        return (
            "I'd be happy to help you schedule an appointment. "
            "What is the reason for your visit?"
        )
    
    # Get available slots
    if "slots_shown" not in scheduling_state:
        slots_result = await get_upcoming_slots(context)
        slots = slots_result.get("data", [])
        scheduling_state["slots_shown"] = True
        scheduling_state["upcoming_slots"] = slots
        cl.user_session.set("healthcare_scheduling_state", scheduling_state)
        
        slots_text = "\n".join(f"- {slot}" for slot in slots)
        return (
            f"Here are some available appointment times:\n{slots_text}\n\n"
            "Which time works best for you?"
        )
    
    # Check if user picked a time
    upcoming_slots = scheduling_state.get("upcoming_slots", [])
    picked_slot = None
    for slot in upcoming_slots:
        if any(word in message_lower for word in slot.lower().split()):
            picked_slot = slot
            break
    
    if picked_slot:
        scheduling_state["selected_slot"] = picked_slot
        cl.user_session.set("healthcare_scheduling_state", scheduling_state)
        return (
            f"I have {picked_slot} available. Would you like me to confirm this appointment?"
        )
    
    # Check if user wants to confirm
    if "selected_slot" in scheduling_state and any(
        word in message_lower for word in ["yes", "confirm", "sounds good", "ok"]
    ):
        selected = scheduling_state["selected_slot"]
        result = await schedule_appointment(context, selected)
        cl.user_session.set("healthcare_scheduling_state", {})  # Reset
        return result.get("data", f"Appointment scheduled for {selected}")
    
    # Check if none of the times work
    if any(word in message_lower for word in ["none", "don't work", "not available"]):
        later_result = await get_later_slots(context)
        later_slots = later_result.get("data", [])
        scheduling_state["later_slots_shown"] = True
        cl.user_session.set("healthcare_scheduling_state", scheduling_state)
        
        slots_text = "\n".join(f"- {slot}" for slot in later_slots)
        return (
            f"I understand. Here are some later available times:\n{slots_text}\n\n"
            "Do any of these work for you?"
        )
    
    # If still no match, ask to call office
    if scheduling_state.get("later_slots_shown"):
        return (
            "I understand those times don't work either. Please call our office "
            "at +1-234-567-8900 to speak with our scheduling team, and they'll "
            "help you find a time that works."
        )
    
    return "I'm here to help you schedule an appointment. Which time works best for you?"


async def _handle_lab_results(user_message: str, context: dict) -> str:
    """Handle lab results retrieval journey."""
    from .tools import get_lab_results
    
    result = await get_lab_results(context)
    lab_data = result.get("data", {})
    
    if isinstance(lab_data, dict):
        report = lab_data.get("report", "No report available")
        prognosis = lab_data.get("prognosis", "Unknown")
        
        if prognosis.lower() in ["normal", "good", "healthy"]:
            return (
                f"Your lab results are in. {report} "
                "Everything looks normal - nothing to worry about!"
            )
        else:
            return (
                f"Your lab results are in. {report} "
                "However, I'm not a doctor and cannot provide medical interpretations. "
                "Please call our office at +1-234-567-8900 to discuss these results "
                "with your healthcare provider."
            )
    
    return "I couldn't find your lab results. Please call our office at +1-234-567-8900 for assistance."

