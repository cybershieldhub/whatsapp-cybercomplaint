import pytest
from backend.models import Session, SessionState

def test_session_initial_stage():
    session = Session(phone="+911234567890")
    # Default stage should be START
    assert session.stage == SessionState.START.value

def test_session_state_transitions():
    session = Session(phone="+911234567890")
    
    # Transition through states
    session.set_stage(SessionState.COLLECTING)
    assert session.stage == SessionState.COLLECTING.value

    session.set_stage(SessionState.PREFILL_REQUESTED)
    assert session.stage == SessionState.PREFILL_REQUESTED.value

    session.set_stage(SessionState.AWAITING_CAPTCHA)
    assert session.stage == SessionState.AWAITING_CAPTCHA.value

    session.set_stage(SessionState.AWAITING_OTP)
    assert session.stage == SessionState.AWAITING_OTP.value

    session.set_stage(SessionState.SUBMITTING)
    assert session.stage == SessionState.SUBMITTING.value

    session.set_stage(SessionState.SUBMITTED)
    assert session.stage == SessionState.SUBMITTED.value

    session.set_stage(SessionState.EXPIRED)
    assert session.stage == SessionState.EXPIRED.value
