import os
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_modelo")

import pkgutil
import importlib
from config.jwt_config import *

from flask import Flask, request, jsonify

app = Flask(__name__)
predictions_cache = {}

import views
for module_info in pkgutil.iter_modules(views.__path__):
    module = importlib.import_module(f"views.{module_info.name}")
    exec(f"from views.{module_info.name} import *")


if __name__=="__main__":
    app.run(debug=True)