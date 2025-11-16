# coding: utf-8

from __future__ import absolute_import
import os
os.environ['TESTING'] = 'true'  # Activar modo test antes de importar

from unittest.mock import patch

from flask import json
from six import BytesIO

from swagger_server.models.error import Error  # noqa: E501
from swagger_server.models.payment_method import PaymentMethod  # noqa: E501
from swagger_server.test import BaseTestCase


class TestPaymentController(BaseTestCase):
    """PaymentController integration test stubs"""

    @patch('swagger_server.controllers.payment_controller.dbConectar')
    def test_add_payment_method(self, mock_db):
        """Test case for add_payment_method
        
        Verifica que se puede añadir un método de pago válido.
        """
        # Mock base de datos
        mock_conn = mock_db.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.lastrowid = 1
        
        body = PaymentMethod(
            card_number='1234567812345678',
            expire_month=12,
            expire_year=2030,
            card_holder='John Doe'
        )
        
        # Configurar cookie en el cliente de test
        self.client.set_cookie('localhost', 'token', 'test_token_123')
        
        response = self.client.open(
            '/payment',
            method='POST',
            data=json.dumps(body),
            content_type='application/json'
        )
        
        self.assert200(response, 'Response body is : ' + response.data.decode('utf-8'))

    @patch('swagger_server.controllers.payment_controller.dbConectar')
    def test_delete_payment_method(self, mock_db):
        """Test case for delete_payment_method

        Delete a payment method by ID.
        """
        # Mock base de datos
        mock_conn = mock_db.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchone.return_value = (1,)  # Método pertenece al usuario
        
        # Configurar cookie en el cliente de test
        self.client.set_cookie('localhost', 'token', 'test_token_123')
        
        response = self.client.open(
            '/payment/{paymentMethodId}'.format(paymentMethodId='1'),
            method='DELETE'
        )
        
        self.assert200(response, 'Response body is : ' + response.data.decode('utf-8'))

    @patch('swagger_server.controllers.payment_controller.dbConectar')
    def test_show_user_payment_methods(self, mock_db):
        """Test case for show_user_payment_methods
        
        Verifica que se pueden listar los métodos de pago del usuario.
        """
        # Mock base de datos
        mock_conn = mock_db.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = []  # Sin métodos de pago
        
        # Configurar cookie en el cliente de test
        self.client.set_cookie('localhost', 'token', 'test_token_123')
        
        response = self.client.open(
            '/payment',
            method='GET'
        )
        
        self.assert200(response, 'Response body is : ' + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()

