import sys, os, stat, uuid as pyuuid, re
import plistlib, datetime, glob
from MoinMoin.storage import PageAdaptor
from MoinMoin.logfile import editlog
from MoinMoin import wikiutil
from MoinMoin import log
from werkzeug import escape
logging = log.getLogger(__name__)


class DayoneMiddleware:
    def __init__(self, path, prefix='', restrict_user=None):
        self.path = path
        self.prefix = prefix
        self.user = restrict_user
        self.basepath = os.path.join(os.path.abspath(path), 'entries')
        # print 'hello'
    def get_adaptor(self, request, pagename_fs):
        return DayonePageAdaptor(request, pagename_fs[len(self.prefix):], self.basepath, self.prefix, self.user)
    def history(self, request):
        if not self.user or (request.user.valid and request.user.name == self.user):
            files = self._list_files(request)
            # files = sorted(files, lambda x,y:os.path.getmtime(x) < os.path.getmtime(y), reverse=True)
            files = sorted(files, key=lambda x:os.path.getmtime(x), reverse=True)
            _usercache = {}
            for filename in files:
                result = editlog.EditLogLine(_usercache)
                result.ed_time_usecs = wikiutil.timestamp2version(os.path.getmtime(filename))
                result.rev = 0
                result.action = 'SAVE'
                result.pagename = wikiutil.unquoteWikiname(self.prefix + os.path.splitext(os.path.basename(filename))[0])
                result.addr = ''
                result.hostname = ''
                if self.user:
                    result.userid = request.user.id #restrict_user is self
                else:
                    result.userid = ''
                result.extra = None
                result.comment = ''
                yield result
    def _list_files(self, request):
        lst = glob.glob(os.path.join(self.basepath, "*.doentry"))
        # logging.error(self.prefix)
        # logging.error(lst[:10])
        return lst
    def list_pages(self, request):
        # if not self.user or (request.user.valid and request.user.name == self.user):
        fnfilter = lambda x: wikiutil.unquoteWikiname(self.prefix + os.path.splitext(os.path.basename(x))[0])
        return map(fnfilter, self._list_files(request))
        # else:
        #     return []

class DayonePageAdaptor(PageAdaptor):
    def __init__(self, request, pagename_fs, basepath, prefix='', user=None):
        PageAdaptor.__init__(self, request, pagename_fs)
        self.pagename_fs = self.request.cfg.pagename_router(pagename_fs)
        self.path = basepath
        self.filepath = basepath + os.sep + pagename_fs + '.doentry'
        self.e = None
        self.prefix = prefix
        self.user = user
    def _get_entry(self):
        if self.e: return self.e

        # try to open file
        try:
            # f = codecs.open(self.filepath, 'rb', config.charset)
            self.e = Entry(self, self.filepath)
            # print e
        except IOError, er:
            import errno
            if er.errno == errno.ENOENT:
                # just doesn't exist, return empty text (note that we
                # never store empty pages, so this is detectable and also
                # safe when passed to a function expecting a string)
                return None
            else:
                raise

        return self.e

    def get_body(self):

        e = self._get_entry()

        try:
            # if len(e.tags):
            #     text = e.text
            # else:
            text = e.text
            # if re.match('[A-Z0-9]{32}', self.pagename_fs):
            #     text = '#acl All:\n#format text_markdown\n' + text

        except:
            text = ''
        finally:
            pass

        return text
    def text(self):
        return '[dayone]' + escape(self.get_body()[:20]) + '...'
    def exists(self, rev=0, domain=None, includeDeleted=False):
        # print self.filepath
        return os.path.isfile(self.filepath)
    def is_write_file(self, newtext):
        # save to page file
        e = self._get_entry()
        # Write the file using text/* mime type
        # newtext = newtext.replace(r'#acl All:', '').replace(r'#format text_markdown', '').strip()
        e.text = newtext
        if not re.match('[A-Z0-9]{32}', self.pagename_fs):
            # e.date = datetime.datetime.today()
            e.starred = True

            pagename = wikiutil.unquoteWikiname(self.pagename_fs)
            if not e.has_tag(pagename):
                e.addtag(pagename)

        try:
            if not e.date: e.date = datetime.datetime.utcnow()
        except KeyError: e.date = datetime.datetime.utcnow()
        try:
            if not e.uuid: e.uuid = str(pyuuid.uuid1()).upper().replace('-','')
        except KeyError: e.uuid = str(pyuuid.uuid1()).upper().replace('-','')
        e.save()


        return True
    def last_modified(self):
        return os.path.getmtime(self.filepath)
    def isWritable(self):
        return os.access(self.filepath, os.W_OK) or not self.exists()
    def delete(self):
        os.remove(self.filepath)
    def header(self):
        e = self._get_entry()
        # logging.error('hello'*100)
        # logging.error(str(e.picture))
        if e.picture:
            return '<img class="attachment" src="/%sdayone_photos/%s" style="max-width:100%%"/>' % (self.prefix, e.picture)
        else:
            return ''
    def lastEditInfo(self, request=None):
        time = wikiutil.version2timestamp(self.last_modified())
        if request:
            time = request.user.getFormattedDateTime(time) # Use user time format
        else:
            time = datetime.datetime.fromtimestamp(time*1000*1000).strftime('%Y-%m-%d %H:%M:%S') # Use user time format
        return {'editor': self.user, 'time': time}
    # def footer(self):
    #     e = self._get_entry()
    #     return u'<div style="text-align:right;">%s<br/>TAGS: <span style="background-color:yellow">%s</span></div>' % (self.prefix + e.uuid, '</span><span style="background-color:yellow">'.join(e.tags))

