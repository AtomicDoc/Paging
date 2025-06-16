import unittest
from Server import app

class FlaskAppTests(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_admin_page_exists(self):
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 200)

    def test_client_page_exists(self):
        response = self.client.get('/client')
        self.assertEqual(response.status_code, 200)

    def test_successful_login(self):
        response = self.client.post('/login', json={'password': 'CHANGEME'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'success', response.data)

    def test_failed_login(self):
        response = self.client.post('/login', json={'password': 'wrongpassword'})
        self.assertEqual(response.status_code, 401)
        self.assertIn(b'Wrong Password', response.data)

    def test_play_alert_endpoint_with_users(self):
        # Fake user ID list to simulate checkbox-based selection
        response = self.client.post('/play_alert', json={'users': ['fake_user_id']})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'success', response.data)

    def test_play_alert_endpoint_with_group(self):
        # Fake group name to simulate Group A or B
        response = self.client.post('/play_alert', json={'group': 'Group A'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'success', response.data)

    def test_send_tts_with_users(self):
        response = self.client.post('/send_tts', json={
            'message': 'Test TTS',
            'users': ['fake_user_id']
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'success', response.data)

    def test_send_tts_with_group(self):
        response = self.client.post('/send_tts', json={
            'message': 'Group message',
            'group': 'A'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'success', response.data)

    def test_send_tts_missing_fields(self):
        response = self.client.post('/send_tts', json={})
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
