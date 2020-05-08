import pymonetdb
from pymonetdb import Error as PyMonetdbErr
from pymonetdb.sql import monetize
import configparser
import os

config = configparser.ConfigParser()
dir_ = os.path.dirname(__file__)
configuration = os.path.join(dir_, 'mroll.ini')
config.read(configuration)
db_name = config['db']['db_name']
user = config['db']['user']
password = config['db']['password']
port = config['db']['port']
tbl_name = monetize.convert(config['mroll']['rev_history_tbl_name']).replace('\'', '\"')


def get_head(db_name=db_name, tbl_name=tbl_name):
    rev = None
    conn = pymonetdb.connect(db_name, port=port, username=user, password=password)
    try:
        sql = "select id, description, ts from {} as r where r.ts=(select max(ts) from {})".format(tbl_name, tbl_name)
        curr = conn.cursor()
        curr.execute(sql)
        rev = curr.fetchone()
    finally:
        conn.close()
    return rev

def create_revisions_table(db_name=db_name, tbl_name=tbl_name):
    conn = pymonetdb.connect(db_name, port=port, username=user, password=password)
    sql = """
    create table if not exists {}(id string, description string, ts timestamp);
    alter table {} add constraint mroll_rev_pk primary key (id);
    """.format(tbl_name, tbl_name)
    try:
        conn.execute(sql)
        conn.commit()
        return True
    except PyMonetdbErr as e:
        conn.rollback()
        raise(e)    
    finally:
        conn.close()
    return False

def get_revisions(db_name=db_name, tbl_name=tbl_name):
    conn = pymonetdb.connect(db_name, port=port, username=user, password=password)
    sql = "select id, description, ts from {} order by ts".format(tbl_name)
    cur = conn.cursor()
    try:
        cur.execute(sql)
        return cur.fetchall()
    finally:
        conn.close()

def add_revision(id_, description, ts, upgrade_sql, db_name=db_name, tbl_name=tbl_name):
    """
    Applies the upgrade sql and adds it to meta data in one transaction
    """
    conn = pymonetdb.connect(db_name, port=port, username=user, password=password)
    sql = """
    insert into {} values ('{}', '{}', '{}')
    """.format(tbl_name, id_, description, ts)
    try:
        conn.execute(upgrade_sql)
        conn.execute(sql)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise(e)
    finally:
        conn.close()
    return False

def remove_revision(id_, downgrade_sql, db_name=db_name, tbl_name=tbl_name):
    conn = pymonetdb.connect(db_name, port=port, username=user, password=password)
    sql = "delete from {} where id='{}'".format(tbl_name, id_)
    try:
        conn.execute(downgrade_sql)
        conn.execute(sql)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise(e)
    finally:
        conn.close()
    return False
