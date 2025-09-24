import os
import jwt

from tools import TimeTools


class TokenManager:
    @staticmethod
    def encode_token(payload) -> str:
        secret = os.getenv("JWT_SECRET", "secretApp")
        return jwt.encode(payload, secret, algorithm="HS256")

    @staticmethod
    def verify_token_expiration(token: str) -> bool:
        payload = jwt.decode(token, verify=False)

        expiration = payload.get("exp")
        if expiration is None:
            return False

        if int(expiration) < int(TimeTools.get_now_in_milliseconds()):
            return False

        return True

    @staticmethod
    def decode_token(token) -> dict | None:
        secret = os.getenv("JWT_SECRET", "secretApp")
        try:
            res = jwt.decode(token, secret, algorithms=["HS256"])
            return res
        except Exception:
            return None

    @staticmethod
    def super_token_verify(token: str) -> dict | None:
        public_key = os.getenv("SUPER_PUBLIC_KEY", "secret")
        public_key_bytes = public_key.encode("utf-8")

        try:
            res = jwt.decode(token, public_key_bytes, algorithms=["EdDSA"])
            return res
        except Exception:
            return None
