import logging
import os

import connexion
from flask_testing import TestCase
from unittest.mock import patch, MagicMock

from swagger_server.encoder import JSONEncoder


class BaseTestCase(TestCase):

    def create_app(self):
        # Activar modo testing
        os.environ['TESTING'] = 'true'
        
        logging.getLogger('connexion.operation').setLevel('ERROR')
        app = connexion.App(__name__, specification_dir='../swagger/')
        app.app.json_encoder = JSONEncoder
        app.add_api('swagger.yaml', validate_responses=False)
        return app.app
    
    def tearDown(self):
        # Desactivar modo testing al terminar
        os.environ.pop('TESTING', None)
