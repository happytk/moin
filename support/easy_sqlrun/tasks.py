#-*-encoding:utf-8-*-

"""
SqlRunner


Usage:
- sqlrun('scott/tiger@xe', sql(u'select sysdate from dual')).run()
- sqlrun('scott/tiger@xe', sql(u'select sysdate from dual')).rrun() #async
- sqlrun('scott/tiger@xe', sql(u'select sysdate from dual')).rrun(sync=True, timeout_sec=600)  #sync

- sql(u'select sysdate from dual').run('scott/tiger@xe')
- sql(u'select sysdate from dual').rrun('scott/tiger@xe') #async
- sql(u'select sysdate from dual').rrun('scott/tiger@xe', sync=True, timeout_sec=600)  #sync
- sql(u'select sysdate, :b1 from dual', {u'b1':u'ppp'}).rrun()

- sqlrun_forget(task_id)
- sqlrun_result(task_id)

QuickStart for remote:
- sr = sqlrun('scott/tiger@xe', sql(u'select sysdate from dual'))
- sr.rrun() # getting result or update sattus
- sr.rrun() # ..
- sr.revoke() # cancel job (not working in Windows)
- sr.rrun()
- sr.forget() # delete the result

QuickStart for local:


Issue:
- revoked된 task_id는 다시 수행할 수 없다. (worker에서 메모리로 관리함)

"""

import jsonpickle
import time
import logging
import sys
import pprint
import json
import cx_Oracle
import logging

from urllib import urlencode
from mongo import mongo_lock, singleton
from celery import exceptions as celery_exceptions, current_task
from dbutil import dbconn
from datetime import datetime
# from support.celeryapp import celeryapp

try:
	import config
except ImportError:
	import config_sample as config


class SqlRuntimeError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


@config.celeryapp.task(track_started=True)
def sqlrun_fetchone(conn_str, sql, col_sep='\t', line_sep='\n'):
    conn = cx_Oracle.connect(conn_str)
    curr = conn.cursor()
    curr.execute(sql)
    record = curr.fetchone()
    keys = [d[0].decode(conn.encoding) for d in curr.description]
    vals = [str(d) for d in record]
    ret = []
    ret.append(col_sep.join(keys))
    ret.append(col_sep.join(vals))
    curr.close()
    conn.close()
    return line_sep.join(ret)

@config.celeryapp.task(track_started=True)
def sqlrun_fetchall(conn_str, sql, col_sep='\t', line_sep='\n'):
    conn = cx_Oracle.connect(conn_str)
    curr = conn.cursor()
    curr.execute(sql)
    records = curr.fetchall()
    ret = []
    keys = [d[0].decode(conn.encoding) for d in curr.description]
    ret.append(col_sep.join(keys))
    for record in records:
        vals = [str(d) for d in record]
        ret.append(col_sep.join(vals))
    curr.close()
    conn.close()
    return line_sep.join(ret)


@config.celeryapp.task(track_started=True)
def sqlrun_nofetch(conn_str, sql):
    conn = cx_Oracle.connect(conn_str)
    curr = conn.cursor()
    curr.execute(sql)
    curr.close()
    conn.close()
    return ''


@config.celeryapp.task(track_started=True, name='easy_sqlrun.tasks.sql_run_by_worker')
def sql_run_by_worker(sqlrunner_data):

    class sqlrun_dummy(sqlrun):
        def __init__(self):
            pass

    ## storage check
    SQLRUN_STORAGE = config.easy_sqlrun_storage
    # if SQLRUN_STORAGE == 'mongodb':
    #     from mongo import spawn
    # elif SQLRUN_STORAGE == 'redis':
    # 	import redis
    #     def spawn(): return redis.Redis()
    # else:
    #     assert SQLRUN_STORAGE in ['mongodb', 'redis']

    mongodb = singleton()

    result = []

    have_lock = False

    if SQLRUN_STORAGE == 'mongodb':
        # mongodb = spawn()
        ldb = config.easy_sqlrun_mongodb_lockdb
        lcol = config.easy_sqlrun_mongodb_lock_coll
        my_lock = mongo_lock(mongodb[ldb][lcol], current_task.request.id)
    else:
        my_lock = spawn().lock(current_task.request.id)
    try:
        if SQLRUN_STORAGE == 'mongodb':
            have_lock = my_lock.acquire()
        else:
            have_lock = my_lock.acquire(blocking=False)

        if have_lock:
            sr = sqlrun_dummy()
            sr.from_json(sqlrunner_data)

            ret = sr.run(current_task.request.id) # local
            ret.task_id = current_task.request.id
            ret.async = True

            # logging.critical(ret)
            ret = ret.to_json()
            logging.critical(ret)
            sql_run_by_worker.ignore_result = False

            logging.critical('sqlrun(%s) done.' % (current_task.request.id))
        else:
            ret = None
            sql_run_by_worker.ignore_result = True
            logging.critical('sqlrun(%s) failed(acquring the lock failed.).' % (current_task.request.id))
    finally:
        if SQLRUN_STORAGE == 'mongodb':
            # mongodb.close()
            pass
        if have_lock:
            my_lock.release()

    mongodb.close()

    if ret:
        return ret
    else:
        raise Exception('Already acquired.')

# import jsonpickle
def sqlrun_forget(task_id):
    ret = sql_run_by_worker.AsyncResult(task_id)
    if ret.status == 'SUCCESS' or ret.status == 'PENDING' or ret.status == 'REVOKED':
        # json_str = ret.get()
        # ret_dic = jsonpickle.decode(json_str)
        # query = ret_dic['query']
        # params = ret_dic['params']
        # dbname = ret_dic['dbname']
        ret.forget()

        # _params = {}
        # for k in params: _params[unicode(k)] = unicode(params[k])

        # s = sqlrun.sql(query, _params )
        # #sr = sqlrun.sqlrun(dbname, s)
        # data = s.rrun(dbname, task_id=task_id)
        # print sqlrun.html_table(data).format()
    else:
        pass

