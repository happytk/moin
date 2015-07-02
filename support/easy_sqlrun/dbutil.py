import logging
from datetime import datetime


try:
    import cx_Oracle
    class dbconn():
        # def __init__(self, id, passwd, ip, port, db, db_encoding='cp949'):
        def __init__(self, conn_str):
            self.conn_str = conn_str
            # self.id = id
            # self.passwd = passwd
            # self.ip = ip
            # self.port = port
            # self.db = db
            # self.dsn = cx_Oracle.makedsn(self.ip, self.port, self.db)
            self.encoding = "cp949"
        def getConn(self):
            conn = cx_Oracle.connect(self.conn_str)
            # self.encoding = conn.encoding
            logging.debug('%s - encoding: %s', self.conn_str, self.encoding)
            return conn
        def proc_exec(self, code):
            conn = self.getConn()
            curr = conn.cursor()
            curr.callproc("dbms_output.enable")

            try:
                curr.callproc(str(code))
                # get the procedure result
                ret = []
                statusVar = curr.var(cx_Oracle.NUMBER)
                lineVar = curr.var(cx_Oracle.STRING)
                while True:
                    curr.callproc("dbms_output.get_line", (lineVar, statusVar))
                    if statusVar.getvalue() != 0:
                        break
                    ret.append(lineVar.getvalue())
                    cx_Oracle.OperationalError
            except cx_Oracle.OperationalError as e:
                # operational error는 여기서 처리할 수 없다.
                raise e
            except Exception as e:
                # connection에는 문제가 없으나
                # package maintenance 등으로 인한 오류일 수 있음. 시간지연시킨 후 다시 시도
                logging.critical('DB Call error - %s' % str(e.message).strip())
                # time.sleep(10)
                # ret = []
                raise e

            curr.close()
            conn.close()
            return '\n'.join(ret)
        def select(self, q, k={}):
            conn = self.getConn()
            logging.debug('sqlrun - connected to %s' % (self.conn_str))
            curr = conn.cursor()

            try:
                ################################################################################
                # encoding
                params = {}
                for key, val in k.iteritems():
                    params[key.encode(self.encoding)] = val.encode(self.encoding)

                q = q.encode(self.encoding)

                ################################################################################
                curr.execute("begin dbms_application_info.set_module('zezem-sqlrun', ''); end;")
                logging.debug('sqlrun - %s@%s' % (q, str(params)))
                curr.execute(q, params)

                if curr.rowcount >= 0:
                    ################################################################################
                    descriptions = curr.description
                    if descriptions:
                        columns = [desc[0].decode(self.encoding) for desc in descriptions]
                    else:
                        columns = []

                    ################################################################################
                    rows = []
                    for row in curr.fetchall():
                        cs = []
                        for c in row:
                            if isinstance(c, int): cs.append(c)
                            elif isinstance(c, unicode): cs.append(c.decode(self.encoding))
                            elif isinstance(c, str): cs.append(c.decode(self.encoding))
                            elif isinstance(c, datetime): cs.append(c.__str__())
                            elif c is None: cs.append(u'')
                            else: cs.append(c)
                        rows.append(cs)
                else:
                    rows = []
                    columns = []
            except Exception as e:
                try:
                    raise SqlRuntimeError(e.message.decode(self.encoding))
                except UnicodeDecodeError:
                    raise SqlRuntimeError(e.message)
            finally:
                curr.close()
                conn.close()
                logging.debug('sqlrun - disconnected to %s' % (self.conn_str))
            return (columns, rows)

        def getEncoding(self):
            return self.encoding
except ImportError:
    class dbconn():
        def __init__(self, conn_str):
            pass
        def getConn(self): raise Exception('Not found cx_Oracle module.')
        def select(self, q, k=None): raise Exception('Not found cx_Oracle module.')
        def getEncoding(self): raise Exception('Not found cx_Oracle module.')
