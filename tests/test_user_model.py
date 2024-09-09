import unittest
from app.models import User


class UserModelTests(unittest.TestCase):
    def test_password_setter(self):
        u = User.anonymous_user('cat')
        self.assertTrue(u.password_hash is not None)
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_password_no_getter(self):
        u = User.anonymous_user('cat')
        with self.assertRaises(AttributeError):
            print(u.password)

if __name__ == '__main__':
    unittest.main()