# def sqlrun_check(task_id):
#     ret = sql_run_by_worker.AsyncResult(task_id)
#     return ret.status

def sqlrun_result(task_id):
    ret = sql_run_by_worker.AsyncResult(task_id)
    # return json.loads(ret.get())
    if ret.status == 'SUCCESS':
        # get()은 success가 아니면 infinite-waiting이므로
        return json.loads(ret.get())
    else:
        return {'states':ret.status, 'task_id':task_id}


class dict_obj(dict):
    def __setattr__(self, key, value):
        self[key] = value
    def __getattr__(self, key):
        return self[key]
    def to_json(self):
        return jsonpickle.encode(self)
    def from_json(self, json_str):
        dic = jsonpickle.decode(json_str)
        self.update(dic)
    # def __repr__(self):
    #     return super(dict, self).__repr__()

class procedure(dict_obj):
    def __init__(self, code):
        super(procedure, self).__init__()
        self.__build(code)
    def __repr__(self):
        return '<procedure[uid:%s][%s ..]>' % (self.uid, self.__getitem__('code')[:15].encode('ascii', 'ignore'))
    def __get_uid(self):
        import md5
        m = md5.new()
        m.update(self.__getitem__('code').encode('ascii', 'ignore'))
        return m.hexdigest()[:16]
    def __build(self, code):
        _chku = lambda x: isinstance(x, unicode)
        assert _chku(code) and len(code.strip()) > 0
        self.__setitem__('code', code)
        self.__setitem__('uid', self.__get_uid())
        return self
    def run(self, dbname):
        pr = procedure_run(dbname, self)
        return pr.run()
    def rrun(self, dbname, task_id = None, sync=False, timeout_sec=600):
        pr = procedure_run(dbname, self)
        return pr.rrun(task_id, sync=sync, timeout_sec=timeout_sec)


class sql(dict_obj):
    def __init__(self, query, params={}):
        super(sql, self).__init__()
        self.__build(query, params)

    def __repr__(self):
        return '<sql[uid:%s] - %s>' % (self.uid, pprint.pformat(super(sql, self).__repr__(), width=-1))

    def __get_uid(self):
        import md5
        m = md5.new()
        m.update(self.__getitem__('query').encode('ascii', 'ignore'))
        m.update(str(self.__getitem__('params')))
        # m.update(self.__getitem__('dbname'))
        return m.hexdigest()[:16]

    def __build(self, query, params={}):

        _chku = lambda x: isinstance(x, unicode)
        assert _chku(query) and len(query.strip()) > 0
        self.__setitem__('query', query)

        assert all(map(_chku, params))
        self.__setitem__('params', params)

        self.__setitem__('uid', self.__get_uid())
        return self

    @classmethod
    def clear_comments(cls, txt):
        import re
        cstyle_cmt = re.compile("\\'.*?\\'")#, re.MULTILINE | re.DOTALL)
        txt = cstyle_cmt.sub('',txt)

        lnstyle_cmt = re.compile("--.*")
        txt = lnstyle_cmt.sub('', txt)

        #re_string = re.compile("\".*?\"")
        #txt = re_string.sub('', txt)

        return txt

    @classmethod
    def checkBindVars(cls, query):
        import re
        iparams = re.findall(':[a-zA-Z0-9_]+', cls.clear_comments(query))
        iparams = map(lambda x:x[1:], iparams)
        return iparams

    def run(self, dbname):
        sr = sqlrun(dbname, self)
        return sr.run()

    def rrun(self, dbname, task_id = None, sync=False, timeout_sec=600):
        sr = sqlrun(dbname, self)
        return sr.rrun(task_id, sync=sync, timeout_sec=timeout_sec)


