#!/opt/bin/python
#-*-encoding: utf-8 -*-
import os, sys, signal, logging
from werkzeug.serving import BaseRequestHandler, run_simple

class RequestHandler(BaseRequestHandler):
    """
    A request-handler for WSGI, that overrides the default logging
    mechanisms to log via MoinMoin's logging framework.
    """
    server_version = "MoinMoin-Customized-by-happytk"

    __shared = {}

    # override the logging functions
    def log_request(self, code='-', size='-'):
        self.log_message('"%s" %s %s',
                         self.requestline, code, size)

    def log_error(self, format, *args):
        self.log_message(format, *args)

    def log_message(self, format, *args):
        # logging.info("%s %s", self.address_string(), (format % args))
        pass


if __name__ == "__main__":
    pidfile = "/volume1/moindev/moin.pid"
    if len(sys.argv) > 1 and sys.argv[1] in ['stop', 'restart']:
            try:
                pids = open(pidfile, "r").read()
                os.remove(pidfile)
            except IOError:
                print "pid file not found (server not running?)"
            else:
                try:
                    os.kill(int(pids), signal.SIGTERM)
                except OSError:
                    print "kill failed (server not running?)"
    if len(sys.argv) > 1 and sys.argv[1] in ['start', 'restart']:
        from werkzeug.wsgi import DispatcherMiddleware
        from MoinMoin.util.daemon import Daemon
        from MoinMoin.web.serving import make_application
        from OpenSSL import SSL
        # from easy_attach import app as attach_app
        from easy_attach import easy_attach_page
        import flask


        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.use_certificate_file('/volume1/moindev/htdocs_ssl_data/ssl.crt')
        ctx.use_privatekey_file('/volume1/moindev/htdocs_ssl_data/ssl.key')

        hostname = '0.0.0.0'
        port = 8090
        debug = 'off'
        user = None
        group = None
        threaded = True
        ssl_context = ctx
        shared = '/volume1/moindev/lib/moin/MoinMoinHtdocs'

        # moin-lib의 make_application에서 shared가 dict일 경우
        # 별도처리없이 SharedDataMiddleware를 만들어주기때문에
        # 여기에 통합해서 사용한다.
        docs = {'/moin_static195': shared,
                      # XXX only works / makes sense for root-mounted wikis:
                      '/favicon.ico': os.path.join(shared, 'favicon.ico'),
                      '/robots.txt': os.path.join(shared, 'robots.txt'),
                      '/TK_dayone_photos': '/volume1/homes/me/dropbox/Apps/Day One/Journal.dayone/photos',
                      '/MEI_dayone_photos': '/volume1/homes/me/dropbox_happytk/Apps/Day One (1)/Journal.dayone/photos/',
                      '/webpub_amb': '/volume1/photo/webpub_amb',
                      }
        application = make_application(shared=docs)

        if debug == 'external':
            # no threading is better for debugging, the main (and only)
            # thread then will just terminate when an exception happens
            threaded = False

        app = flask.Flask(__name__)
        app.register_blueprint(easy_attach_page, url_prefix='/easy_attach')
        application = DispatcherMiddleware(application, {
            '/archive':  application,
            '/ntuning':  application,
            '/mei':      application,
            '/master':   application,
            '/__moinfbp': app,
        })

        kwargs = dict(hostname=hostname, port=port,
                       application=application,
                       threaded=threaded,
                       use_debugger=(debug == 'web'),
                       passthrough_errors=(debug == 'external'),
                       request_handler=RequestHandler,
                       ssl_context=ctx)
        if len(sys.argv) > 1 and sys.argv[1] in ['start', 'restart']:
            daemon = Daemon('moin', pidfile, run_simple, **kwargs)
            daemon.do_start()
        else:
            run_simple(**kwargs)
