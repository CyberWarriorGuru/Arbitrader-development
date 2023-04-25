"""
Development settings
"""

from .settings import *

DEBUG = True

SECRET_KEY = get_env_var("SECRET_KEY")

ALLOWED_HOSTS = ["*"]


if not os.path.exists(BASE_DIR / "logs"):
    os.mkdir(BASE_DIR / "logs")

LOG_FILE = BASE_DIR / "logs" / "dev.log"