class sqlrun(dict_obj):
    def __init__(self, dbname, sqlobj):
        super(sqlrun, self).__init__()
        self.update(sqlobj)

        assert isinstance(dbname, str)
        assert isinstance(sqlobj, sql)

        self.__setitem__('dbname', dbname)
        self.__build()

    def __repr__(self):
        # return '<sqlrun[id:%s][st:%s] - %s>\n-----' % (self.task_id,self.states,pprint.pformat(super(sqlrun, self).__repr__(), width=-1))
        # print dict(super(sqlrun, self))
        # print super(sqlrun, self).__repr__()
        # print super(dict, self).__repr__()
        return '<sqlrun [id:%s] [st:%s]>\n%s\n' % (self.task_id,self.states,pprint.pformat(eval(super(sqlrun, self).__repr__()), width=-1))

    def __get_uid(self):
        import md5
        m = md5.new()
        m.update(self.__getitem__('query').encode('ascii', 'ignore'))
        m.update(self.__getitem__('dbname'))
        m.update(str(self.__getitem__('params')))
        return m.hexdigest()[:16]
    def __build(self):
        self.__setitem__('run', False)
        self.__setitem__('columns', [])
        self.__setitem__('rows', [])
        self.__setitem__('elapsed', 0)
        self.__setitem__('rowcnt', 0)
        self.__setitem__('task_id', None)
        self.__setitem__('gen_time', time.time())
        self.__setitem__('states', '')
        self.start_time = 0
        self.end_time = 0
        self.error = False
        self.error_msg = ''
        import random
        random.seed()
        self.__setitem__('id', str(hex(random.getrandbits(128)))[2:-1])
        self.__setitem__('uid', self.__get_uid())

    def rrun_async(self, task_id = None, expires=60):
        if task_id is None:
            task_id = 'sql_' + self.uid

        ret = sql_run_by_worker.AsyncResult(task_id)
        if ret.status == 'SUCCESS':
            data_from_worker = ret.get()
            if data_from_worker is None:
                self['states'] = 'EXECUTED_BY_ANOTHER_JOB'
                ret.forget()
            else:
                data = dict_obj()
                data.from_json(data_from_worker)
                self.update(data)
                self['states'] = ret.status

        elif ret.status in ('FAILED'):
            self.error = True
            self['states'] = ret.status

        elif ret.status in ('PENDING', 'FAILURE'):
            #http://loose-bits.com/2010/10/distributed-task-locking-in-celery.html
            #http://stackoverflow.com/questions/6998377/celery-standard-method-for-querying-pending-tasks
            # ret = sql_run_by_worker.apply_async((self.to_json(),), {}, task_id=task_id) #eta=datetime.now() + timedelta(minutes=5))#
            # sql_run_by_worker.update_state('WAITING')
            # from celery.app.task import Task
            # Task.update_state(task_id, 'WAITING')
            ret = sql_run_by_worker.apply_async((self.to_json(),), {}, task_id=task_id, expires=expires) #, queue='sqlrun') # expires in 3

            self['states'] = ret.status
        else:
            self['states'] = ret.status

        self['task_id'] = task_id
        self['async'] = True


    def revoke(self, terminate=True, signal='KILL'):
        if self.task_id and self.states in ('PENDING', 'FAILURE', 'STARTED'):
            ret = sql_run_by_worker.AsyncResult(self.task_id)
            ret.revoke(terminate=terminate, signal=signal)

            # mongodb = spawn()
            # my_lock = mongo_lock(mongodb.sqlrun.sqlrun_lock, self.task_id)
            # my_lock.acquire()
            # my_lock.release()
            # mongodb.close()
        else:
            logging.warning("revoke didn't work for [%s] - states:%s" % (self.task_id, self.states))

    def forget(self):
        # if self.task_id and self.states in ('SUCCESS', 'REVOKED'):
        #     ret = sql_run_by_worker.AsyncResult(self.task_id)
        #     ret.forget()
        # else:
        #     logging.warning("forget didn't work for [%s] - states:%s" % (self.task_id, self.states))
        ret = sql_run_by_worker.AsyncResult(self.task_id)
        ret.forget()

    def rrun_sync(self, task_id=None, timeout_sec=600):
        if task_id is None:
            task_id = 'sql_' + self.uid

        loop_cnt = 0

        ret = sql_run_by_worker.AsyncResult(task_id)
        if ret.status == 'SUCCESS':
            data_from_worker = ret.get()
            if data_from_worker is None:
                self['states'] = 'ERROR'
                ret.forget()
            else:
                data = dict_obj()
                data.from_json(data_from_worker)
                self.update(data)
                self['states'] = ret.status

        elif ret.status in ('FAILED'):
            self.error = True
            self['states'] = ret.status

        elif ret.status in ('PENDING', 'FAILURE', 'STARTED'): #pending
            ret = sql_run_by_worker.apply_async((self.to_json(),), {}, task_id=task_id) #, queue='sqlrun')
            try:
                data_from_worker = ret.get(timeout=timeout_sec, interval=1)
                logging.debug('sqlrun-sync-result, %s' % data_from_worker)
            except celery_exceptions.TimeoutError:
                logging.debug('sqlrun-sync-timeouterror, timeout:%d sec.' % timeout_sec)
                data_from_worker = None

            if data_from_worker is None:
                self['states'] = 'TimeoutError'
                # ret.revoke() #not working..........!!!!
                # ret.forget() #not working..........!!!!
            else:
                data = dict_obj()
                data.from_json(data_from_worker)
                self.update(data)
                self['states'] = ret.status
        else:
            self['states'] = ret.status

        self['task_id'] = task_id
        self['async'] = False
        return self

    def rrun(self, task_id=None, sync=False, timeout_sec=600):
        if sync:
            self.rrun_sync(task_id, timeout_sec)
        else:
            self.rrun_async(task_id)
        return self

    def run(self, task_id=''):
        logging.critical('task_id: %s', task_id)
        try:
            self.__run()
        except SqlRuntimeError as e:
            logging.critical('sqlrun[%s][%s] failed. - %s' % (self.dbname, task_id, e.message), exc_info=True)
            self.run = False
            self.error = True
            self.error_msg = str(e.message)
        self['states'] = 'EXECUTED'
        self['task_id'] = task_id
        self['async'] = False
        return self

    def __run(self):

        logging.debug('__run init..')

        # check connection
        # conn_info = getjson('sqlrun-dblist', self.dbname)
        # conn_info = env('daemon_instances').get(self.dbname, None)
        # if conn_info is None:
        #     raise Exception(u'null db object')

        # check bindvars
        binds2chk = []
        for key in self.params:
            self.params[key] = str(self.params[key])
            if len(str(self.params[key]).strip()) == 0:
                binds2chk.append(key)
        if len(binds2chk)>0:
            raise SqlRuntimeError(u'Check bind variables. -> ' + ','.join(binds2chk))

        # check unicode
        _chku = lambda x: isinstance(x, unicode)
        assert _chku(self.query)
        assert all(map(_chku, self.params))

        # connect
        try:
            logging.debug('connect to ' + self.dbname)
            db = dbconn(self.dbname)
        except Exception as e:
            logging.critical('failed to connect to ' + self.dbname)
            raise SqlRuntimeError('failed to connect to ' + self.dbname)

        # run
        try:
            # db = dbconn(conn_info['dbconn_id'], conn_info['dbconn_pw'], conn_info['dbconn_ip'], conn_info['dbconn_port'], conn_info['dbconn_db'], conn_info['dbconn_encoding'])
            self.start_time = time.time()
            self.columns, self.rows = db.select(self.query, self.params)
            self.end_time = time.time()
            self.error = False
        except Exception as e:
            self.error = True
            self.error_msg = str(e.message)
            logging.critical('sqlrun failed.', exc_info=True)
            # print dir(e.args)
            # print dir(e.message)
            # try:
            #     msg = unicode(e.message, self.getEncoding.strip()
            # except:
            #     # msg = 'ora-%d' % e.message.code
            #     msg = e.message
            # raise Exception(e)
            raise SqlRuntimeError(str(e.message))

        self.run = True
        self.elapsed = str(float(self.end_time-self.start_time))
        self.rowcnt = len(self.rows)



