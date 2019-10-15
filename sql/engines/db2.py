# -*- coding: UTF-8 -*-

import ibm_db
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
    def get_connection(self, db_name=None):
        if self.conn:
            # self.thread_id = self.conn.thread_id()
            return self.conn
        if db_name:
            self.conn = ibm_db.connect(config.database,config.user,config.password)
        else:
            self.conn = ibm_db.connect(config.user,config.password)

        # self.thread_id = self.conn.connectionID()

        return self.conn

    @property
    def name(self):
        return 'Db2'

    @property
    def info(self):
        return 'Db2 engine'

    @property
    def server_version(self):
        conn = self.get_connection()

        server_name = ibm_db.server_info(conn).DBMS_NAME
        server_version = ibm_db.server_info(conn).DBMS_VER
        version = server_name + '-' + server_version

        # sql_stmt = ibm_db.exec_immediate(conn, "SELECT service_level FROM TABLE (sysproc.env_get_inst_info())")
        # row = ibm_db.fetch_tuple(sql_stmt)
        # if row:
        #     version = row[0]

        return version

    def get_all_databases(self):
        """获取数据库列表， 返回resultSet 供上层调用， 暂未实现"""
        # return self._get_all_schemas()

    def query(self, db_name=None, sql='', limit_num=0, close_conn=True):
        """返回 ResultSet """
        result_set = ResultSet(full_sql=sql)
        try:
            conn = self.get_connection(db_name=db_name)

            stmt = ibm_db.prepare(conn, sql, )

            if int(limit_num) > 0:
                rows = ibm_db.fetch_row(stmt, int(limit_num))
            else:
                rows = ibm_db.fetch_row(stmt)

            fields = cursor.description

            result_set.column_list = [i[0] for i in fields] if fields else []
            result_set.rows = rows
            result_set.affected_rows = effect_row
        except Exception as e:
            logger.warning(f"MySQL语句执行报错，语句：{sql}，错误信息{traceback.format_exc()}")
            result_set.error = str(e)
        finally:
            if close_conn:
                self.close()
        return result_set


    def query_check(self):
        return 0
    def filter_sql(self):
        return 0
    def query(self):
        return 0
    def get_all_databases(self):
        return 0
    def get_all_tables(self):
        return 0
    def get_all_columns_by_tb(self):
        return 0
    def describe_table(self):
        return 0