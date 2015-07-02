#!/opt/bin/python
import json
import os
import time
import logging
import shutil
# from gevent.event import AsyncResult, Timeout
# from gevent.queue import Empty, Queue
# from shutil import rmtree
from hashlib import sha1
from stat import S_ISREG, ST_CTIME, ST_MODE
from werkzeug import secure_filename
import flask

try:
    import localconfig as config
except ImportError:
    import config_default as config

easy_attach_page = flask.Blueprint('easy_attach_page', __name__, template_folder='templates', static_folder='static')

# ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'mp3', 'mp4'])
# DATA_DIR = '/volume1/moindev/photo_origins'
# KEEP_ALIVE_DELAY = 25
# MAX_IMAGE_SIZE = 800, 600
# MAX_IMAGES = 10
# MAX_DURATION = 300

app = flask.Flask(__name__)# , static_folder=DATA_DIR)
# broadcast_queue = Queue()




# def broadcast(message):
#     """Notify all waiting waiting gthreads of message."""
#     waiting = []
#     try:
#         while True:
#             waiting.append(broadcast_queue.get(block=False))
#     except Empty:
#         pass
#     print('Broadcasting {0} messages'.format(len(waiting)))
#     for item in waiting:
#         item.set(message)


# def receive():
#     """Generator that yields a message at least every KEEP_ALIVE_DELAY seconds.

#     yields messages sent by `broadcast`.

#     """
#     now = time.time()
#     end = now + MAX_DURATION
#     tmp = None
#     # Heroku doesn't notify when client disconnect so we have to impose a
#     # maximum connection duration.
#     while now < end:
#         if not tmp:
#             tmp = AsyncResult()
#             broadcast_queue.put(tmp)
#         try:
#             yield tmp.get(timeout=KEEP_ALIVE_DELAY)
#             tmp = None
#         except Timeout:
#             yield ''
#         now = time.time()


def safe_addr(ip_addr):
    """Strip of the trailing two octets of the IP address."""
    return '.'.join(ip_addr.split('.')[:2] + ['xxx', 'xxx'])


def save_normalized_image(data_dir, filename, data):

    from PIL import Image, ImageFile
    from pilkit.processors import Transpose

    if not os.path.isdir(config.DATA_DIR):
        try:  # Reset saved files on each start
            # rmtree(DATA_DIR, True)
            os.mkdir(config.DATA_DIR)
        except OSError:
            raise
            return False

    path = os.path.join(data_dir, filename)
    orig_store_path = os.path.join(config.DATA_DIR, filename)

    image_parser = ImageFile.Parser()
    try:
        image_parser.feed(data)
        image = image_parser.close()
    except IOError:
        raise
        return False

    image.save(orig_store_path)

    try:
        image = Transpose().process(image)
    except (IOError, IndexError):
        pass

    image.thumbnail(config.MAX_IMAGE_SIZE, Image.ANTIALIAS)
    if image.mode != 'RGB':
        image = image.convert('RGB')

    image.save(path)
    return True


# def event_stream(client):
#     force_disconnect = False
#     try:
#         for message in receive():
#             yield 'data: {0}\n\n'.format(message)
#         print('{0} force closing stream'.format(client))
#         force_disconnect = True
#     finally:
#         if not force_disconnect:
#             print('{0} disconnected from stream'.format(client))


def get_filename(data):
      sha1sum = sha1(data).hexdigest()
      # target = os.path.join(data_dir, '{0}.jpg'.format(sha1sum))
      return sha1sum

@easy_attach_page.route("/upload", methods=["POST"])
def upload():
    """Handle the upload of a file."""
    form = request.form

    # Create a unique "session ID" for this particular batch of uploads.
    upload_key = str(uuid4())

    # Is the upload using Ajax, or a direct POST by the form?
    is_ajax = False
    if form.get("__ajax", None) == "true":
        is_ajax = True

    data_dir =  form.get("path", None)

    # # Target folder for these uploads.
    # target = "uploadr/static/uploads/{}".format(upload_key)
    try:
        if not data_dir: raise ''
        os.mkdir(data_dir)
    except:
        # if is_ajax:
        #     return ajax_response(False, "Couldn't create upload directory: {}".format(target))
        # else:
        return "Couldn't create upload directory: {}".format(data_dir)

    # print "=== Form Data ==="
    for key, value in form.items():
        print key, "=>", value

    for upload in request.files.getlist("file"):
        filename = upload.filename.rsplit("/")[0]
        destination = os.sep.join([target, filename])
        print "Accept incoming file:", filename
        print "Save it to:", destination
        upload.save(destination)

    # if is_ajax:
    #     return ajax_response(True, upload_key)
    # else:
    #     return redirect(url_for("upload_complete", uuid=upload_key))
    return 'success'