class procedure_run(dict_obj):
    def __init__(self, dbname, procedure_obj):
        super(procedure_run, self).__init__()
        self.update(procedure_obj)

        assert isinstance(dbname, str)
        assert isinstance(procedure_obj, procedure)

        self.__setitem__('dbname', dbname)
        self.__build()

    def __repr__(self):
        # return '<procedure_run[id:%s][st:%s] - %s>\n-----' % (self.task_id,self.states,pprint.pformat(super(procedure_run, self).__repr__(), width=-1))
        # print dict(super(procedure_run, self))
        # print super(procedure_run, self).__repr__()
        # print super(dict, self).__repr__()
        return '<procedure_run [id:%s] [st:%s]>\n%s\n' % (self.task_id,self.states,pprint.pformat(eval(super(procedure_run, self).__repr__()), width=-1))

    def __get_uid(self):
        import md5
        m = md5.new()
        m.update(self.__getitem__('code').encode('ascii', 'ignore'))
        m.update(self.__getitem__('dbname'))
        return m.hexdigest()[:16]
    def __build(self):
        self.__setitem__('run', False)
        self.__setitem__('columns', [])
        self.__setitem__('rows', [])
        self.__setitem__('elapsed', 0)
        self.__setitem__('rowcnt', 0)
        self.__setitem__('task_id', None)
        self.__setitem__('gen_time', time.time())
        self.__setitem__('states', '')
        self.start_time = 0
        self.end_time = 0
        self.error = False
        self.error_msg = ''
        import random
        random.seed()
        self.__setitem__('id', str(hex(random.getrandbits(128)))[2:-1])
        self.__setitem__('uid', self.__get_uid())

    def rrun_async(self, task_id = None, expires=60):
        if task_id is None:
            task_id = 'procedure_' + self.uid

        ret = procedure_run_by_worker.AsyncResult(task_id)
        if ret.status == 'SUCCESS':
            data_from_worker = ret.get()
            if data_from_worker is None:
                self['states'] = 'EXECUTED_BY_ANOTHER_JOB'
                ret.forget()
            else:
                data = dict_obj()
                data.from_json(data_from_worker)
                self.update(data)
                self['states'] = ret.status

        elif ret.status in ('FAILED'):
            self.error = True
            self['states'] = ret.status

        elif ret.status in ('PENDING', 'FAILURE'):
            #http://loose-bits.com/2010/10/distributed-task-locking-in-celery.html
            #http://stackoverflow.com/questions/6998377/celery-standard-method-for-querying-pending-tasks
            # ret = procedure_run_by_worker.apply_async((self.to_json(),), {}, task_id=task_id) #eta=datetime.now() + timedelta(minutes=5))#
            # procedure_run_by_worker.update_state('WAITING')
            # from celery.app.task import Task
            # Task.update_state(task_id, 'WAITING')
            ret = procedure_run_by_worker.apply_async((self.to_json(),), {}, task_id=task_id, expires=expires) #, queue='sqlrun') # expires in 3

            self['states'] = ret.status
        else:
            self['states'] = ret.status

        self['task_id'] = task_id
        self['async'] = True


    def revoke(self, terminate=True, signal='KILL'):
        if self.task_id and self.states in ('PENDING', 'FAILURE', 'STARTED'):
            ret = procedure_run_by_worker.AsyncResult(self.task_id)
            ret.revoke(terminate=terminate, signal=signal)

            # mongodb = spawn()
            my_lock = mongo_lock(mongodb.sqlrun.sqlrun_lock, self.task_id)
            my_lock.acquire()
            my_lock.release()
            # mongodb.close()
        else:
            logging.warning("revoke didn't work for [%s] - states:%s" % (self.task_id, self.states))

    def forget(self):
        if self.task_id and self.states in ('SUCCESS', 'REVOKED'):
            ret = procedure_run_by_worker.AsyncResult(self.task_id)
            ret.forget()
        else:
            logging.warning("forget didn't work for [%s] - states:%s" % (self.task_id, self.states))

    def rrun_sync(self, task_id=None, timeout_sec=600):
        if task_id is None:
            task_id = 'sql_' + self.uid

        loop_cnt = 0

        ret = procedure_run_by_worker.AsyncResult(task_id)
        if ret.status == 'SUCCESS':
            data_from_worker = ret.get()
            if data_from_worker is None:
                self['states'] = 'ERROR'
                ret.forget()
            else:
                data = dict_obj()
                data.from_json(data_from_worker)
                self.update(data)
                self['states'] = ret.status

        elif ret.status in ('FAILED'):
            self.error = True
            self['states'] = ret.status

        elif ret.status in ('PENDING', 'FAILURE', 'STARTED'): #pending
            ret = procedure_run_by_worker.apply_async((self.to_json(),), {}, task_id=task_id) #, queue='sqlrun')
            try:
                data_from_worker = ret.get(timeout=timeout_sec, interval=1)
                logging.debug('procedure-run-sync-result, %s' % data_from_worker)
            except celery_exceptions.TimeoutError:
                logging.debug('procedure-run-sync-timeouterror, timeout:%d sec.' % timeout_sec)
                data_from_worker = None

            if data_from_worker is None:
                self['states'] = 'TimeoutError'
                # ret.revoke() #not working..........!!!!
                # ret.forget() #not working..........!!!!
            else:
                data = dict_obj()
                data.from_json(data_from_worker)
                self.update(data)
                self['states'] = ret.status
        else:
            self['states'] = ret.status

        self['task_id'] = task_id
        self['async'] = False
        return self

    def rrun(self, task_id=None, sync=False, timeout_sec=600):
        if sync:
            self.rrun_sync(task_id, timeout_sec)
        else:
            self.rrun_async(task_id)
        return self

    def run(self, task_id=''):
        try:
            self.__run()
        except Exception as e:
            logging.critical('procedure-run[%s] failed. - %s' % (task_id, e.message), exc_info=True)
            self.run = False
            self.error = True
            self.error_msg = e.message
        self['states'] = 'EXECUTED'
        self['task_id'] = task_id
        self['async'] = False
        return self

    def __run(self):

        # # check connection
        # # conn_info = getjson('sqlrun-dblist', self.dbname)
        # conn_info = env('daemon_instances').get(self.dbname, None)
        # if conn_info is None:
        #     raise Exception(u'null db object')

        # check unicode
        _chku = lambda x: isinstance(x, unicode)
        assert _chku(self.code)

        # connect
        try:
            # db = dbconn(conn_info['dbconn_str'])
            db = dbconn(self.dbname)
        except Exception as e:
            logging.critical('failed to connect to ' + self.dbname)
            raise Exception('failed to connect to ' + self.dbname)

        # run
        try:
            # db = dbconn(conn_info['dbconn_id'], conn_info['dbconn_pw'], conn_info['dbconn_ip'], conn_info['dbconn_port'], conn_info['dbconn_db'], conn_info['dbconn_encoding'])
            self.start_time = time.time()
            self.result = db.proc_exec(self.code)
            self.end_time = time.time()
        except Exception as e:
            self.error = True
            # logging.critical('sqlrun failed.')#, exc_info=True)
            msg = unicode(e.message, db.getEncoding()).strip()
            raise Exception(msg)

        self.error = True
        self.run = True
        self.elapsed = str(float(self.end_time-self.start_time))




