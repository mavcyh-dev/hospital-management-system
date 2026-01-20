import bcrypt


class SecurityService:
    """
    Handles password hashing and verification using bcrypt.
    bcrypt automatically generates a unique salt for every hash.
    """

    def __init__(self, rounds: int = 12):
        # cost factor — 12 is a good secure default
        self.rounds = rounds

    def hash_password(self, plain_password: str) -> str:
        """Hash a password using bcrypt. Returns UTF-8 string."""
        # always encode to bytes for bcrypt
        plain_bytes = plain_password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed_bytes = bcrypt.hashpw(plain_bytes, salt)
        return hashed_bytes.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a stored hash."""
        plain_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
