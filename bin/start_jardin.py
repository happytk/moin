import os, sys
MOINPATH = os.environ['MOIN']
sys.path.insert(0, os.path.join(MOINPATH, 'wiki-jardin')) #for wikiconfig
#sys.path.insert(0, os.path.join(MOINPATH, 'chloe-skt'))   #ptree-web
sys.path.insert(0, os.path.join(MOINPATH, 'moin'))
sys.path.insert(0, os.path.join(MOINPATH, 'moin', 'MoinMoin', 'support'))
sys.path.insert(0, os.path.join(MOINPATH, 'moin', 'support'))

from werkzeug.wsgi import DispatcherMiddleware
from werkzeug import run_simple
from easy_attach import easy_attach_page
from easy_sqlrun import sqlrun_page
import flask

from MoinMoin.web.serving import make_application, switch_user, RequestHandler

def run_server(hostname='', port=8080,
               docs=True,
               debug='off',
               user=None, group=None,
               threaded=True,
               **kw):
    app = flask.Flask(__name__)
    app.register_blueprint(easy_attach_page, url_prefix='/easy_attach')
    app.register_blueprint(sqlrun_page, url_prefix='/sqlrun')
    """ Run a standalone server on specified host/port. """
    application = make_application(shared=docs)
    application = DispatcherMiddleware(application, {
        '/': application,
      	'/__moinfbp': app,
    })


    if port < 1024:
        if os.name == 'posix' and os.getuid() != 0:
            raise RuntimeError('Must run as root to serve port number under 1024. '
                               'Run as root or change port setting.')

    if user:
        switch_user(user, group)

    if debug == 'external':
        # no threading is better for debugging, the main (and only)
        # thread then will just terminate when an exception happens
        threaded = False

    run_simple(hostname=hostname, port=port,
               application=application,
               threaded=threaded,
               use_debugger=(debug == 'web'),
               passthrough_errors=(debug == 'external'),
               request_handler=RequestHandler,
               **kw)

if __name__ == "__main__":
    run_server(hostname='', port=8099, docs=os.path.join(MOINPATH, 'moin', 'MoinMoinHtdocs'))
