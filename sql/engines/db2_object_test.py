import json
from datetime import timedelta, datetime
from unittest.mock import patch, Mock, ANY

# from django.contrib.auth import get_user_model
# from django.test import TestCase

from common.config import SysConfig
from sql.engines import EngineBase
from sql.engines.goinception import GoInceptionEngine
from sql.engines.models import ResultSet, ReviewSet, ReviewResult
from sql.engines.mssql import MssqlEngine
from sql.engines.mysql import MysqlEngine
from sql.engines.redis import RedisEngine
from sql.engines.pgsql import PgSQLEngine
from sql.engines.oracle import Db2Engine
from sql.engines.db2 import Db2Engine
from sql.engines.mongo import MongoEngine
from sql.engines.inception import InceptionEngine, _repair_json_str
from sql.models import Instance, SqlWorkflow, SqlWorkflowContent

User = get_user_model()


class TestReviewSet(TestCase):
    def test_review_set(self):
        new_review_set = ReviewSet()
        new_review_set.rows = [{'id': '1679123'}]
        self.assertIn('1679123', new_review_set.json())


class TestDb2(TestCase):
    """Db2 测试"""
    # self.conn = None
    # self.thread_id = None
    # if instance:
    #     self.instance = instance
    #     self.instance_name = instance.instance_name
    #     self.host = instance.host
    #     self.port = int(instance.port)
    #     self.user = instance.user
    #     self.password = instance.raw_password
    #     self.db_name = instance.db_name
    #     self.protocol = instance.protocol

    def setUp(self):
        self.ins = Instance.objects.create(instance_name='db2inst1', type='slave', db_type='db2',
                                           host='127.0.0.1', port=50000, user='db2inst1', password='db2inst1',
                                           db_name='SAMPLE', protocol='TCPIP')

    def test_get_connection(self, _connect, _makedsn):
        # 填写 sid 测试
        new_engine = Db2Engine(self.ins)
        new_engine.get_connection()
        _connect.assert_called_once()
        _makedsn.assert_called_once()
        # 填写 service_name 测试
        _connect.reset_mock()
        _makedsn.reset_mock()
        self.ins.service_name = 'some_service'
        self.ins.sid = ''
        self.ins.save()
        new_engine = Db2Engine(self.ins)
        new_engine.get_connection()
        _connect.assert_called_once()
        _makedsn.assert_called_once()
        # 都不填写, 检测 ValueError
        _connect.reset_mock()
        _makedsn.reset_mock()
        self.ins.service_name = ''
        self.ins.sid = ''
        self.ins.save()
        new_engine = Db2Engine(self.ins)
        with self.assertRaises(ValueError):
            new_engine.get_connection()

    @patch('cx_Oracle.connect')
    def test_engine_base_info(self, _conn):
        new_engine = Db2Engine(instance=self.ins)
        self.assertEqual(new_engine.name, 'Oracle')
        self.assertEqual(new_engine.info, 'Oracle engine')
        _conn.return_value.version = '12.1.0.2.0'
        self.assertTupleEqual(new_engine.server_version, ('12', '1', '0'))

    @patch('cx_Oracle.connect.cursor.execute')
    @patch('cx_Oracle.connect.cursor')
    @patch('cx_Oracle.connect')
    def test_query(self, _conn, _cursor, _execute):
        _conn.return_value.cursor.return_value.fetchmany.return_value = [(1,)]
        new_engine = Db2Engine(instance=self.ins)
        query_result = new_engine.query(db_name='archery', sql='select 1', limit_num=100)
        self.assertIsInstance(query_result, ResultSet)
        self.assertListEqual(query_result.rows, [(1,)])

    @patch('cx_Oracle.connect.cursor.execute')
    @patch('cx_Oracle.connect.cursor')
    @patch('cx_Oracle.connect')
    def test_query_not_limit(self, _conn, _cursor, _execute):
        _conn.return_value.cursor.return_value.fetchall.return_value = [(1,)]
        new_engine = Db2Engine(instance=self.ins)
        query_result = new_engine.query(db_name=0, sql='select 1', limit_num=0)
        self.assertIsInstance(query_result, ResultSet)
        self.assertListEqual(query_result.rows, [(1,)])

    @patch('sql.engines.oracle.Db2Engine.query',
           return_value=ResultSet(rows=[('AUD_SYS',), ('archery',), ('ANONYMOUS',)]))
    def test_get_all_databases(self, _query):
        new_engine = Db2Engine(instance=self.ins)
        dbs = new_engine.get_all_databases()
        self.assertListEqual(dbs.rows, ['archery'])

    @patch('sql.engines.oracle.Db2Engine.query',
           return_value=ResultSet(rows=[('AUD_SYS',), ('archery',), ('ANONYMOUS',)]))
    def test__get_all_databases(self, _query):
        new_engine = Db2Engine(instance=self.ins)
        dbs = new_engine._get_all_databases()
        self.assertListEqual(dbs.rows, ['AUD_SYS', 'archery', 'ANONYMOUS'])

    @patch('sql.engines.oracle.Db2Engine.query',
           return_value=ResultSet(rows=[('archery',)]))
    def test__get_all_instances(self, _query):
        new_engine = Db2Engine(instance=self.ins)
        dbs = new_engine._get_all_instances()
        self.assertListEqual(dbs.rows, ['archery'])

    @patch('sql.engines.oracle.Db2Engine.query',
           return_value=ResultSet(rows=[('ANONYMOUS',), ('archery',), ('SYSTEM',)]))
    def test_get_all_schemas(self, _query):
        new_engine = Db2Engine(instance=self.ins)
        schemas = new_engine._get_all_schemas()
        self.assertListEqual(schemas.rows, ['archery'])

    @patch('sql.engines.oracle.Db2Engine.query', return_value=ResultSet(rows=[('test',), ('test2',)]))
    def test_get_all_tables(self, _query):
        new_engine = Db2Engine(instance=self.ins)
        tables = new_engine.get_all_tables(db_name='archery')
        self.assertListEqual(tables.rows, ['test2'])

    @patch('sql.engines.oracle.Db2Engine.query',
           return_value=ResultSet(rows=[('id',), ('name',)]))
    def test_get_all_columns_by_tb(self, _query):
        new_engine = Db2Engine(instance=self.ins)
        columns = new_engine.get_all_columns_by_tb(db_name='archery', tb_name='test2')
        self.assertListEqual(columns.rows, ['id', 'name'])

    @patch('sql.engines.oracle.Db2Engine.query',
           return_value=ResultSet(rows=[('archery',), ('template1',), ('template0',)]))
    def test_describe_table(self, _query):
        new_engine = Db2Engine(instance=self.ins)
        describe = new_engine.describe_table(db_name='archery', tb_name='text')
        self.assertIsInstance(describe, ResultSet)

    def test_query_check_disable_sql(self):
        sql = "update xxx set a=1;"
        new_engine = Db2Engine(instance=self.ins)
        check_result = new_engine.query_check(db_name='archery', sql=sql)
        self.assertDictEqual(check_result,
                             {'msg': '仅支持^select语法!', 'bad_query': True, 'filtered_sql': sql.strip(';'),
                              'has_star': False})

    def test_query_check_star_sql(self):
        sql = "select * from xx;"
        new_engine = Db2Engine(instance=self.ins)
        check_result = new_engine.query_check(db_name='archery', sql=sql)
        self.assertDictEqual(check_result,
                             {'msg': '禁止使用 * 关键词\n', 'bad_query': False, 'filtered_sql': sql.strip(';'),
                              'has_star': True})

    def test_query_check_IndexError(self):
        sql = ""
        new_engine = Db2Engine(instance=self.ins)
        check_result = new_engine.query_check(db_name='archery', sql=sql)
        self.assertDictEqual(check_result,
                             {'msg': '没有有效的SQL语句', 'bad_query': True, 'filtered_sql': sql.strip(), 'has_star': False})

    def test_query_check_plus(self):
        sql = "select 100+1 from tb;"
        new_engine = Db2Engine(instance=self.ins)
        check_result = new_engine.query_check(db_name='archery', sql=sql)
        self.assertDictEqual(check_result,
                             {'msg': '禁止使用 + 关键词\n', 'bad_query': True, 'filtered_sql': sql.strip(';'),
                              'has_star': False})

    def test_filter_sql_with_delimiter(self):
        sql = "select * from xx;"
        new_engine = Db2Engine(instance=self.ins)
        check_result = new_engine.filter_sql(sql=sql, limit_num=100)
        self.assertEqual(check_result, "select * from xx WHERE ROWNUM <= 100")

    def test_filter_sql_with_delimiter_and_where(self):
        sql = "select * from xx where id>1;"
        new_engine = Db2Engine(instance=self.ins)
        check_result = new_engine.filter_sql(sql=sql, limit_num=100)
        self.assertEqual(check_result, "select * from xx where id>1 AND ROWNUM <= 100")

    def test_filter_sql_without_delimiter(self):
        sql = "select * from xx;"
        new_engine = Db2Engine(instance=self.ins)
        check_result = new_engine.filter_sql(sql=sql, limit_num=100)
        self.assertEqual(check_result, "select * from xx WHERE ROWNUM <= 100")

    def test_filter_sql_with_limit(self):
        sql = "select * from xx limit 10;"
        new_engine = Db2Engine(instance=self.ins)
        check_result = new_engine.filter_sql(sql=sql, limit_num=1)
        self.assertEqual(check_result, "select * from xx limit 10 WHERE ROWNUM <= 1")

    def test_query_masking(self):
        query_result = ResultSet()
        new_engine = Db2Engine(instance=self.ins)
        masking_result = new_engine.query_masking(schema_name='', sql='select 1', resultset=query_result)
        self.assertEqual(masking_result, query_result)

    def test_execute_check_select_sql(self):
        sql = 'select * from user;'
        row = ReviewResult(id=1, errlevel=2,
                           stagestatus='驳回不支持语句',
                           errormessage='仅支持DML和DDL语句，查询语句请使用SQL查询功能！',
                           sql=sql)
        new_engine = Db2Engine(instance=self.ins)
        check_result = new_engine.execute_check(db_name='archery', sql=sql)
        self.assertIsInstance(check_result, ReviewSet)
        self.assertEqual(check_result.rows[0].__dict__, row.__dict__)

    def test_execute_check_critical_sql(self):
        self.sys_config.set('critical_ddl_regex', '^|update')
        self.sys_config.get_all_config()
        sql = 'update user set id=1'
        row = ReviewResult(id=1, errlevel=2,
                           stagestatus='驳回高危SQL',
                           errormessage='禁止提交匹配' + '^|update' + '条件的语句！',
                           sql=sql)
        new_engine = Db2Engine(instance=self.ins)
        check_result = new_engine.execute_check(db_name='archery', sql=sql)
        self.assertIsInstance(check_result, ReviewSet)
        self.assertEqual(check_result.rows[0].__dict__, row.__dict__)

    def test_execute_check_normal_sql(self):
        self.sys_config.purge()
        sql = 'alter table tb set id=1'
        row = ReviewResult(id=1,
                           errlevel=0,
                           stagestatus='Audit completed',
                           errormessage='None',
                           sql=sql,
                           affected_rows=0,
                           execute_time=0, )
        new_engine = Db2Engine(instance=self.ins)
        check_result = new_engine.execute_check(db_name='archery', sql=sql)
        self.assertIsInstance(check_result, ReviewSet)
        self.assertEqual(check_result.rows[0].__dict__, row.__dict__)

    @patch('cx_Oracle.connect.cursor.execute')
    @patch('cx_Oracle.connect.cursor')
    @patch('cx_Oracle.connect')
    def test_execute_workflow_success(self, _conn, _cursor, _execute):
        sql = 'update user set id=1'
        row = ReviewResult(id=1,
                           errlevel=0,
                           stagestatus='Execute Successfully',
                           errormessage='None',
                           sql=sql,
                           affected_rows=0,
                           execute_time=0,
                           full_sql=sql)
        wf = SqlWorkflow.objects.create(
            workflow_name='some_name',
            group_id=1,
            group_name='g1',
            engineer_display='',
            audit_auth_groups='some_group',
            create_time=datetime.now() - timedelta(days=1),
            status='workflow_finish',
            is_backup=True,
            instance=self.ins,
            db_name='some_db',
            syntax_type=1
        )
        SqlWorkflowContent.objects.create(workflow=wf, sql_content=sql)
        new_engine = Db2Engine(instance=self.ins)
        execute_result = new_engine.execute_workflow(workflow=wf)
        self.assertIsInstance(execute_result, ReviewSet)
        self.assertEqual(execute_result.rows[0].__dict__.keys(), row.__dict__.keys())

    @patch('cx_Oracle.connect.cursor.execute')
    @patch('cx_Oracle.connect.cursor')
    @patch('cx_Oracle.connect', return_value=RuntimeError)
    def test_execute_workflow_exception(self, _conn, _cursor, _execute):
        sql = 'update user set id=1'
        row = ReviewResult(id=1,
                           errlevel=2,
                           stagestatus='Execute Failed',
                           errormessage=f'异常信息：{f"Oracle命令执行报错，语句：{sql}"}',
                           sql=sql,
                           affected_rows=0,
                           execute_time=0, )
        wf = SqlWorkflow.objects.create(
            workflow_name='some_name',
            group_id=1,
            group_name='g1',
            engineer_display='',
            audit_auth_groups='some_group',
            create_time=datetime.now() - timedelta(days=1),
            status='workflow_finish',
            is_backup=True,
            instance=self.ins,
            db_name='some_db',
            syntax_type=1
        )
        SqlWorkflowContent.objects.create(workflow=wf, sql_content=sql)
        with self.assertRaises(AttributeError):
            new_engine = Db2Engine(instance=self.ins)
            execute_result = new_engine.execute_workflow(workflow=wf)
            self.assertIsInstance(execute_result, ReviewSet)
            self.assertEqual(execute_result.rows[0].__dict__.keys(), row.__dict__.keys())

