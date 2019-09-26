# code:utf8

import ibm_db
import ibm_db_dbi
import unittest

name = 'name'
picture = 'picture'


class IbmDbTestCase(unittest.TestCase):
    def test_000_PrepareDb(self):
        # obj = IbmDbTestFunctions()
        # obj.assert_expect(self.run_test_000)
        self.run_test_000

    def run_test_000(self):
        # Make a connection
        conn_str='database=frontend;hostname=10.137.102.31;port=50000;protocol=tcpip;uid=db2inst1;pwd=db2inst1'
        conn_str1='database=sample;hostname=localhost;port=50001;protocol=tcpip;uid=db2inst1;pwd=db2inst1'
        conn = ibm_db.connect(conn_str1,'','')

        # Get the server type
        server = ibm_db.server_info( conn )

        # Drop the animal table, in case it exists
        drop = 'DROP TABLE animals'
        try:
            result = ibm_db.exec_immediate(conn, drop)
        except:
            pass

        # Create the animal table
        create = 'CREATE TABLE animals (id INTEGER, breed VARCHAR(32), name CHAR(16), weight DECIMAL(7,2))'
        result = ibm_db.exec_immediate(conn, create)

        # Populate the animal table
        animals = (
            (0, 'cat', 'Pook', 3.2),
            (1, 'dog', 'Peaches', 12.3),
            (2, 'horse', 'Smarty', 350.0),
            (3, 'gold fish', 'Bubbles', 0.1),
            (4, 'budgerigar', 'Gizmo', 0.2),
            (5, 'goat', 'Rickety Ride', 9.7),
            (6, 'llama', 'Sweater', 150)
        )
        insert = 'INSERT INTO animals (id, breed, name, weight) VALUES (?, ?, ?, ?)'
        stmt = ibm_db.prepare(conn, insert)
        if stmt:
            for animal in animals:
                result = ibm_db.execute(stmt, animal)

        # Drop the test view, in case it exists
        drop = 'DROP VIEW anime_cat'
        try:
            result = ibm_db.exec_immediate(conn, drop)
        except:
            pass
        # Create test view
        ibm_db.exec_immediate(conn, """CREATE VIEW anime_cat AS
            SELECT name, breed FROM animals
            WHERE id = 0""")

IbmDbTestCase().run_test_000()