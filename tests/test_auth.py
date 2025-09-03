import unittest
import json
from app import create_app
from app.config import TestingConfig

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test client"""
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up after tests"""
        self.app_context.pop()

    def test_token_generation_success(self):
        """Test successful token generation"""
        response = self.client.post('/api/auth/token',
                                  data=json.dumps({'api_key': 'sabda_flutter_2025_secure_key'}),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('token', data['data'])

    def test_token_generation_invalid_key(self):
        """Test token generation with invalid API key"""
        response = self.client.post('/api/auth/token',
                                  data=json.dumps({'api_key': 'invalid_key'}),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')

    def test_token_generation_missing_key(self):
        """Test token generation without API key"""
        response = self.client.post('/api/auth/token',
                                  data=json.dumps({}),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')

if __name__ == '__main__':
    unittest.main()
