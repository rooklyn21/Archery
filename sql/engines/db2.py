# -*- coding: UTF-8 -*-

import ibm_db
import ibm_db_dbi
# import config
import logging
import traceback
import re
import sqlparse

#django相关
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

    def get_connection(self, db_name=None):
        if self.conn:
            return self.conn

        conn_str = "DATABASE=%s;HOSTNAME=%s;PORT=%s;PROTOCOL=TCPIP;UID=%s;PWD=%s" % \
            (self.db_name, self.host, self.port, self.user, self.password)

        # conn_str = "DATABASE=SAMPLE;HOSTNAME=127.0.0.1;PORT=50000;PROTOCOL=TCPIP;UID=db2inst1;PWD=db2inst1"
        # self.conn = db2_conn

        ibm_db_conn = ibm_db.connect(conn_str, '', '')
        self.conn = ibm_db_dbi.Connection(ibm_db_conn)

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
        result = self.query(sql="SELECT schemaname FROM syscat.schemata where schemaname = CURRENT SCHEMA")
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

    def get_all_columns_by_tb(self, db_name, tb_name):
        """获取所有字段, 返回一个ResultSet"""
        result = self.describe_table(db_name, tb_name)
        column_list = [row[0] for row in result.rows]
        result.rows = column_list
        return result

    def describe_table(self, db_name, tb_name):
        """return ResultSet"""
        sql = f"""SELECT COLNAME,TYPENAME,LENGTH,NULLS,DEFAULT FROM syscat.columns WHERE tabname='{tb_name.upper()}'
        """
        result = self.query(sql=sql)
        return result

    def query_check(self, db_name=None, sql=''):
        # 查询语句的检查、注释去除、切分
        result = {'msg': '', 'bad_query': False, 'filtered_sql': sql, 'has_star': False}
        keyword_warning = ''
        star_patter = r"(^|,| )\*( |\(|$)"
        # 删除注释语句，进行语法判断，执行第一条有效sql
        try:
            sql = sqlparse.split(sql)[0]
            result['filtered_sql'] = re.sub(r';$', '', sql.strip())
            sql = sqlparse.format(sql, strip_comments=True)
            sql_lower = sql.lower()
        except IndexError:
            result['bad_query'] = True
            result['msg'] = '没有有效的SQL语句'
            return result
        if re.match(r"^select", sql_lower) is None:
            result['bad_query'] = True
            result['msg'] = '仅支持^select语法!'
            return result
        if re.search(star_patter, sql_lower) is not None:
            keyword_warning += '禁止使用 * 关键词\n'
            result['has_star'] = True
        if '+' in sql_lower:
            keyword_warning += '禁止使用 + 关键词\n'
            result['bad_query'] = True
        if result.get('bad_query') or result.get('has_star'):
            result['msg'] = keyword_warning
        return result

    def filter_sql(self, sql='', limit_num=0):
        sql_lower = sql.lower()
        # 对查询sql增加limit限制
        if re.match(r"^select", sql_lower):
            if sql_lower.find(' rows only ') == -1:
                if sql_lower.find('where') == -1:
                    return f"{sql.rstrip(';')} FETCH FIRST {limit_num} ROWS ONLY"
                else:
                    return f"{sql.rstrip(';')} FETCH FIRST {limit_num} ROWS ONLY "
        return sql.strip()


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

    def query_masking(self, schema_name=None, sql='', resultset=None):
        """传入 sql语句, db名, 结果集,
        返回一个脱敏后的结果集"""
        # 仅对select语句脱敏
        if re.match(r"^select", sql, re.I):
            filtered_result = brute_mask(resultset)
            filtered_result.is_masked = True
        else:
            filtered_result = resultset
        return filtered_result

    def execute_check(self, db_name=None, sql=''):
        """上线单执行前的检查, 返回Review set"""
        config = SysConfig()
        check_result = ReviewSet(full_sql=sql)
        # 禁用/高危语句检查
        line = 1
        critical_ddl_regex = config.get('critical_ddl_regex', '')
        p = re.compile(critical_ddl_regex)
        check_result.syntax_type = 2  # TODO 工单类型 0、其他 1、DDL，2、DML
        for statement in sqlparse.split(sql):
            statement = sqlparse.format(statement, strip_comments=True)
            # 禁用语句
            if re.match(r"^select", statement.lower()):
                check_result.is_critical = True
                result = ReviewResult(id=line, errlevel=2,
                                      stagestatus='驳回不支持语句',
                                      errormessage='仅支持DML和DDL语句，查询语句请使用SQL查询功能！',
                                      sql=statement)
            # 高危语句
            elif critical_ddl_regex and p.match(statement.strip().lower()):
                check_result.is_critical = True
                result = ReviewResult(id=line, errlevel=2,
                                      stagestatus='驳回高危SQL',
                                      errormessage='禁止提交匹配' + critical_ddl_regex + '条件的语句！',
                                      sql=statement)

            # 正常语句
            else:
                result = ReviewResult(id=line, errlevel=0,
                                      stagestatus='Audit completed',
                                      errormessage='None',
                                      sql=statement,
                                      affected_rows=0,
                                      execute_time=0, )
            # 判断工单类型
            if get_syntax_type(statement) == 'DDL':
                check_result.syntax_type = 1
            check_result.rows += [result]

            # 遇到禁用和高危语句直接返回，提高效率
            if check_result.is_critical:
                check_result.error_count += 1
                return check_result
            line += 1
        return check_result

    def execute_workflow(self, workflow, close_conn=True):
        """执行上线单，返回Review set"""
        sql = workflow.sqlworkflowcontent.sql_content
        execute_result = ReviewSet(full_sql=sql)
        # 删除注释语句，切分语句，将切换CURRENT_SCHEMA语句增加到切分结果中
        sql = sqlparse.format(sql, strip_comments=True)
        split_sql = [f"SET CURRENT SCHEMA = {workflow.db_name};"] + sqlparse.split(sql)
        line = 1
        statement = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            # 逐条执行切分语句，追加到执行结果中
            for statement in split_sql:
                statement = statement.rstrip(';')
                with FuncTimer() as t:
                    cursor.execute(statement)
                    conn.commit()
                execute_result.rows.append(ReviewResult(
                    id=line,
                    errlevel=0,
                    stagestatus='Execute Successfully',
                    errormessage='None',
                    sql=statement,
                    affected_rows=cursor.rowcount,
                    execute_time=t.cost,
                ))
                line += 1
        except Exception as e:
            logger.warning(f"DB2命令执行报错，语句：{statement or sql}， 错误信息：{traceback.format_exc()}")
            execute_result.error = str(e)
            # 追加当前报错语句信息到执行结果中
            execute_result.rows.append(ReviewResult(
                id=line,
                errlevel=2,
                stagestatus='Execute Failed',
                errormessage=f'异常信息：{e}',
                sql=statement or sql,
                affected_rows=0,
                execute_time=0,
            ))
            line += 1
            # 报错语句后面的语句标记为审核通过、未执行，追加到执行结果中
            for statement in split_sql[line - 1:]:
                execute_result.rows.append(ReviewResult(
                    id=line,
                    errlevel=0,
                    stagestatus='Audit completed',
                    errormessage=f'前序语句失败, 未执行',
                    sql=statement,
                    affected_rows=0,
                    execute_time=0,
                ))
                line += 1
        finally:
            if close_conn:
                self.close()
        return execute_result

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None