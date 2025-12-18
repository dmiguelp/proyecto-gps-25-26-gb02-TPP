#!/usr/bin/env python3

import connexion

from swagger_server import encoder
import os

def main():
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('swagger.yaml', arguments={'title': 'Tienda y Pasarela de Pago (TPP)'}, pythonic_params=True)
    app.run(host=os.environ.get('HOST', '0.0.0.0'), port=int(os.environ.get('PORT', 8082)))


if __name__ == '__main__':
    main()
