import random
import string


class PasswordUtils:

    @ staticmethod
    def generate_random_password():
        """
        Creates a new random password for a new user.
        """
        new_pass = random.choice(string.ascii_uppercase)
        new_pass += "".join(random.choices(string.ascii_lowercase, k=5))
        new_pass += "".join(random.choices(string.digits, k=3))
        return new_pass
