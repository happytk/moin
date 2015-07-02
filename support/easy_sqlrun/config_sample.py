


easy_sqlrun_storage = 'mongodb'

easy_sqlrun_mongodb_host = '150.20.21.196' #localhost'
easy_sqlrun_mongodb_port = 27017

easy_sqlrun_mongodb_lockdb = 'sqlrun'
easy_sqlrun_mongodb_lock_coll = 'sqlrun_lock'


# for remote run

from celery import Celery
celeryapp = Celery('sqlrun')
celeryapp.conf.update(
	CELERY_TASK_SERIALIZER='json',
	CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml'],
	BROKER_URL = 'mongodb://%s:%d/%s' % (mongodb_host, mongodb_port, mongodb_lockdb),
	CELERY_RESULT_BACKEND = 'mongodb://%s:%d/%s' % (mongodb_host, mongodb_port, mongodb_lockdb),
	CELERY_ENABLE_UTC=False,
	USE_TZ = False,
	CELERY_IMPORTS = ('tasks',),#INCLUDE = ('easy_sqlrun.tasks.sql_run_by_worker'),
)
