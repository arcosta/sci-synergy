import os
import unittest
 
from scisynergy import app
 
class BasicTests(unittest.TestCase):
    def test_main_page(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
