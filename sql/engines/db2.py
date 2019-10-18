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
            self.protocol = instance.protocol

    def get_connection(self, db_name=None):
        if self.conn:
            return self.conn

        # conn_str = "DATABASE=SAMPLE;HOSTNAME=127.0.0.1;PORT=50000;PROTOCOL=TCPIP;UID=db2inst1;PWD=db2inst1"
        conn_str = "DATABASE=%s;HOSTNAME=%s;PORT=%s;PROTOCOL=%s;UID=%s;PWD=%s" % \
            (self.db_name, self.host, self.port, self.protocol, self.user, self.password)

        db2_conn = ibm_db.connect(conn_str, '', '')
        # self.conn = db2_conn
        self.conn = ibm_db_dbi.Connection(db2_conn)

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
        return conn.server_info()


    def get_all_databases(self):
        """获取数据库列表， 返回resultSet 供上层调用， 底层实际上是获取db2的schema列表"""
        return self._get_all_schemas()

    def _get_all_databases(self):
        """获取数据库列表, 返回一个ResultSet"""
        sql = "SELECT name FROM sysibm.sysschemata WHERE definer=%s " % (self.service_name.upper())
        result = self.query(sql=sql)
        db_list = [row[0] for row in result.rows]
        result.rows = db_list
        return result

    def _get_all_instances(self):
        """获取实例列表, 返回一个ResultSet"""
        sql = "SELECT name FROM sysibm.sysschemata WHERE definer=%s " % (self.service_name.upper())
        result = self.query(sql=sql)
        instance_list = [row[0] for row in result.rows]
        result.rows = instance_list
        return result

    def _get_all_schemas(self):
        """获取模式列表, 返回一个ResultSet"""
        result = self.query(sql="SELECT schemaname FROM syscat.schemata ")
        schemaname = ('DB2INST1','NULLID','SQLJ','SYSCAT','SYSFUN','SYSIBM','SYSIBMADM','SYSIBMINTERNAL',
                      'SYSIBMTS','SYSPROC','SYSPUBLIC','SYSSTAT','SYSTOOLS')
        schema_list = [row[0] for row in result.rows if row[0] not in schemaname]
        result.rows = schema_list
        return result

    def get_all_tables(self, schema_name=None):
        """获取table 列表, 返回一个ResultSet"""
        sql = "SELECT tabname FROM syscat.tables WHERE tabschema = CURRENT schema"
        result = self.query(sql=sql)
        db_list = result.rows
        result.rows = db_list
        return result


    def query(self, db_name=None, sql='', limit_num=0, close_conn=True):
        """返回 ResultSet """
        result_set = ResultSet(full_sql=sql)
        try:
            conn = self.get_connection()
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