from app.core.language import resolve_language


def test_user_language_override_wins_over_org_default():
    assert resolve_language(org_default="en", user_override="nl") == "nl"


def test_org_default_language_applies_when_no_user_override():
    assert resolve_language(org_default="nl", user_override=None) == "nl"
