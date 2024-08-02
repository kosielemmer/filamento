import unittest
from app import app, get_db_connection
from unittest.mock import patch, MagicMock

class TestRoutes(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('app.get_db_connection')
    def test_index(self, mock_db_conn):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    @patch('app.get_db_connection')
    def test_select_manufacturer(self, mock_db_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(1, 'Manufacturer1'), (2, 'Manufacturer2')]
        mock_db_conn.return_value.cursor.return_value = mock_cursor

        response = self.app.get('/select_manufacturer')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Manufacturer1', response.data)
        self.assertIn(b'Manufacturer2', response.data)

    @patch('app.get_db_connection')
    def test_select_filament_type(self, mock_db_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [('PLA',), ('ABS',)]
        mock_db_conn.return_value.cursor.return_value = mock_cursor

        response = self.app.get('/select_filament_type/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'PLA', response.data)
        self.assertIn(b'ABS', response.data)

    @patch('app.get_db_connection')
    def test_select_color(self, mock_db_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [('Red', '#FF0000'), ('Blue', '#0000FF')]
        mock_db_conn.return_value.cursor.return_value = mock_cursor

        response = self.app.get('/select_color?manufacturer_id=1&filament_type=PLA')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Red', response.data)
        self.assertIn(b'Blue', response.data)

    def test_select_shelf(self):
        response = self.app.get('/select_shelf?manufacturer_id=1&filament_type=PLA&color_name=Red&color_hex_code=%23FF0000')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Select Shelf', response.data)

    def test_select_position(self):
        response = self.app.get('/select_position/1/PLA/Red/%23FF0000/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Select Position', response.data)

    @patch('app.get_db_connection')
    def test_add_inventory(self, mock_db_conn):
        mock_cursor = MagicMock()
        mock_db_conn.return_value.cursor.return_value = mock_cursor

        response = self.app.post('/add_inventory', data={
            'manufacturer_id': '1',
            'filament_type': 'PLA',
            'color_name': 'Red',
            'color_hex_code': '#FF0000',
            'location': 'Shelf 1 Left Front'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Success', response.data)

    @patch('app.get_db_connection')
    def test_view_inventory(self, mock_db_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [('Manufacturer1', 'PLA', 'Red', '#FF0000', 'Shelf 1 Left Front')]
        mock_db_conn.return_value.cursor.return_value = mock_cursor

        response = self.app.get('/view_inventory')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Manufacturer1', response.data)
        self.assertIn(b'PLA', response.data)
        self.assertIn(b'Red', response.data)
        self.assertIn(b'Shelf 1 Left Front', response.data)

if __name__ == '__main__':
    unittest.main()