class html_object_from_svr:
    def __init__(self, sqlrun_obj):
        self.data = sqlrun_obj

        #properties
        self.show_toolbox = False
        self.show_sql = False
        self.show_info = False

    def format(self):
        result = []

        result.append('<div>')
        result.append('<small><small>')
        result.append('''&nbsp;<a href="javascript:display_toggle('mmq_toolbox_%(hash)s');">sqlrun_info</a> %(gen)s %(task_id)s
<span id="mmq_toolbox_%(hash)s" style="display: none;">
<a href="javascript:proc_http_param('%(async_confirm_url)s', '%(async_confirm_url_param)s', document.getElementById('mmq_rst_%(hash)s'));">status check</a> |
<a href="javascript:proc_http_param('%(forget_url)s', '%(forget_url_param)s', document.getElementById('mmq_rst_%(hash)s'));">forget</a> |
<a href="javascript:proc_http_param('%(cancel_url)s', '%(cancel_url_param)s', document.getElementById('mmq_rst_%(hash)s'));">cancel</a>
<pre>%(data_query)s</pre>
<pre>%(data)s</pre>
</span>''' % {
                'hash':self.data['id'],
                'data':'\n'.join(['%s:%s' % (key,self.data[key]) for key in self.data.keys() if key not in ['rows','query']]),
                'data_query':self.data['query'],
                'task_id':self.data['task_id'],
                'gen':time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(self.data['gen_time']))),
                'async_confirm_url': '/__async_sqlrun_status',
                'async_confirm_url_param':urlencode({'action':'pythonruntime',
                                    'task_id': self.data['task_id'] if 'task_id' in self.data else ''}),
                'forget_url': '/__async_sqlrun_forget',
                'forget_url_param': urlencode({'action':'pythonruntime',
                                    'task_id': self.data['task_id'] if 'task_id' in self.data else ''}),
                'cancel_url': '/__async_sqlrun_revoke',
                'cancel_url_param': urlencode({'action':'pythonruntime',
                                    'task_id': self.data['task_id'] if 'task_id' in self.data else ''}),
        })
        result.append('</small></small>')

        if self.data.error:
            #error handling
            result.append('<div id="mmq_rst_%s">' % self.data.id)
            result.append('<font color="red">')
            result.append('&nbsp;Failed to construct the data. (msg: %s)' % (self.data.error_msg))
            result.append('</font>')
            result.append('</div>')
        elif not self.data.run:
            result.append('<div id="mmq_rst_%s">' % self.data.id)
            if self.data.task_id is None:
                result.append('&nbsp;Not started yet.')
            else:
                result.append('&nbsp;Generating.. (status:' + self.data.states + ')')
            result.append('</div>')
        else:
            # if self.show_sql:     result.append(self.build_sql())
            # if self.show_toolbox: result.append(self.build_toolbox())
            result.append('<div id="mmq_rst_%s">' % self.data.id)
            result.append(self.build_object())
            result.append('</div>')
            # if self.show_info:    result.append(self.build_info())
        result.append('</div>')
        return ''.join(result)


    def build_sql(self):
        # if show_sql:
        #     show_sql_cssstyle = "display:"
        # else:
        #     show_sql_cssstyle = "display:none"

        return '''<div id="mmq_sql_%s" style="%s"><pre>%s</pre></div>''' % (self.data['id'], '', self.data.query)

    def build_toolbox(self):
        import cgi
        from urllib import urlencode

        ### params
        params = {
            'hash':self.data['id'],
            'params':cgi.escape(str(self.data['params'])) if len(self.data['params'])>0 else '',
            #'hard_copy_form':self.get_hard_copy_form(macro),
            'sqlrun_url': '',
            'sqlrun_url_param': urlencode({'action':'sqlrun',
                                      'dbins':self.data['dbname'],
                                      #'options': ','.join(self.options),
                                      'dbqry':unicode(self.data['query']).encode('utf8')}),
            'async_confirm_url': '',
            'async_confirm_url_param':urlencode({'action':'sqlrun_async',
                                'task_id': self.data['task_id'] if 'task_id' in self.data else ''}),
            'task_id': self.data['task_id'] if 'task_id' in self.data else 'None',
            'forget_url': '/__async_sqlrun_forget',
            'forget_url_param': urlencode({'action':'pythonruntime',
                                'task_id': self.data['task_id'] if 'task_id' in self.data else ''}),
            'toolbox_css':'',
        }

        result = []
        result.append("""
<script type="text/javascript">
function execute_q%(hash)s () {
    proc_http_param('%(sqlrun_url)s',
                    '%(sqlrun_url_param)s',
                    document.getElementById('mmq_rst_%(hash)s'));
}
function async_q%(hash)s () {
    proc_http_param('%(async_confirm_url)s',
                    '%(async_confirm_url_param)s',
                    document.getElementById('mmq_rst_%(hash)s'));
}
function forget_q%(hash)s () {
    proc_http_param('%(forget_url)s',
                    '%(forget_url_param)s',
                    document.getElementById('mmq_rst_%(hash)s'));
}
</script>""" % params)

        result.append('''<div id="toolbox" style="%(toolbox_css)s">''' % params)
        if self.show_sql:
            result.append('''<a href="javascript:display_toggle('mmq_sql_%(hash)s');">TOGGLE SQL</a> %(params)s |''' % params)
        if self.data.async:
            result.append('''<a href="javascript:forget_q%(hash)s();">DELETE-BACKEND-DATA</a> |
<a href="javascript:async_q%(hash)s();">CHECK RESULT (id: %(task_id)s)</a>''' % params)
        else:
            result.append('''<a href="javascript:execute_q%(hash)s();">RE-EXECUTE</a>''' % params)
        result.append('</div>')

        return '\n'.join(result)


    def build_info(self):
        return '''<div>[%s] Elapsed <b>%ss</b>,
Executed at <b>%s</b>,
Record count: <b>%d</b></div>''' % (self.data['states'], self.data['elapsed'], self.data['dbname'], self.data['rowcnt'])

    def build_object(self):
        raise Exception('Not implemented')

