import json
from datetime import timedelta, datetime
from unittest.mock import patch, Mock, ANY

# django相关
# from django.contrib.auth import get_user_model
# from django.test import TestCase
# from common.config import SysConfig

# sql实例
# from sql.models import Instance
from django.db import models
from common.utils.aes_decryptor import Prpcrypt

from sql.engines import EngineBase
from sql.engines.models import ResultSet, ReviewSet, ReviewResult
from sql.engines.db2 import Db2Engine


class TestDb2():

    def setUp(self):
        self.ins = Instance.objects.create(instance_name='db2inst1', type='slave', db_type='db2',
                                           host='127.0.0.1', port=50000, user='db2inst1', password='db2inst1',
                                           db_name='SAMPLE', protocol='TCPIP')
    def test_get_connection(self):
        new_engine = Db2Engine(instance=self.ins)
        new_engine.get_connection(self.ins)
        version = new_engine.server_version
        print(version)

    def test_other(self):
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

        result = a.get_all_databases()


        # 测试查询语句
        # result = a.query("SAMPLE", f"""SELECT * FROM animals""")

        for each in result.to_dict():
            print(each)

        # for each in result.to_dict():
        #     print(each)

        # for each in result.to_sep_dict()['rows']:
        #     print(each)

        # new_engine = Db2Engine(instance=inst1)
        # new_engine.get_connection()

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

class Instance(models.Model):
    """
    各个线上实例配置
    """
    instance_name = models.CharField('实例名称', max_length=50, unique=True)
    type = models.CharField('实例类型', max_length=6, choices=(('master', '主库'), ('slave', '从库')))
    db_type = models.CharField('数据库类型', max_length=20, choices=DB_TYPE_CHOICES)
    host = models.CharField('实例连接', max_length=200)
    port = models.IntegerField('端口', default=0)
    user = models.CharField('用户名', max_length=100, default='', blank=True)
    password = models.CharField('密码', max_length=300, default='', blank=True)
    charset = models.CharField('字符集', max_length=20, default='', blank=True)
    service_name = models.CharField('Oracle service name', max_length=50, null=True, blank=True)
    sid = models.CharField('Oracle sid', max_length=50, null=True, blank=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    @property
    def raw_password(self):
        """ 返回明文密码 str """
        pc = Prpcrypt()  # 初始化
        return pc.decrypt(self.password)

    def __str__(self):
        return self.instance_name

    class Meta:
        managed = True
        db_table = 'sql_instance'
        verbose_name = u'实例配置'
        verbose_name_plural = u'实例配置'

    def save(self, *args, **kwargs):
        pc = Prpcrypt()  # 初始化
        if self.password:
            if self.id:
                old_password = Instance.objects.get(id=self.id).password
            else:
                old_password = ''
            # 密码有变动才再次加密保存
            self.password = pc.encrypt(self.password) if old_password != self.password else self.password
        super(Instance, self).save(*args, **kwargs)

TestDb2().setUp()
TestDb2().test_get_connection()