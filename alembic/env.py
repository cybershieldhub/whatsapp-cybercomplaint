from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# import your Base
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from backend.models import Base  # <- add this

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

target_metadata = Base.metadata  # <- add this
