# coding: utf-8

from __future__ import absolute_import
import os
os.environ['TESTING'] = 'true'  # Activar modo test antes de importar

# Fix para Python 3.12: collections.Callable movido a collections.abc.Callable
import collections
import collections.abc
if not hasattr(collections, 'Callable'):
    collections.Callable = collections.abc.Callable

from unittest.mock import patch

from flask import json
from six import BytesIO

from swagger_server.models.error import Error  # noqa: E501
from swagger_server.models.purchase import Purchase  # noqa: E501
from swagger_server.test import BaseTestCase


class TestPurchasesController(BaseTestCase):
    """PurchasesController integration test stubs"""

    @patch('swagger_server.controllers.purchases_controller.dbConectar')
    @patch('swagger_server.controllers.purchases_controller.requests.post')
    def test_set_purchase(self, mock_post, mock_db):
        """Test case for set_purchase
        
        Verifica que se puede realizar una compra.
        """
        # Mock base de datos
        mock_conn = mock_db.return_value
        mock_cursor = mock_conn.cursor.return_value
        
        # Mock para validación de método de pago (pertenece al usuario)
        # Mock para inserción de compra (retorna ID)
        def fetchone_side_effect():
            # Primera llamada: validación de método de pago
            # Segunda llamada: ID de compra insertada
            for value in [(1,), (100,)]:
                yield value
        
        mock_cursor.fetchone.side_effect = fetchone_side_effect()
        
        body = Purchase(
            purchase_price=19.99,
            purchase_date='2025-11-16T10:00:00Z',
            payment_method_id=1,
            song_ids=[1, 2],
            album_ids=[1],
            merch_ids=[]
        )
        
        # Configurar cookie en el cliente de test
        self.client.set_cookie('localhost', 'token', 'test_token_123')
        
        response = self.client.open(
            '/purchase',
            method='POST',
            data=json.dumps(body),
            content_type='application/json'
        )
        
        self.assert200(response, 'Response body is : ' + response.data.decode('utf-8'))

    def test_purchase_without_auth(self):
        """Test case for purchase without authentication
        
        Verifica que sin token se rechaza el acceso.
        """
        body = Purchase(
            purchase_price=19.99,
            purchase_date='2025-11-16T10:00:00Z',
            payment_method_id=1,
            song_ids=[1],
            album_ids=[],
            merch_ids=[]
        )
        
        response = self.client.open(
            '/purchase',
            method='POST',
            data=json.dumps(body),
            content_type='application/json'
        )
        
        # Debería retornar 401 sin autenticación
        self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    import unittest
    unittest.main()