@easy_attach_page.route('/post', methods=['POST','GET'])
def post():
    filename = flask.request.values.get('filename', '').lower()
    data_dir = flask.request.values.get('path', None)
    direct = flask.request.values.get('direct', 'false')

    if data_dir is None:
        return 'storage-path is not specified.'

    if not os.path.isdir(data_dir):
        try:
            os.mkdir(data_dir)
        except:
            return "Couldn't create upload directory: {}".format(data_dir)

    def _save_direct():
        # f = secure_filename(filename)
        f = filename
        target = os.path.join(data_dir, f)

        if os.path.isfile(target) or os.path.isdir(target):
            return 'FAIL/%s exists already.' % f

        try:
            open(target, 'wb').write(flask.request.data)
        except Exception as e:
            return '{0}'.format(e)

        return 'success' + '/' + f

    # if not filename:
    #   return 'no filename'

    # if not pagename:
    #   return 'no pagename'

    # if filename and (not filename.endswith('.jpg') or not filename.endswith('.jpeg')):
    #   target = os.path.join(data_dir, filename)
    if direct == 'false' and (filename.endswith('.jpg') or filename.endswith('.jpeg')):

        sha1sum = get_filename(flask.request.data)
        target = '{0}.jpg'.format(sha1sum)
        # message = json.dumps({'src': '{0}.jpg'.format(sha1sum),
        #                       'ip_addr': safe_addr(flask.request.access_route[0])})
        try:
            # save_normalized_image(target, flask.request.data)
            tf = os.path.join(data_dir, target)
            if os.path.isfile(tf) or os.path.isdir(tf):
                return 'FAIL/%s exists already.' % target
            if save_normalized_image(data_dir, target, flask.request.data):
                # broadcast(message)  # Notify subscribers of completion
                pass
        except ImportError:
            logging.critical('Image normalizing failed (import error)')
            return _save_direct()

        except Exception as e:  # Output errors
            return 'FAIL/{0}'.format(e)
        
        return 'success' + '/' + '{0}.jpg'.format(sha1sum)

    else:
        return _save_direct()


# @app.route('/stream')
# def stream():
#     return flask.Response(event_stream(flask.request.access_route[0]),
#                           mimetype='text/event-stream')


@easy_attach_page.route('/')
def home():
    # Code adapted from: http://stackoverflow.com/questions/168409/
    # image_infos = []
    # for filename in os.listdir(DATA_DIR):
    #     filepath = os.path.join(DATA_DIR, filename)
    #     file_stat = os.stat(filepath)
    #     if S_ISREG(file_stat[ST_MODE]):
    #         image_infos.append((file_stat[ST_CTIME], filepath))

    images = []
    # for i, (_, path) in enumerate(sorted(image_infos, reverse=True)):
    #     if i >= MAX_IMAGES:
    #         os.unlink(path)
    #         continue
    #     images.append('<div><img alt="User uploaded image" src="{0}" /></div>'
    #                   .format(path))
    return flask.render_template('upload.html', max_image = config.MAX_IMAGES, img_tags = '\n'.join(images))


# #@baker.command
# def serve():
#     app.debug = True
#     app.run('0.0.0.0', port=8090)#, threaded=True)

#@baker.command
def convert(filename):
    if filename.endswith('.jpg') or filename.endswith('.jpeg'):
        data = open(filename, 'rb').read()
        sha1sum = get_filename(data)
        target = '{0}.jpg'.format(sha1sum)
        try:
            save_normalized_image('.', target, data)
            shutil.move('./' + filename, '/tmp/' + filename)
        except Exception as e:  # Output errors
            print e
    else:
        pass

#@baker.command
def convert_all():
    import glob
    for imgfn in glob.glob('*.jpg'):
        print 'converting ' + imgfn + '...'
        convert(imgfn)


if __name__ == '__main__':
    baker.run()