class Entry(object):
    def __init__(self, journal, filename=None):
        self._entry = {}
        self.journal = journal
        self.filename = filename
        if filename is not None:
            self.load()

    def load(self, filename=None):
        if filename is None:
            filename = self.filename
        try:
            self._entry = plistlib.readPlist(filename)
        except: #IOError
            self._entry = {}

    def save(self, filename=None):
        if filename is None:
            filename = self.filename
        self._entry["Time Zone"] = "Asia/Seoul"
        self._entry["Activity"] = "Stationary"

        plistlib.writePlist(self._entry, filename)

    def remove(self, filename=None):
        if filename is None:
            filename = self.filename
        os.remove(filename)

    @property
    def uuid(self): return self._entry["UUID"]
    @uuid.setter
    def uuid(self, x):
        self._entry["UUID"] = str(x)

    @property
    def text(self): return self._entry["Entry Text"]
    @text.setter
    def text(self, x):
        self._entry["Entry Text"] = unicode(x)

    @property
    def date(self): return self._entry["Creation Date"]
    @date.setter
    def date(self, x):
        if not isinstance(x, datetime.datetime):
            raise ValueError, "date must be a datetime object"
        self._entry["Creation Date"] = x

    @property
    def starred(self): return self._entry["Starred"]
    @starred.setter
    def starred(self, x):
        self._entry["Starred"] = bool(x)

    # Tags
    @property
    def tags(self): return self._entry.get("Tags",[])
    @tags.setter
    def tags(self, x):
        self._entry["Tags"] = list(x)
    def addtag(self, tag):
        if not self._entry.get("Tags", None): self._entry["Tags"] = []
        if tag not in self._entry["Tags"]:
            self._entry["Tags"].append(tag)
    def rmtag(self, tag):
        if tag in self._entry["Tags"]:
            self._entry["Tags"].remove(tag)
    def has_tag(self, tag):
        return tag in self.tags

    def pagename(self):
        return ''.join(self._entry.get("Tags", []))

    def last_modified(self):
        return os.path.getmtime(self.filename)

    # Location not implemented yet
    @property
    def location(self): return self._entry.get("Location",{})

    # Weather not implemented yet
    @property
    def weather(self): return self._entry.get("Weather",{})

    # Return the picture if there is one, not implemented yet
    @property
    def picture(self):
        fn = os.path.join(os.path.split(self.journal.path)[0], "photos", "%s.jpg" % (str(self.uuid).upper(),))
        # print fn
        if os.path.isfile(fn):
            # from PIL import Image
            # im = Image.open(fn)
            # if im.size[0] > 800:
            #     img_width = 800
            # else:
            #     img_width = im.size[0]
            return "%s.jpg" % str(self.uuid).upper()
        return None



# # This class could have more intelligence about when to load entries, checking
# # mtimes of cached entries to see if they've been changed externally, etc.
# # But for now, none of that is really necessary.

# class DayoneMiddleware(object):
#     def __init__(self, path="~/Dropbox/Apps/Day One/Journal.dayone"):
#         self.path = os.path.expanduser(path)
#         self._cache = {}
#         self._pagecache = {}

#     def filename_for_uuid(self, uuid):
#         return os.path.join(self.path, "entries", "%s.doentry" % (str(uuid).upper(),))

#     def new(self, title=None, body=None):
#         uuid = str(pyuuid.uuid1()).replace("-", "")
#         fn = self.filename_for_uuid(uuid)

#         entry = Entry(self, fn)
#         entry.uuid = uuid
#         entry.date = datetime.datetime.today()
#         entry.text = body
#         entry.addtag(title)
#         entry.save()

#         self._cache[uuid] = entry
#         self._pagecache[title] = entry

#         return self._cache[uuid]

#     def get(self, uuid):
#         fn = self.filename_for_uuid(uuid)
#         if uuid not in self._cache:
#             self._cache[uuid] = Entry(self, fn)

#         return self._cache[uuid]

