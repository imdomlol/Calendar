from flask import g
from models.user import User


def makeUser() -> User:
    return User(
        userId=g.user["id"],
        displayName=g.user.get("display_name", ""),
    )
