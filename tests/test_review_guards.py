"""Independent regression checks for claims that would mislead a customer."""
import pytest

from zentro.agent import guard_reply


@pytest.mark.parametrize("claim", [
    "I have successfully cancelled your order.",
    "Your refund has been processed.",
    "I have sent your complaint to the team.",
    "I've forwarded this to a human agent.",
    "Your ticket is ready.",
    "I have booked the reverse pickup.",
    "Your compensation has been credited.",
])
def test_no_unsupported_completed_action(claim):
    reply = guard_reply(claim, [], [], first=False)
    assert reply != claim, f"Unsupported completed action escaped guard: {claim}"


def test_policy_explanation_survives_action_guard():
    claim = "UPI refunds take 1 to 3 business days after initiation. [REF-2]"
    reply = guard_reply(claim, [], [{"section_id": "REF-2"}], first=False)
    assert "1 to 3 business days" in reply
    assert "[REF-2]" in reply


def test_successful_handover_uses_only_real_ticket_id():
    real_id = "TKT" + "a" * 32
    invented_id = "TKT" + "b" * 32
    calls = [{"name": "create_ticket", "result": {"created": True, "ticket_id": real_id}}]
    reply = guard_reply(f"Your ticket is {invented_id}.", calls, [], first=False)
    assert real_id in reply
    assert invented_id not in reply


@pytest.mark.parametrize("policy", [
    "Your refund will be processed within 5 to 7 business days after pickup. [REF-2]",
    "Once your return is picked up, the refund is initiated within 2 business days. [REF-2]",
    "Once your refund has been initiated, UPI refunds take 1 to 3 business days. [REF-2]",
    "If your order was cancelled before shipping, the refund is credited to the original method. [REF-2]",
])
def test_refund_timeline_explanations_survive(policy):
    reply = guard_reply(policy, [], [{"section_id": "REF-2"}], first=False)
    assert reply == policy


def test_case_state_allowed_only_from_verified_order():
    claim = "Your refund was initiated on 12 October 2026. [REF-2]"
    assert guard_reply(claim, [], [{"section_id": "REF-2"}], verified=True) == claim
    assert "initiated" not in guard_reply(claim, [], [{"section_id": "REF-2"}], verified=False)


@pytest.mark.parametrize("claim", ["I've gone ahead and cancelled your order.", "We have just refunded the amount."])
def test_self_claims_blocked_even_when_verified(claim):
    assert guard_reply(claim, [], [], verified=True) != claim


def test_invented_citation_drops_only_that_sentence():
    reply = guard_reply("UPI refunds take 1 to 3 business days [REF-2]. Wallet refunds are instant [FAKE-1].", [], [{"section_id": "REF-2"}])
    assert "1 to 3 business days" in reply and "FAKE" not in reply and "instant" not in reply


def test_clarifying_question_without_citation_is_not_replaced():
    from zentro.agent import ungrounded
    assert not ungrounded("Thanks! Could you share your order ID?", [])
    assert not ungrounded("Please share the order ID so I can check it.", [])
    assert ungrounded("Refunds take 5 to 7 business days.", [])


def test_ticket_id_survives_when_its_sentence_is_filtered():
    tid = "TKT" + "c" * 32
    calls = [{"name": "create_ticket", "result": {"created": True, "ticket_id": tid}}]
    reply = guard_reply(f"I've escalated it; your ticket ID is {tid} [NOPE-1].", calls, [{"section_id": "REF-2"}])
    assert tid in reply


def test_spoken_ticket_and_punctuation():
    from zentro.speech import normalize_speech
    spoken = normalize_speech("No compensation applies [DEL-4]. Your ticket ID is TKT" + "0" * 28 + "5fbd.")
    assert "TKT" not in spoken and "ticket number ends in 5 F B D" in spoken and " ." not in spoken


def test_premise_restatement_keeps_policy_answer():
    chunks = [{"section_id": s} for s in ("CAN-1", "REF-1", "REF-2")]
    raw = ("Since you cancelled before shipping, your refund was initiated immediately and reaches UPI "
           "in 1–3 business days. [CAN-1] [REF-1] [REF-2]")
    reply = guard_reply(raw, [], chunks, first=False)
    assert "1–3 business days" in reply


def test_dropped_claim_never_leaves_bare_citations():
    chunks = [{"section_id": "REF-1"}]
    raw = "I'm ZentroMart's AI support assistant. I have refunded your order. [REF-1]"
    reply = guard_reply(raw, [], chunks, first=False)
    assert "[REF-1]" not in reply
    assert "don't have that information" in reply
