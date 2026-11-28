import pytest

from kardex.core.policies import PolicyDecision


def test_allowed_decision_has_no_reason():
    decision = PolicyDecision(allowed=True)

    assert decision.allowed is True
    assert decision.reason is None


def test_allowed_decision_accepts_a_reason():
    decision = PolicyDecision(allowed=True, reason="Sin restricciones.")

    assert decision.allowed is True
    assert decision.reason == "Sin restricciones."


def test_allowed_decision_does_not_require_a_reason():
    decision = PolicyDecision(allowed=True, reason="   ")

    assert decision.allowed is True


@pytest.mark.parametrize("reason", [None, "", "   "])
def test_rejected_decision_requires_a_non_empty_reason(reason: str | None):
    with pytest.raises(ValueError, match="Una decisión rechazada requiere un motivo."):
        PolicyDecision(allowed=False, reason=reason)


def test_rejected_decision_accepts_a_reason():
    decision = PolicyDecision(allowed=False, reason="Regla incumplida.")

    assert decision.allowed is False
    assert decision.reason == "Regla incumplida."