class html_table_from_svr(html_object_from_svr):

    def __init__(self, sqlobj):
        html_object_from_svr.__init__(self, sqlobj)
        self.show_table_header = True
        self.wrap_funcs = percee_util.get_percee_resource_link_wrapfuncs(self.data.columns)

    def build_object(self):
        result = []
        result.append('<table>')

        #header
        if self.show_table_header:
            result.append('<tr>')
            for col in self.data.columns:
                result.append('<td>')
                #result.append(unicode(str(l), 'euc-kr'))
                result.append(unicode(col))
                result.append('</td>')
            result.append('</tr>')

        #data
        if len(self.data.rows) > 0:
            for row in self.data.rows:
                result.append('<tr>')
                for i in range(0, len(self.data.columns)):

                    try:
                        s = unicode(row[i])
                        #result.append(unicode(str(l[i]), 'euc-kr'))
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        #x = l[i]
                        #x = x.decode('euc-kr','ignore')
                        #x = x.encode('utf-8')
                        #result += x
                        traceback.print_exc(file=sys.stdout)

                    result.append('<td>')
                    if self.wrap_funcs is not None:
                        result.append(self.wrap_funcs[i](s))
                    else:
                        result.append(s)
                    result.append('</td>')
                result.append('</tr>')
        else:
            result.append('<tr><td colspan="%d" align="center"><i>No entries.</i></td></tr>' % len(self.data.columns))
        result.append('</table>')
        return '\n'.join(result)

class html_chart:
    def __init__(self, sqlobj, width='99%', height='400px'):
        self.sqlobj = sqlobj
        self.width = width
        self.height = height
    def format(self, show_form=True):
        return '''<div id="chart_%s" style="width:%s;height:%s;"></div>
<script type="text/javascript">
var res = %s;
graphy('#chart_%s', res, %s);
</script>''' % (self.sqlobj.id,
                self.width,
                self.height,
                self.sqlobj.to_json(), self.sqlobj.id, ('false', 'true')[show_form])


class html_table_refresh:
    def __init__(self, sqlobj):
        self.sqlobj = sqlobj
    def format(self):
        return '''<div id="table_%s"></div>
<script type="text/javascript">
var res = %s;
tabulate_refresh('#table_%s', res, 10000);
</script>''' % (self.sqlobj.id,
                self.sqlobj.to_json(), self.sqlobj.id)
    def format_with_id(self, div_id):
        return '''<script type="text/javascript">
var res = %s;
tabulate_refresh('%s', res, 10000);
</script>''' % (self.sqlobj.to_json(), div_id)