#     def load(self):
#         self._cache = {}
#         # print 'loaded', os.listdir(os.path.join(self.path.encode('cp949'), "entries"))#, "*.doentry")
#         for fn in glob.iglob(os.path.join(self.path, "entries", "*.doentry")):
#             uuid = os.path.splitext(os.path.basename(fn))[0]
#             self._cache[uuid] = Entry(self, fn)
#             if len(self._cache[uuid].pagename()):
#                 self._pagecache[self._cache[uuid].pagename()] = self._cache[uuid]
#             # print uuid

#     def iter_entries(self):
#         if not self._cache:
#             self.load()

#         for entry in self._cache.itervalues():
#             yield entry

#     def entries(self):
#         return list(self.iter_entries())

#     def entries_by_creation_date(self):
#         e = self.entries()
#         e.sort(lambda x,y: cmp(x.date, y.date))
#         return e

#     def get_adaptor(self, request, pagename_fs):
#         return DayonePageAdaptor(request, pagename_fs, self.path, self)

#     def history(self, request):
#         files = sorted(self._list_files(request), key=lambda x:x.last_modified(), reverse=True)
#         _usercache = {}
#         for e in files:
#             result = editlog.EditLogLine(_usercache)
#             result.ed_time_usecs = wikiutil.timestamp2version(e.last_modified())
#             result.rev = 0
#             result.action = 'SAVE'
#             result.pagename = e.pagename()
#             result.addr = ''
#             result.hostname = ''
#             result.userid = ''
#             result.extra = None
#             result.comment = ''
#             yield result

#     def _list_files(self, request):
#         # return glob.glob(os.path.join(self.basepath, request.cfg.fs_extension))
#         # return glob.iglob(os.path.join(self.path, "entries", "*.doentry"))
#         if not self._pagecache:
#             self.load()

#         for entry in self._pagecache.itervalues():
#             yield entry

#     def list_pages(self, request):
#         pages = []
#         for e in self._list_files(None):
#             if len(e.pagename()):
#                 pages.append(e.pagename())
#         return pages

#     def find_uuid(self, pagename):
#         for e in self._list_files(None):
#             if e.pagename() == pagename:
#                 return e

#         return None


# class DayonePageAdaptor(PageAdaptor):
#     def __init__(self, request, pagename_fs, basepath, journal):
#         PageAdaptor.__init__(self, request, pagename_fs)
#         self.pagename_fs = self.request.cfg.pagename_router(pagename_fs)
#         self.journal = journal
#         self.filepath = journal.filename_for_uuid(self.pagename_fs)

#     def get_body(self):

#         entry = self.journal.find_pagename_fs(self.pagename_fs)
#         if entry:
#             return entry.text
#         else:
#             return ''

#     def exists(self):
#         return os.path.isfile(self.filepath)

#     def is_write_file(self, newtext):

#         if self.e:
#             # update the entry
#             self.e.text = newtext
#             self.e.date = datetime.datetime.today() # update the creation date
#             self.e.save()
#         else:
#             # new entry
#             self.e = self.journal.new(self.pagename_fs, newtext)

#         # UPDATE THE WIKI-BACKEND
#         return True

#     def last_modified(self):
#         if self.e:
#             return self.e.last_modified()
#         else:
#             return None

#     def isWritable(self):
#         if self.e:
#             return os.access(self.e.filename_fs, os.W_OK) or not self.exists()
#         return True

#     def delete(self):
#         # os.remove(self.filepath)
#         if self.e:
#             self.e.remove()

# """
# class DayoneMiddleware:
#     def __init__(self, path):
#         self.path = path
#         self.dodb = dayone.Journal(path=path)
#     def get_adaptor(self, request, pagename_fs):
#         return DayonePageAdaptor(request, pagename_fs, self.dodb)
#     def history(self, request):
#         for i in range(0):
#             yield i
#     def list_pages(self, request):
#         return []

# class DayonePageAdaptor(PageAdaptor):
#     def __init__(self, request, pagename_fs, dodb):
#         PageAdaptor.__init__(self, request, pagename_fs)

#         #todo- request
#         self.dodb = dodb
#         self.uuid = self.pagename_fs[len('DayOne(2f)'):]

#     def get_body(self):
#         entry = self.dodb.get(self.uuid)
#         return entry.text

#     def exists(self):
#         return True

#     def is_write_file(self, newtext):
#         e = self.dodb.get(self.uuid)
#         e.text = newtext
#         e.save()
#         return False

#     def last_modified(self):
#         # request.last_modified = os.path.getmtime(self._text_filename()) self.hgdb.page_meta(self.page_name_fs)[1]
#         return None

#     def isWritable(self):
#         # return os.access(self._text_filename(), os.W_OK) or not self.exists()
#         #return not self.exists()
#         return True

#     def delete(self):
#         pass
# """