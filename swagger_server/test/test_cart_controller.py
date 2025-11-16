# coding: utf-8

from __future__ import absolute_import
import os
os.environ['TESTING'] = 'true'  # Activar modo test antes de importar

from unittest.mock import patch

from flask import json
from six import BytesIO

from swagger_server.models.cart_body import CartBody  # noqa: E501
from swagger_server.models.error import Error  # noqa: E501
from swagger_server.models.product import Product  # noqa: E501
from swagger_server.test import BaseTestCase


class TestCartController(BaseTestCase):
    """CartController integration test stubs"""

    @patch('swagger_server.controllers.cart_controller.dbConectar')
    def test_add_to_cart(self, mock_db):
        """Test case for add_to_cart
        
        Verifica que se puede añadir un producto al carrito
        con autenticación válida.
        """
        # Mock base de datos
        mock_conn = mock_db.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchone.return_value = None  # No existe en carrito
        
        body = CartBody(song_id=1, album_id=None, merch_id=None, unidades=None)
        
        # Configurar cookie en el cliente de test
        self.client.set_cookie('localhost', 'token', 'test_token_123')
        
        response = self.client.open(
            '/cart',
            method='POST',
            data=json.dumps(body),
            content_type='application/json'
        )
        
        self.assert200(response, 'Response body is : ' + response.data.decode('utf-8'))

    @patch('swagger_server.controllers.cart_controller.dbConectar')
    def test_get_cart_products(self, mock_db):
        """Test case for get_cart_products
        
        Verifica que se pueden obtener los productos del carrito.
        """
        # Mock base de datos
        mock_conn = mock_db.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = []  # Carrito vacío
        
        # Configurar cookie en el cliente de test
        self.client.set_cookie('localhost', 'token', 'test_token_123')
        
        response = self.client.open(
            '/cart',
            method='GET'
        )
        
        self.assert200(response, 'Response body is : ' + response.data.decode('utf-8'))

    @patch('swagger_server.controllers.cart_controller.dbConectar')
    def test_remove_from_cart(self, mock_db):
        """Test case for remove_from_cart
        
        Verifica que se puede eliminar un producto del carrito.
        """
        # Mock base de datos
        mock_conn = mock_db.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchone.return_value = (1,)  # Existe en carrito
        
        # Configurar cookie en el cliente de test
        self.client.set_cookie('localhost', 'token', 'test_token_123')
        
        response = self.client.open(
            '/cart/{productId}'.format(productId=1),
            method='DELETE',
            query_string=[('type', 'song')]
        )
        
        self.assert200(response, 'Response body is : ' + response.data.decode('utf-8'))

    def test_cart_without_auth(self):
        """Test case for cart operations without authentication
        
        Verifica que sin token se rechaza el acceso.
        """
        response = self.client.open(
            '/cart',
            method='GET'
        )
        
        # Debería retornar 401 sin autenticación
        self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    import unittest
    unittest.main()

