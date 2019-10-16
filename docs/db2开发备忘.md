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

### 查看api文档

版本一：https://github.com/ibmdb/python-ibmdb/wiki/APIs 
版本二：https://www.python.org/dev/peps/pep-0249/#connection-objects

### db2连接方式

    # dsn方式需要配置 \Lib\site-packages\clidriver\cfg\db2dsdriver.cfg
    db2_conn = ibm_db.connect(db_name, '', '')
    
    # config 方式需要配置 Lib\site-packages\config.py
    import config
    db2_conn = ibm_db.connect(config.database, config.user, config.password)
    
    # 此方式需要从engines--__init__.py中获取连接参数
    conn_str = "DATABASE=%s;HOSTNAME=%s;PORT=%s;PROTOCOL=%s;UID=%s;PWD=%s" % \
        (self.db_name, self.host, self.port, self.protocol, self.user, self.password)
    db2_conn = ibm_db.connect(conn_str, '', '')

    # 直连方式
    conn_str = "DATABASE=SAMPLE;HOSTNAME=127.0.0.1;PORT=50000;PROTOCOL=TCPIP;UID=db2inst1;PWD=db2inst1"
    db2_conn = ibm_db.connect(conn_str, '', '')

### 运行db2test.py报错

### 问题1，TypeError: query() got an unexpected keyword argument 'sql'
    TypeError: query() takes 1 positional argument but 2 were given

原因：db2.py中复制多了query空函数，删掉即可
    def query(self):
        return 0

    sql = "SELECT * FROM animals"
    a.query(sql=sql)

#### 问题2，AttributeError: 'ibm_db.IBM_DBConnection' object has no attribute 'close'
因为self_conn用的是ibm_db.connect函数
db2_conn = ibm_db.connect(conn_str, '', '')
self.conn = db2_conn

所以在部分需要ibm_db_dbi.Connection的调用中需要添加语句
conn = ibm_db_dbi.Connection(self.conn)

#### 问题3，<sql.engines.models.ResultSet object at 0x0000019590515198>对象无法查看
result = a.get_all_databases()

# 查看ResultSet对象
在models.py里查找ResultSet对象，发现有json, to_dict, to_sep_dict 函数，调用to_dict查看
    for each in result.to_dict():
        print(each['TABNAME'])

### ibm_db_dbi接口函数

查看ibm_db_dbi.py文件，检查class Connection的成员函数

    __get_dbms_name()
    __get_dbms_ver()
    get_current_schema
    server_info
    tables(self, schema_name=None, table_name=None):
    indexes(self, unique=True, schema_name=None, table_name=None):
    primary_keys(self, unique=True, schema_name=None, table_name=None):
    
    callproc(self, procname, parameters=None)
    execute(self, operation, parameters=None)
    executemany(self, operation, seq_parameters):
    fetchone(self):
    fetchmany(self, size=0):
    fetchall(self):
    nextset(self):
    
### ibm_db接口函数

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
```
import ibm_db
import ibm_db_dbi

conn_str='database=pydev;hostname=host.test.com;port=portno;protocol=tcpip;uid=db2inst1;pwd=secret'
ibm_db_conn = ibm_db.connect(conn_str,'','')
conn = ibm_db_dbi.Connection(ibm_db_conn)
conn.tables('SYSCAT', '%')
```