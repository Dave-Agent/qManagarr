import requests
from . import db


def get_session():
    """Returns an authenticated (session, host) pair, or (None, None) on failure."""
    host = db.get_setting("qbt_host")
    username = db.get_setting("qbt_username")
    password = db.get_setting("qbt_password")

    if not host:
        return None, None

    try:
        session = requests.Session()
        res = session.post(
            f"{host}/api/v2/auth/login",
            data={"username": username, "password": password},
            timeout=10,
        )
        if "Ok" in res.text:
            return session, host
        return None, None
    except Exception:
        return None, None
