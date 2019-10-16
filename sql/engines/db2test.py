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
a.get_connection()

# 测试server_version函数
version = a.server_version
print(version)

# result = a.get_all_databases()

# 测试get_all_tables()函数
# result = a.get_all_tables()
# for each in result.to_dict():
#     print(each['TABNAME'])

# 测试查询语句
result = a.query("SAMPLE", f"""SELECT * FROM animals""")
for each in result.to_dict():
    print(each)

# for each in result.to_dict():
#     print(each)

# for each in result.to_sep_dict()['rows']:
#     print(each)

# new_engine = Db2Engine(instance=inst1)
# new_engine.get_connection()

