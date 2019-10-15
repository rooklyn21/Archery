import json
import config
from datetime import timedelta, datetime
from unittest.mock import patch, Mock, ANY

# from django.contrib.auth import get_user_model
# from django.test import TestCase
# from common.config import SysConfig
from sql.engines import EngineBase
from sql.engines.models import ResultSet, ReviewSet, ReviewResult
from sql.engines.db2 import Db2Engine

a = Db2Engine()
a.get_connection(db_name='sample')
print(a.server_version)
print(a.get_all_databases())

# new_engine = Db2Engine(instance=inst1)
# new_engine.get_connection()

