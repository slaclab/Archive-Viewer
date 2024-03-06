import os
from json import load
from logging import getLogger
from qtpy.QtGui import QColor


logger = getLogger(__name__)

with open("config.json") as f:
    loaded_json = load(f)

archiver_urls = loaded_json['archivers']
if not archiver_urls:
    archiver_urls = [os.getenv("PYDM_ARCHIVER_URL")]

color_palette = [QColor(hex_code) for hex_code in loaded_json['colors']]