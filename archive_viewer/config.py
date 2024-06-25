import os
from json import load
from pathlib import Path
from logging import getLogger
from qtpy.QtGui import QColor


config_file = Path(__file__).parent / "config.json"
with config_file.open() as f:
    loaded_json = load(f)

logger = getLogger(__name__)

save_file_dir = Path(os.path.expandvars(loaded_json['save_file_dir']))
if not save_file_dir.is_dir():
    save_file_dir = Path.home()

archiver_urls = loaded_json['archivers']
if not archiver_urls:
    archiver_urls = [os.getenv("PYDM_ARCHIVER_URL")]

color_palette = [QColor(hex_code) for hex_code in loaded_json['colors']]
