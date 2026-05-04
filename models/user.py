import os

import requests

from utils.supabase_client import get_supabase_client


# ========================= User Model =========================


class User():
    # set up the user object with the main profile fields
    def __init__(self, userId: str, displayName: str) -> None:
        self.userId = userId
        self.displayName = displayName


    # ========================= Calendar Methods =========================


    # list calendars owned by this user or shared with this user
    def list_calendars(self) -> list:
        db = get_supabase_client()

        # Supabase filters both owner and member matches in one query
        filterText = f"owner_id.eq.{self.userId},member_ids.cs.{{{self.userId}}}"
        query = db.table("calendars")
        query = query.select("*")
        query = query.or_(filterText)
        result = query.execute()

        return result.data or []


    # ========================= External Calendar Methods =========================


    # list external calendar connections for this user
    def list_externals(self) -> list:
        db = get_supabase_client()
        result = db.table("externals").select("*").eq("user_id", self.userId).execute()

        return result.data or []


    # ========================= Friend Methods =========================


    # get the raw friend ids from the user record
    def list_friends(self) -> list:
        db = get_supabase_client()
        result = db.table("users").select("friends").eq("id", self.userId).execute()

        if not result.data:
            return []

        return result.data[0].get("friends") or []


    # turn friend ids into full user rows
    def list_friends_data(self) -> list:
        friendIds = self.list_friends()

        if not friendIds:
            return []

        db = get_supabase_client()
        result = (
            db.table("users")
            .select("id, email, display_name")
            .in_("id", friendIds)
            .execute()
        )

        return result.data or []


    # add a friend by id email or display name
    def add_friend(self, friendId: str = None, email: str = None, value: str = None) -> list:
        db = get_supabase_client()
        lookup = email or value

        # find the friend id from email or display name when needed
        if friendId is None and lookup is not None:
            emailResult = db.table("users").select("id").eq("email", lookup).limit(1).execute()

            if emailResult.data:
                friendId = emailResult.data[0]["id"]
            else:
                nameResult = (
                    db.table("users")
                    .select("id")
                    .eq("display_name", lookup)
                    .limit(1)
                    .execute()
                )

                if nameResult.data:
                    friendId = nameResult.data[0]["id"]
                else:
                    friendId = lookup

        if friendId is None:
            raise ValueError("friend_id, email, or display name is required")

        # stop a user from adding their own account
        if friendId == self.userId:
            raise ValueError("User cannot add themselves as a friend")

        currentFriends = self.list_friends()

        if friendId in currentFriends:
            raise ValueError(f"User {friendId} is already a friend")

        currentFriends.append(friendId)
        db.table("users").update({"friends": currentFriends}).eq("id", self.userId).execute()

        return currentFriends


    # remove a friend id from the users friend list
    def remove_friend(self, friendId: str) -> None:
        db = get_supabase_client()
        currentFriends = self.list_friends()

        if friendId not in currentFriends:
            raise ValueError(f"User {friendId} is not in the friends list")

        currentFriends.remove(friendId)
        db.table("users").update({"friends": currentFriends}).eq("id", self.userId).execute()


    # ========================= Account Methods =========================


    # delete the user row and then ask Supabase auth to delete the auth user
    def remove_account(self, accessToken: str) -> None:
        db = get_supabase_client()
        db.table("users").delete().eq("id", self.userId).execute()

        supabaseUrl = os.getenv("SUPABASE_URL")
        requests.delete(
            f"{supabaseUrl}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {accessToken}",
                "apikey": os.getenv("SUPABASE_KEY", ""),
            },
        )


    # show the display name when debugging a user object
    def __repr__(self) -> str:
        return f"<User: {self.displayName}>"