class html_table:
    def __init__(self, sqlobj):
        self.sqlobj = sqlobj
    def format(self, show_form=True):
        return '''<div id="table_%s"></div>
<script type="text/javascript">
var res = %s;
tabulate('#table_%s', res, %s);
</script>''' % (self.sqlobj.id,
                self.sqlobj.to_json(), self.sqlobj.id, ('false', 'true')[show_form])

class html_chart_from_svr(html_object_from_svr):

    def __init__(self, sqlobj):
        html_object_from_svr.__init__(self, sqlobj)
        self.column_selection_data = None # means all
        self.column_selection_xaxis = None # no column record
        self.custom_script = ''
        self.width = '99%'
        self.height = '400px'

    def build_autogen_chart(self):

        # data selection
        if self.column_selection_data is None \
            or type(self.column_selection_data) != type([]):
            data_column_selection = range(0, len(self.data['columns']))
            if self.column_selection_xaxis is not None:
                data_column_selection.remove(self.column_selection_xaxis)
        else:
            data_column_selection = self.column_selection_data

        # making cols
        if self.column_selection_xaxis is not None:
            cols = [[idx, str(row[self.column_selection_xaxis])] \
                        for idx, row in enumerate(self.data.rows)]
        else:
            cols = []

        # making data
        vals = []
        for column_index in data_column_selection:
            vals.append([[idx, str(row[column_index])] \
                        for idx, row in enumerate(self.data.rows)])

        # chart script
        result = []
        result.append('''<div id="placeholder_''' + self.data['id'] + '''"
style="width:''' + str(self.width) + ''';height:''' + str(self.height) + '''"></div>
<script type="text/javascript">
$(function () {
    var placeholder = $("#placeholder_''' + str(self.data['id']) + '''");
    ''')

        val_delcaration_list = []
        for idx, val_list in enumerate(vals):
            result.append('var d%02d = %s;' % (idx+1, str(val_list)))
            val_delcaration_list.append('d%02d' % (idx+1))


        result.append('''
    var plot = $.plot(placeholder, [''' + ','.join(val_delcaration_list) + '''], {''')

        if len(cols) > 0:
            result.append('''
            xaxis: {
                ticks: ''' + str(cols) + '''
            },''')

        result.append('''
            series: {
                   lines: { show: true },
                   points: { show: true }
            },
            grid: { hoverable: true, clickable: true },
        });''')

        result.append('''
    function showTooltip(x, y, contents) {
        $('<div id="tooltip">' + contents + '</div>').css( {
            position: 'absolute',
            display: 'none',
            top: y + 5,
            left: x + 20,
            border: '1px solid #fdd',
            padding: '2px',
            'background-color': '#fee',
            opacity: 0.80
        }).appendTo("body").fadeIn(200);
    }

    var previousPoint = null;
    placeholder.bind("plothover", function (event, pos, item) {
        $("#x").text(pos.x.toFixed(2));
        $("#y").text(pos.y.toFixed(2));

        if (item) {
            if (previousPoint != item.dataIndex) {
                previousPoint = item.dataIndex;

                $("#tooltip").remove();
                var x = item.datapoint[0].toFixed(2),
                    y = item.datapoint[1].toFixed(2);

                showTooltip(item.pageX, item.pageY, String(parseInt(y)));
                            //item.series.label + " of " + x + " = " + y);
            }
        }
        else {
            $("#tooltip").remove();
            previousPoint = null;
        }
    }); //end of placeholder.bind()
});
</script>''')

        return '\n'.join(result)


    def build_autogen_time_chart(self):

        # data selection
        if self.column_selection_data is None \
            or type(self.column_selection_data) != type([]):
            data_column_selection = range(0, len(self.data['columns']))
            if self.column_selection_xaxis is not None:
                data_column_selection.remove(self.column_selection_xaxis)
        else:
            data_column_selection = self.column_selection_data

        # making cols
        if self.column_selection_xaxis is not None:
            cols = [[idx, str(row[self.column_selection_xaxis])] \
                        for idx, row in enumerate(self.data.rows)]
        else:
            cols = []

        # time column (yyyymmdd)
        time_col_index = self.data.columns.index('YYYYMMDD')
        if time_col_index in data_column_selection:
            data_column_selection.remove(time_col_index)

        # chart script
        result = []
        result.append('''<div id="placeholder_''' + self.data['id'] + '''"
style="width:''' + str(self.width) + ''';height:''' + str(self.height) + '''"></div>
<script type="text/javascript">
$(function () {
    var placeholder = $("#placeholder_''' + str(self.data['id']) + '''");
    ''')

        # making data
        val_delcaration_list = []
        for column_index in data_column_selection:
            # for row in self.data.rows:
            #     print str(int(time.mktime(datetime.strptime(row[time_col_index], "%Y%m%d").timetuple())))
            #     print str(row[column_index])
            rr = ["[%d000,%d]" % (time.mktime(datetime.strptime(row[time_col_index], "%Y%m%d").timetuple()), # bad
                    int(row[column_index])) for row in self.data.rows]

            result.append('    var %s = [%s];' % (self.data.columns[column_index], ",".join(rr)))
            val_delcaration_list.append(self.data.columns[column_index])

        result.append('''    var data = [''')
        data_result = []
        for d in val_delcaration_list:
            data_result.append('''{
            label: '%s',
            data: %s,
            lines: { show: true, fill: false }
        }
        ''' % (d,d))
        result.append(','.join(data_result))
        result.append('''];
    var plot = $.plot(placeholder, data, {
        xaxis: {
            mode: "time"
        },
        series: {
               lines: { show: true },
               points: { show: false }
        },
        grid: { hoverable: true, clickable: true },
        });''')

        result.append('''
    function showTooltip(x, y, contents) {
        $('<div id="tooltip">' + contents + '</div>').css( {
            position: 'absolute',
            display: 'none',
            top: y + 5,
            left: x + 20,
            border: '1px solid #fdd',
            padding: '2px',
            'background-color': '#fee',
            opacity: 0.80
        }).appendTo("body").fadeIn(200);
    }
//null means this operation is working now..
    var previousPoint = null;
    placeholder.bind("plothover", function (event, pos, item) {
        $("#x").text(pos.x.toFixed(2));
        $("#y").text(pos.y.toFixed(2));

        if (item) {
            if (previousPoint != item.dataIndex) {
                previousPoint = item.dataIndex;

                $("#tooltip").remove();
                var x = item.datapoint[0].toFixed(2),
                    y = item.datapoint[1].toFixed(2);

                showTooltip(item.pageX, item.pageY, String(parseInt(y)) + ' at ' + new Date(parseInt(x)));
                            //item.series.label + " of " + x + " = " + y);
            }
        }
        else {
            $("#tooltip").remove();
            previousPoint = null;
        }
    }); //end of placeholder.bind()
});
</script>''')

        return '\n'.join(result)

    def build_object(self):
        result = []
        if len(self.custom_script) == 0:
            if 'YYYYMMDD' in self.data['columns']:
                result.append(self.build_autogen_time_chart())
            else:
                result.append(self.build_autogen_chart())
        else:
            try:
                cols = [str(col) for col in self.data['columns']]
                vals = [map(str, row) for row in self.data['rows']]
                ret = []
                for idx, col in enumerate(cols):
                    ret.append('var %s = %s;' % (col, str([val[idx] for val in vals])))
                #javascript build

                define_vars = '\n'.join(ret)
            except ValueError:
                define_vars = ''

            if len(define_vars) > 0:
                result.append('''
<div id="placeholder_''' + self.data['id'] + '''" style="width:95%;height:400px;"></div>
<script type="text/javascript">
$(function () {

    ''' + define_vars + '''

    var data = [];
    var options = {};
    var placeholder = $("#placeholder_''' + self.data['id'] + '''");

    ''' + self.custom_script + '''

    var plot = $.plot(placeholder, data, options);
});
</script>''')
        return '\n'.join(result)

