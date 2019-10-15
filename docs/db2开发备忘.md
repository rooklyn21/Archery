# 开发指南
https://github.com/hhyo/archery/wiki/%E5%BC%80%E5%8F%91%E8%80%85%E6%8C%87%E5%8D%97

## 如何接入不支持的数据库

### 在model层加入新数据库的名字 https://github.com/hhyo/Archery/blob/master/sql/models.py#L72
     Archery/sql/models.py
     
     DB_TYPE_CHOICES = (
    ('mysql', 'MySQL'),
    ('mssql', 'MsSQL'),
    ('redis', 'Redis'),
    ('pgsql', 'PgSQL'),
    ('oracle', 'Oracle'),
    ('db2', 'Db2'),
    ('mongo', 'Mongo'),
    ('phoenix', 'Phoenix'),
    ('inception', 'Inception'),
    ('goinception', 'goInception'))
    
### 在engines目录下新增一个 python 文件, 如oracle.py , 文件内部定义一个Engine, 并继承EngineBase:
    Archery/sql/engines/
    
    from sql.engines import EngineBase
    
    
    class OracleEngine(EngineBase):
        def get_connection(self, db_name=None):
    ...

将下列方法实现后, 这种数据库的查询方法就可用了
    def get_connection(self):
    def query_check(self):
    def filter_sql(self):
    def query(self):
    def get_all_databases(self):
    def get_all_tables(self):
    def get_all_columns_by_tb(self):
    def describe_table(self):

将其他方法实现后, 工单执行就可用了, 
所有实现都可以暂时使用伪实现, 如脱敏, 语句检查等, 
只要返回值和文档中要求一致即可

### 在 __init__.py 的 get_engine 函数中加入新类型数据库的入口 
    Archery/blob/master/sql/engines/__init__.py

    elif instance.db_type == 'oracle':
        from .oracle import OracleEngine
    return OracleEngine(instance=instance)

一个接入范例 Redis的接入: https://github.com/hhyo/Archery/pull/101

## 遇到的问题

### 在db2.py实现get_connection函数，在 db2test.py 中测试
django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet.
在db2test.py和db2.py中注释掉以下引用。
# from django.contrib.auth import get_user_model
# from django.test import TestCase
# from common.config import SysConfig

AttributeError: 'ibm_db.IBM_DBConnection' object has no attribute 'thread_id'
查看api文档
https://github.com/ibmdb/python-ibmdb/wiki/APIs

### 函数列表

    ibm_db.num_rows(res))
    ibm_db.rollback(conn)
    ibm_db.close(conn)
    
    ibm_db.prepare(conn, sql, )
    ibm_db.fetch_row(stmt)
    ibm_db.fetch_tuple(stmt)    //Returns a tuple, indexed by column position, representing a row in a result set.
    ibm_db.fetch_assoc(stmt)    //Returns a dict, indexed by column name, representing a row in a result set.
    ibm_db.fetch_both(stmt)     //Returns a dict, indexed by column name and position, representing a row in a result set.
    
    ibm_db.exec_immediate(conn, sql)
    resultSet = ibm_db.procedure_columns(conn, None, '', 'PROC', None)
    row = ibm_db.fetch_assoc(resultSet)
    
    stmt = ibm_db.prepare(conn, sql, )
    rows = ibm_db.fetch_row(stmt)
    
    ibm_db.result()
    
sql = "update tabmany set id=15 where id < 40"
res = ibm_db.exec_immediate(conn, sql)
print ("Number of affected rows: %d" % ibm_db.num_rows(res))
ibm_db.rollback(conn)
ibm_db.close(conn)

sql = "select id, name from tabmany"
stmt = ibm_db.exec_immediate(conn, sql)
while (ibm_db.fetch_row(stmt)):
    id = ibm_db.result(stmt, "ID")
    name = ibm_db.result(stmt, "NAME")
    print("col1 = {}, col2 = {}".format(id, name))
    
    
### The ibm_db contains:

    ibm_db driver: Python driver for IBM DB2 and IBM Informix databases. Uses the IBM Data Server Driver for ODBC and CLI APIs to connect to IBM DB2 and Informix.
    ibm_db_dbi: Python driver for IBM DB2 and IBM Informix databases that complies to the DB-API 2.0 specification. Checkout the README for getting started with ibm_db and ibm_db_dbi

https://github.com/ibmdb/python-ibmdb/blob/master/IBM_DB/ibm_db/README.md
>>> import ibm_db
>>> conn_str='database=pydev;hostname=host.test.com;port=portno;protocol=tcpip;uid=db2inst1;pwd=secret'
>>> ibm_db_conn = ibm_db.connect(conn_str,'','')
>>> import ibm_db_dbi
>>> conn = ibm_db_dbi.Connection(ibm_db_conn)
>>> conn.tables('SYSCAT', '%')