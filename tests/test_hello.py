import unittest
from app import create_app

class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')

    def test_something(self):
        with self.app.test_client() as client:
            response = client.get("/hello/inline")
            print(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Hello World!', response.data)

if __name__ == '__main__':
    unittest.main()
