from flask import Blueprint, abort, g, request
from utils.auth import require_auth
from utils.request_helpers import makeUser

user_bp = Blueprint("user", __name__)


@user_bp.route("/me", methods=["GET"])
@require_auth
def getMe():
    user = getattr(g, "user", {})
    uid = user.get("id") or user.get("sub")
    return {
        "id": uid,
        "email": user.get("email"),
        "role": user.get("role"),
        "last_sign_in_at": user.get("last_sign_in_at"),
    }, 200


@user_bp.route("/me", methods=["DELETE"])
@require_auth
def deleteMe():
    user = makeUser()
    user.removeAccount()
    return "", 204


@user_bp.route("/friends", methods=["GET"])
@require_auth
def listFriends():
    user = makeUser()
    return {"friends": user.listFriends()}


@user_bp.route("/friends", methods=["POST"])
@require_auth
def addFriend():
    body = request.get_json(silent=True) or {}
    friendId = body.get("friend_id")
    email = body.get("email")
    user = makeUser()
    try:
        friends = user.addFriend(friendId=friendId, email=email)
    except ValueError as e:
        abort(400, description=str(e))
    return {"friends": friends}


@user_bp.route("/friends/<friend_id>", methods=["DELETE"])
@require_auth
def removeFriend(friend_id):
    user = makeUser()
    try:
        user.removeFriend(friend_id)
    except ValueError as e:
        abort(404, description=str(e))
    return "", 204
