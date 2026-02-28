from app.domain.identity.models import User


def test_user_language_can_be_set_and_persisted(db):
    user = User(email="lang@local", is_active=True, language="nl")
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.language == "nl"


def test_user_language_can_be_null(db):
    user = User(email="lang-null@local", is_active=True, language=None)
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.language is None
