# -*- coding: UTF-8 -*-

import ibm_db
import ibm_db_dbi
import config
import logging
import traceback
import re
import sqlparse

# from common.config import SysConfig
from common.utils.timer import FuncTimer
from sql.utils.sql_utils import get_syntax_type
from . import EngineBase
from .models import ResultSet, ReviewSet, ReviewResult
# from sql.utils.data_masking import brute_mask

logger = logging.getLogger('default')


class Db2Engine(EngineBase):

    def __init__(self, instance=None):
        super(Db2Engine, self).__init__(instance=instance)
        if instance:
            self.db_name = instance.db_name
            self.protocol = int(instance.protocol)

    def get_connection(self, db_name=None):
        if self.conn:
            return self.conn

        conn_str = "DATABASE=SAMPLE;HOSTNAME=127.0.0.1;PORT=50000;PROTOCOL=TCPIP;UID=db2inst1;PWD=db2inst1"

        # 此方式需要从engines--__init__.py中获取连接参数
        # conn_str = "DATABASE=%s;HOSTNAME=%s;PORT=%s;PROTOCOL=%s;UID=%s;PWD=%s" % \
        # (self.db_name, self.host, self.port, self.protocol, self.user, self.password)

        db2_conn = ibm_db.connect(conn_str, '', '')

        # self.conn = ibm_db_dbi.Connection(db2_conn)
        self.conn = db2_conn

        return self.conn

    @property
    def name(self):
        return 'Db2'

    @property
    def info(self):
        return 'Db2 engine'

    @property
    def server_version(self):
        conn = ibm_db_dbi.Connection(self.conn)
        return conn.server_info()

        # return self.conn.server_info()

    def get_all_databases(self):
        return 0

    def get_all_tables(self, schema_name=None):
        sql = "SELECT tabname FROM syscat.tables WHERE tabschema = CURRENT schema"
        result = self.query(sql=sql)
        db_list = result.rows
        result.rows = db_list
        return result

    def query(self, db_name=None, sql='', limit_num=0, close_conn=True):
        """返回 ResultSet """
        result_set = ResultSet(full_sql=sql)
        try:
            conn = ibm_db_dbi.Connection(self.conn)
            cursor = conn.cursor()
            effect_row = cursor.execute(sql)
            if int(limit_num) > 0:
                rows = cursor.fetchmany(size=int(limit_num))
            else:
                rows = cursor.fetchall()
            fields = cursor.description

            result_set.column_list = [i[0] for i in fields] if fields else []
            result_set.rows = rows
            result_set.affected_rows = effect_row
        except Exception as e:
            logger.warning(f"SQL语句执行报错，语句：{sql}，错误信息{traceback.format_exc()}")
            result_set.error = str(e)
        finally:
            if close_conn:
                self.close()
        return result_set

    def close(self):
        if self.conn:
            conn = ibm_db_dbi.Connection(self.conn)
            conn.close()
            self.conn = None