def sqlsrun_id_refresh(task_id, db, q, **kw):
    ret = sql_run_by_worker.AsyncResult(task_id)
    if ret.status == 'SUCCESS':
        # print 'deleting cache..'
        ret.forget()
    # print q
    # print kw
    return sqlsrun_id(task_id, db, q, **kw)

def sqlarun_id_refresh(task_id, db, q, **kw):
    ret = sql_run_by_worker.AsyncResult(task_id)
    if ret.status == 'SUCCESS':
        # print 'deleting cache..'
        ret.forget()
    return sqlarun_id(task_id, db, q, **kw)

def sqlsrun_id(task_id, db, q, **kw):
    return sqlrun(db, sql(q, **kw)).run_sync(task_id)

def sqlarun_id(forget_first, task_id, db, q, **kw):
    return sqlrun(db, sql(q, **kw)).run_async(task_id)

def sqlsrun(db, q, **kw):
    return sqlrun(db, sql(q, **kw)).run_sync()

def sqlarun(db, q, **kw):
    return sqlrun(db, sql(q, **kw)).run_async()

def sqlarun_html_chart(db, q, **kw):
    return html_chart(sqlrun(db, sql(q, **kw)).run_async())

def sqlarun_html_table(db, q, **kw):
    return html_table(sqlrun(db, sql(q, **kw)).run_async())

def sqlsrun_html_chart(db, q, **kw):
    return html_chart(sqlrun(db, sql(q, **kw)).run_sync())

def sqlsrun_html_table(db, q, **kw):
    return html_table(sqlrun(db, sql(q, **kw)).run_sync())


# def wsgiapp(environ, start_response):
#     #expected actions - forget, refresh, result
#     try:
#         qs = parse_qs(environ['QUERY_STRING'])
#         k = qs.get('k', ['deacon_ukyp6'])[0] #instance key
#         if ord('0') <= ord(k[-1]) <= ord('9'):
#             instances = [k]
#             c = 1
#         else:
#             c = int(qs.get('c', [2])[0]) #instance count
#             instances = instance_keys(k, c)

#         dk = qs.get('dk', [None])[0]
#         sk = qs.get('sk', [None])[0]
#         b = qs.get('b', ['000000'])[0]
#         e = qs.get('e', ['235959'])[0]

#         if k and dk:
#             n = qs.get('n', [None])[0] #time
#             if n is None:
#                 n = datetime.today() - timedelta(days=1)
#                 n = n.strftime("%Y%m%d")
#             if sk is None:
#                 sk = dk
#             s = int(qs.get('s', [1])[0])
#             response_body = referenced_tsv(instances, dk, sk, n, s, b, e)
#         else:
#             response_body = ''
#     except:
#         response_body = ''
#         print traceback.format_exc()

#     status = '200 OK'
#     response_headers = [('Content-Type', 'text/plain'),
#                    ('Content-Length', str(len(response_body)))]
#     start_response(status, response_headers)
#     return [str(response_body)]

def test():
    import random
    ri = random.randint(1, 10000)
    query = 'select sysdate, :temp, %d from dual' % ri
    print sql(query, temp="123").run('xe')

if __name__ == "__main__":
    test()

    #connection test
    # for conn_name in DB_CS:
    #     print conn_name, DB_CS[conn_name].select('select sysdate from dual')

