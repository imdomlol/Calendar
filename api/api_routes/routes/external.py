import os
from flask import abort, request
from api.api_routes import api_bp
from api.api_routes.helpers import makeUser
from models.external import External
from utils.auth import require_auth
from utils.supabase_client import get_supabase_client


def _oauth_credentials_for_provider(provider: str) -> tuple[str, str]:
    provider = (provider or "").lower()
    if provider == "google":
        return (
            os.environ.get("GOOGLE_CLIENT_ID", "").strip(),
            os.environ.get("GOOGLE_CLIENT_SECRET", "").strip(),
        )
    if provider == "outlook":
        return (
            os.environ.get("MS_CLIENT_ID", "").strip(),
            os.environ.get("MS_CLIENT_SECRET", "").strip(),
        )
    return "", ""


@api_bp.route("/externals", methods=["GET"])
@require_auth
def listExternals():
    user = makeUser()
    return {"externals": user.listExternals()}


@api_bp.route("/externals", methods=["POST"])
@require_auth
def createExternal():
    body = request.get_json(silent=True) or {}
    url = body.get("url")
    provider = body.get("provider")
    if not url or not provider:
        abort(400, description="url and provider are required")
    user = makeUser()
    db = get_supabase_client()
    ext = External(
        id=None,
        url=url,
        provider=provider,
        supabaseClient=db,
        userId=user.userId,
        accessToken=body.get("access_token"),
        refreshToken=body.get("refresh_token"),
    )
    result = ext.save()
    return result.data[0], 201


@api_bp.route("/externals/<external_id>", methods=["DELETE"])
@require_auth
def deleteExternal(external_id):
    user = makeUser()
    db = get_supabase_client()
    ext = External(
        id=external_id,
        url="",
        provider="",
        supabaseClient=db,
        userId=user.userId,
    )
    try:
        ext.remove(external_id)
    except ValueError:
        abort(404)
    return "", 204


@api_bp.route("/externals/<external_id>/pull", methods=["POST"])
@require_auth
def pullExternalData(external_id):
    user = makeUser()
    db = get_supabase_client()
    ownership = db.table("externals").select("id, provider").eq("id", external_id).eq("user_id", user.userId).execute()
    if not ownership.data:
        abort(404)
    client_id, client_secret = _oauth_credentials_for_provider(ownership.data[0].get("provider"))
    ext = External(
        id=external_id,
        url="",
        provider="",
        supabaseClient=db,
        userId=user.userId,
    )
    try:
        data = ext.pullCalData(external_id, client_id=client_id, client_secret=client_secret)
    except Exception as e:
        abort(500, description=f"Failed to pull data: {e}")
    return {"data": data}, 200


@api_bp.route("/externals/<external_id>/push", methods=["POST"])
@require_auth
def pushExternalData(external_id):
    user = makeUser()
    db = get_supabase_client()
    ownership = db.table("externals").select("id, provider").eq("id", external_id).eq("user_id", user.userId).execute()
    if not ownership.data:
        abort(404)
    client_id, client_secret = _oauth_credentials_for_provider(ownership.data[0].get("provider"))
    ext = External(
        id=external_id,
        url="",
        provider="",
        supabaseClient=db,
        userId=user.userId,
    )
    try:
        data = ext.pushCalData(external_id, client_id=client_id, client_secret=client_secret)
    except Exception as e:
        abort(500, description=f"Failed to push data: {e}")
    return {"data": data}, 200
