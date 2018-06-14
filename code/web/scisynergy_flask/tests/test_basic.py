import os
import unittest
 
from scisynergy_flask import app
 
class BasicTests(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_main_page(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_maintenance(self):
        response = self.app.get('/maintenance')

        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()