import random
import string


class IdentifierService:
    @staticmethod
    def generate_id(prefix: str, length: int = 22) -> str:
        """Generate a prefixed ID with a specified length of random
        alphanumeric characters."""
        characters = string.ascii_letters + string.digits
        random_string = "".join(random.choice(characters) for _ in range(length))
        return f"{prefix}_{random_string}"

    @staticmethod
    def generate_position_id() -> str:
        """Generate a position ID."""
        return IdentifierService.generate_id("pos")

    @staticmethod
    def generate_prefixed_id(prefix) -> str:
        """Generate valid UUID4 string for Qdrant compatibility"""
        return IdentifierService.generate_id(prefix)



if __name__ == "__main__":
    identity = IdentifierService()
    print(identity.generate_position_id())
