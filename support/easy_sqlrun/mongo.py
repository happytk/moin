#-*- encoding:utf-8 -*-
import time
import logging
import datetime
import pymongo
import socket
import os

try:
	import config
except ImportError:
	import config_sample as config

# from liufei.util import env
# 'mongodb://150.204.22.84:65060/ptree_orcl'
_server = config.easy_sqlrun_mongodb_host
_port   = config.easy_sqlrun_mongodb_port

_configured = False
mongo = None
# mongo = Connection(_server, _port)

def spawn():
	# return pymongo.Connection(_server, _port)
	return singleton()

def _spawn():
	global _configured, mongo
	logging.critical('mongodb connection is established.(pid:%d)' % os.getpid())
	mongo = pymongo.Connection(_server, _port)
	_configured = True

def singleton():
	global _configured, mongo
	if not _configured:
		_spawn()
	return mongo

#lock implemenation alike redis-lock
class mongo_lock:
    def __init__(self, collection, id):
        self.collection = collection
        self.id = id
        self.lock_doc = None
    def acquire(self):
        doc = self.collection.find_one({'id':self.id})
        if doc:
            return False
        else:
            self.lock_doc = self.collection.find_and_modify(query={'id':self.id}, update={'$set':{'using':True, 'id':self.id}}, upsert=True, new=True)
            return True
    def release(self):
        if self.lock_doc:
            self.collection.remove({'_id':self.lock_doc['_id']})

"""
>>> import logging
>>> logger = logging.getLogger(__name__)
>>> logger = MongoLoggingAdapter(logger, {'db':spawn()['ptree']['log']})
"""
class MongoLoggingAdapter(logging.LoggerAdapter):
	# debug(), info(), warning(), error(), exception(), critical() and log().
	def critical(self, msg, *args, **kwargs):
		"""
		Delegate a debug call to the underlying logger, after adding
		contextual information from this adapter instance.
		"""
		self.extra['db'].insert({'msg': msg % kwargs, 'name': self.logger.name, 'level':'critical', 'reg_dt': datetime.datetime.today(), 'host': socket.gethostname(), 'pid': os.getpid()})
		msg, kwargs = self.process(msg, kwargs)
		self.logger.critical(msg, *args, **kwargs)
	def error(self, msg, *args, **kwargs):
		self.extra['db'].insert({'msg': msg % kwargs, 'name': self.logger.name, 'level':'error', 'reg_dt': datetime.datetime.today(), 'host': socket.gethostname(), 'pid': os.getpid()})
		msg, kwargs = self.process(msg, kwargs)
		self.logger.error(msg, *args, **kwargs)
	def fatal(self, msg, *args, **kwargs):
		self.extra['db'].insert({'msg': msg % kwargs, 'name': self.logger.name, 'level':'fatal', 'reg_dt': datetime.datetime.today(), 'host': socket.gethostname(), 'pid': os.getpid()})
		msg, kwargs = self.process(msg, kwargs)
		self.logger.fatal(msg, *args, **kwargs)
	def info(self, msg, *args, **kwargs):
		self.extra['db'].insert({'msg': msg % kwargs, 'name': self.logger.name, 'level':'info', 'reg_dt': datetime.datetime.today(), 'host': socket.gethostname(), 'pid': os.getpid()})
		msg, kwargs = self.process(msg, kwargs)
		self.logger.info(msg, *args, **kwargs)
	# def debug(self, msg, *args, **kwargs):
	# 	self.extra['db'].insert({'msg': msg % kwargs, 'name': self.logger.name, 'level':'debug', 'reg_dt': datetime.datetime.today(), 'host': socket.gethostname(), 'pid': os.getpid()})
	# 	msg, kwargs = self.process(msg, kwargs)
	# 	self.logger.debug(msg, *args, **kwargs)
	# 모든 call이 참고한다.
	def process(self, msg, kwargs):
		# self.extra['db'].insert({'msg': msg % kwargs, 'reg_dt': datetime.datetime.today()})
		return msg, kwargs
		# return '[%s] %s' % (self.extra['db'], msg), kwargs

def make_capped_collection(database, collection_name, size):
	assert isinstance(database,  pymongo.database.Database)
	if collection_name in database.collection_names():
		database.command({'convertToCapped':collection_name, 'size': size})

# def config_get(section, key, default):
# 	spawn()[section][key]


# mongodb에서 사용할 수 있는 config-object
class mconfig:
	def __init__(self, dbname='spike'):
		self.conn = spawn()
		self.dbname = dbname
		self._cached = {}
	def close(self): self.conn.close()
	def get(self, section, key, default=None, refresh=False):
		_k = section + key
		if not refresh and _k in self._cached:
			return self._cached[_k]

		ret = self.conn[self.dbname][section].find_one(dict(_id=key))
		if ret and '_val' in ret:
			self._cached[_k] = ret['_val']
			return ret['_val']
		else:
			logging.warning('mongo-configuration-module(%s)(%s) cannot get the %s. use the default: %s' % (self.dbname, section, key, str(default)))
			return default
	def set(self, section, key, value):
		self.conn[self.dbname][section].find_and_modify(dict(_id=key), upsert=True, new=True, update={'$set':dict(time=time.time(), _val=value)})

