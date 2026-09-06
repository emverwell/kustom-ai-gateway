from app.policy import load_policy


def test_load_policy_reads_actions():
    policy = load_policy()
    assert policy.action_for("CREDIT_CARD") == "block"
    assert policy.action_for("EMAIL_ADDRESS") == "redact"


def test_unknown_entity_defaults_to_allow():
    policy = load_policy()
    assert policy.action_for("SOMETHING_UNCONFIGURED") == "allow"


def test_custom_entity_carries_patterns():
    policy = load_policy()
    rule = policy.entities["INTERNAL_PROJECT_CODENAME"]
    assert rule.action == "block"
    assert len(rule.patterns) == 1


def test_ve_cedula_has_two_patterns_with_distinct_scores():
    policy = load_policy()
    rule = policy.entities["VE_CEDULA"]
    assert rule.action == "redact"
    by_name = {p.name: p for p in rule.patterns}
    assert by_name["v_prefixed"].context == []
    assert by_name["bare_digits_with_context"].context == ["cedula", "cédula"]
    assert by_name["v_prefixed"].score > by_name["bare_digits_with_context"].score
