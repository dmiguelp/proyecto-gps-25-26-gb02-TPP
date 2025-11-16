# coding: utf-8

from __future__ import absolute_import
import os
os.environ['TESTING'] = 'true'  # Activar modo test antes de importar

from unittest.mock import patch, MagicMock

from flask import json
from six import BytesIO

from swagger_server.models.error import Error  # noqa: E501
from swagger_server.models.product import Product  # noqa: E501
from swagger_server.test import BaseTestCase

class TestStoreController(BaseTestCase):
    """StoreController integration test stubs"""

    @patch('swagger_server.controllers.store_controller.requests.get')
    def test_show_storefront_products(self, mock_get):
        """Test case for show_storefront_products
        
        Verifica que el endpoint /store retorna productos paginados
        desde el microservicio TyA.
        """
        # Mock de las respuestas del microservicio TyA
        mock_response_filter = MagicMock()
        mock_response_filter.ok = True
        mock_response_filter.json.return_value = [
            {"songId": 1},
            {"songId": 2}
        ]
        
        mock_response_list = MagicMock()
        mock_response_list.ok = True
        mock_response_list.json.return_value = [
            {
                "songId": 1,
                "title": "Test Song 1",
                "artistId": 1,
                "albumId": 1,
                "price": 1.99,
                "description": "Test",
                "releaseDate": "2024-01-01",
                "duration": 180,
                "cover": "base64...",
                "genres": [1],
                "collaborators": []
            },
            {
                "songId": 2,
                "title": "Test Song 2",
                "artistId": 1,
                "albumId": 1,
                "price": 2.99,
                "description": "Test",
                "releaseDate": "2024-01-01",
                "duration": 200,
                "cover": "base64...",
                "genres": [1],
                "collaborators": []
            }
        ]
        
        # Configurar mock para retornar diferentes respuestas según la URL
        def side_effect(url, *args, **kwargs):
            if 'filter' in url:
                return mock_response_filter
            elif 'list' in url:
                return mock_response_list
            return MagicMock(ok=False)
        
        mock_get.side_effect = side_effect
        
        # Hacer la petición
        response = self.client.open(
            '/store?page=1&limit=10',
            method='GET'
        )
        
        # Verificaciones
        self.assert200(response, 'Response body is : ' + response.data.decode('utf-8'))
        
        data = json.loads(response.data.decode('utf-8'))
        
        # Verificar estructura de paginación
        self.assertIn('data', data)
        self.assertIn('pagination', data)
        self.assertIn('page', data['pagination'])
        self.assertIn('limit', data['pagination'])
        self.assertIn('total', data['pagination'])
        self.assertIn('totalPages', data['pagination'])


if __name__ == '__main__':
    import unittest
    unittest.main()

