# from support.celeryapp import db, encoding
# from support.util import env
from flask import Blueprint, Response, render_template, request, jsonify
from datetime import datetime
import logging

sqlrun_page = Blueprint('sqlrun_page', __name__, template_folder='templates', static_folder='static')

class SqlRunError(Exception):
	status_code = 400
	def __init__(self, message, status_code=None, payload=None):
		Exception.__init__(self)
		self.message = message
		if status_code is not None:
			self.status_code = status_code
		self.payload = payload
	def to_dict(self):
		rv = dict(self.payload or ())
		rv['message'] = self.message
		return rv

# def _sqlrun(sql):
# 	try:
# 		sql = sql.encode(encoding)
# 		# print encoding
# 	except:
# 		logging.critical('encoding-error', exc_info=True)

# 	try:
# 		# cursor = meta_conn.cursor()
# 		# cursor.execute(sql)
# 		rlst = db.engine.execute(sql)
# 	except (sqlalchemy.exc.DatabaseError, cx_Oracle.DatabaseError, cx_Oracle.OperationalError) as e:
# 		logging.critical('failed to run a sql - %s' % sql, exc_info=True)
# 		m = e.message
# 		m = m.decode(encoding)
# 		# m = m.encode('utf-8')
# 		raise SqlRunError(m, status_code=500)
# 	except:
# 		logging.critical('failed to run a sql - %s' % sql, exc_info=True)
# 		raise SqlRunError(e.message, status_code=500)
# 	finally:
# 		#cursor.close()
# 		pass

# 	def _yield(result_set):
# 		# keys = [d[0].decode(meta_conn.encoding) for d in cursor.description]
# 		keys = result_set.keys()
# 		# to tsv_
# 		yield '\t'.join(keys) + '\n'
# 		while True:
# 			# records = cursor.fetchmany()
# 			records = result_set.fetchmany()
# 			if len(records) == 0:
# 				break
# 			for r in records:
# 				# print r
# 				def _conv(x):
# 					if isinstance(x, datetime): return x.strftime("%Y%m%d%H%M%S")
# 					elif isinstance(x, unicode): return x.encode('utf-8')
# 					elif isinstance(x, str): return x.encode('utf-8')
# 					elif x is None: return '0'
# 					else: return str(x)
# 				r = map(_conv, r)
# 				# print r
# 				yield '\t'.join(r) + '\n'

# 	return Response(_yield(rlst), mimetype='text/tsv')

@sqlrun_page.route('/')
def index():
	return render_template('sqlrun.html')

@sqlrun_page.errorhandler(SqlRunError)
def handle_sqlrun_error(error):
	response = jsonify(error.to_dict())
	response.status_code = error.status_code
	return response


@sqlrun_page.route('/_forget/<task_id>')
def forget(task_id):
	from tasks import sqlrun_forget
	sqlrun_forget(task_id)
	return jsonify(ret='ok')

@sqlrun_page.route('/_result/<task_id>', methods=['POST', 'GET'])
def result(task_id):
	from tasks import sqlrun_result
	return jsonify(sqlrun_result(task_id))

# @sqlrun_page.route('/_sqlrun', methods=['GET', 'POST'])
# def sqlrun():
# 	sqltext = request.form.get('sql', None)
# 	if not sqltext: return

# 	target = request.form.get('key', None)
# 	if not target: return

# 	mode = request.form.get('mode')
# 	if not mode: return

# 	async = request.form.get('async', None)

# 	if mode == 'meta':
# 		return _sqlrun(sqltext)
# 	else:
# 		from bpmodules.sqlrun.tasks import sql
# 		instances = env('daemon_instances')
# 		keys = instances.keys()

# 		def _run(conn_str):
# 			sr = sql(unicode(sqltext))
# 			if mode == 'local':
# 				r = sr.run(conn_str)
# 			else: # remote
# 				r = sr.rrun(conn_str, sync=(not async), timeout_sec=10)
# 				# print r
# 				# sqlrun(instance, sql(u'select sysdate from dual')).rrun(sync=True, timeout_sec=600)
# 			# print "%-40s -> %s" % (r['dbname'], r['rows'],)
# 			if async or mode == 'local': pass
# 			elif r['states'] != 'SUCCESS' or r['error']:
# 				raise SqlRunError('[%s] %s' % (r['states'], r['error_msg']), 500)
# 			return r

# 		def _stream(result):
# 			yield '\t'.join(result['columns']) + '\n'
# 			for row in result['rows']:
# 				# print r
# 				def _conv(x):
# 					if isinstance(x, datetime): return x.strftime("%Y%m%d%H%M%S")
# 					elif isinstance(x, unicode): return x.encode('utf-8')
# 					elif isinstance(x, str): return x.encode('utf-8')
# 					elif x is None: return '0'
# 					else: return str(x)
# 				row = map(_conv, row)
# 				# print r
# 				yield '\t'.join(row) + '\n'

# 		try:
# 			conn_str = instances[target].get('dbconn_str', None)
# 		except:
# 			raise SqlRunError('Instance[%s] not found' % target, 500)
# 		if conn_str:
# 			result = _run(conn_str)
# 			if not async:
# 				return Response(_stream(result))
# 			else:
# 				return jsonify(result)
# 		# else:
# 		# 	for key in sorted(keys):
# 		# 		conn_str = instances[key].get('dbconn_str', None)
# 		# 		if not conn_str: continue
# 		# 		_run(conn_str)
# 		return

