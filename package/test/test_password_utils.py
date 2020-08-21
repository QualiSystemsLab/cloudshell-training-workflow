import unittest

from cloudshell.orch.training.utils.password import PasswordUtils


class TestPasswordUtils(unittest.TestCase):

    def test_random_password(self):
        # act
        random_password1 = PasswordUtils.generate_random_password(12)
        random_password2 = PasswordUtils.generate_random_password(15)

        # assert
        self.assertNotEqual(random_password1, random_password2)
        self.assertEqual(len(random_password1), 12)
        self.assertEqual(len(random_password2), 15)