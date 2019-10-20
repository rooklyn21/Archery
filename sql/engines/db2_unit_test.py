import json
from datetime import timedelta, datetime
from unittest.mock import patch, Mock, ANY

# from django.contrib.auth import get_user_model
# from django.test import TestCase
# from common.config import SysConfig

# sql实例
# from sql.models import Instance
# from django.db import models
from common.utils.aes_decryptor import Prpcrypt

from sql.engines import EngineBase
from sql.engines.models import ResultSet, ReviewSet, ReviewResult
from sql.engines.db2 import Db2Engine


class Instance:
    def __init__(self, instance_name, host, port, user,password, db_name, protocol):
        # Instance('db2inst1','127.0.0.1',50000,'db2inst1','db2inst1','SAMPLE','TCPIP')
        self.instance_name = instance_name
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db_name = db_name
        self.protocol = protocol
    @property
    def raw_password(self):
        # """ 返回明文密码 str """
        # pc = Prpcrypt()  # 初始化
        # return pc.decrypt(self.password)
        return self.password


class TestDb2:
    def __init__(self):
        self.ins = Instance('db2inst1', '127.0.0.1', 50000, 'db2inst1', 'db2inst1', 'SAMPLE', 'TCPIP')
        # return self.ins

    def test_get_connection(self):
        new_engine = Db2Engine(instance=self.ins)
        if new_engine.get_connection(self.ins):
            print("test pass")
        else:
            print("fail")

    def test_server_version(self):
        new_engine = Db2Engine(instance=self.ins)
        new_engine.get_connection(self.ins)
        version = new_engine.server_version
        print(version)

    def test_get_all_schemas(self):
        new_engine = Db2Engine(instance=self.ins)
        new_engine.get_connection(self.ins)
        rs = new_engine._get_all_schemas()
        print(rs.to_dict())
        # for each in rs.to_dict():
        #     print(each['SCHEMANAME'])

    def test_get_all_tables(self):
        new_engine = Db2Engine(instance=self.ins)
        new_engine.get_connection(self.ins)
        rs = new_engine.get_all_tables()
        print(rs.to_dict())

    def get_all_columns_by_tb(self):
        new_engine = Db2Engine(instance=self.ins)
        new_engine.get_connection(self.ins)
        rs = new_engine.get_all_columns_by_tb(self.ins.db_name,'STAFF')
        print(rs.to_dict())

    def test_describe_table(self):
        new_engine = Db2Engine(instance=self.ins)
        new_engine.get_connection(self.ins)
        rs = new_engine.describe_table(self.ins.db_name,'ACT')
        print(rs.to_dict())

    def test_query_check(self):
        new_engine = Db2Engine(instance=self.ins)
        new_engine.get_connection(self.ins)
        sql = f"""select * from staff"""
        rs = new_engine.query_check(self.ins.db_name,sql)
        print(rs)

    def test_filter_sql(self):
        new_engine = Db2Engine(instance=self.ins)
        new_engine.get_connection(self.ins)
        sql = f"""select * from staff"""
        rs = new_engine.filter_sql(sql,5)
        print(rs)

    def test_query(self):
        new_engine = Db2Engine(instance=self.ins)
        new_engine.get_connection(self.ins)
        rs = new_engine.query("SAMPLE", f"""SELECT * FROM staff limit 5""")
        print(rs.to_dict())

    def test_query_masking(self):
        new_engine = Db2Engine(instance=self.ins)
        new_engine.get_connection(self.ins)
        rs = new_engine.query_masking("SAMPLE", f"""SELECT * FROM staff limit 5""")
        print(rs.to_dict())

test1 = TestDb2()
# test1.test_get_connection()
test1.test_server_version()
# test1.test_get_all_schemas()
# test1.test_get_all_tables()
# test1.test_query()
# test1.get_all_columns_by_tb()
# test1.test_describe_table()
# test1.test_query_check()
test1.test_filter_sql()