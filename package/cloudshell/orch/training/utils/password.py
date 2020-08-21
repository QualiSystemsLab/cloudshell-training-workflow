import random
import secrets
import string


class PasswordUtils:

    @ staticmethod
    def generate_random_password(length=12):
        """
        Creates a new random password for a new user.
        """
        # new_pass = random.choice(string.ascii_uppercase)
        # new_pass += "".join(random.choices(string.ascii_lowercase, k=5))
        # new_pass += "".join(random.choices(string.digits, k=3))

        password_characters = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(password_characters) for i in range(length))
