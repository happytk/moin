import glob
import re
import os
import datetime
import codecs

# try:
#     import dayone
# except ImportError:
#     class dayone:
#         def __init__(self, *args, **kwargs):
#             pass

try:
    from hatta.storage import WikiStorage as HattaWikiStorage
    class WikiStorage(HattaWikiStorage):
        def _title_to_file(self, title):
            filename = title.strip() + self.extension
            return os.path.join(self.repo_prefix, filename)

        def _file_to_title(self, filepath):
            _ = self._
            if not filepath.startswith(self.repo_prefix):
                raise Exception(u"Can't read or write outside of the pages repository")
            name = filepath[len(self.repo_prefix):].strip('/')
            # Un-escape special windows filenames and dot files
            # if name.startswith('_') and len(name) > 1:
            #     name = name[1:]
            if self.extension and name.endswith(self.extension):
                name = name[:-len(self.extension)]
            return name
except ImportError:
    class WikiStorage:
        def __init__(self, *args, **kwargs):
            raise Exception('hatta-package import error -- Need the Hatta package to use the mercurial repository.')

from MoinMoin.logfile import editlog
from MoinMoin import caching
from MoinMoin import wikiutil
from MoinMoin import config
from MoinMoin.Page import WikiPage, WikiRootPage
from MoinMoin import log

logging = log.getLogger(__name__)


class PageAdaptor:
    def __init__(self, request, pagename_fs):
        self.request = request
        self.pagename_fs = pagename_fs
    def header(self): return ''
    def footer(self): return ''
    def text(self): return wikiutil.unquoteWikiname(self.pagename_fs)
    def lastEditInfo(self, request=None): return None

class MoinWikiMiddleware:
    def __init__(self):
        pass
    def get_adaptor(self, request, pagename_fs):
        return MoinWikiPageAdaptor(request, pagename_fs)
    def history(self, request):
        for i in range(0):
            yield i
    def list_pages(self, request):
        return WikiRootPage(request)._listPages()

class MoinWikiPageAdaptor(PageAdaptor):
    def __init__(self, request, pagename_fs):
        PageAdaptor.__init__(self, request, pagename_fs)
        self.pagename = wikiutil.unquoteWikiname(pagename_fs)
        self.page = WikiPage(request, self.pagename)

    def get_body(self):
        return self.page.get_raw_body()

    def exists(self, rev=0, domain=None, includeDeleted=False):
        return self.page.exists(rev, domain, includeDeleted)

    def is_write_file(self, newtext):
        return True

    def last_modified(self):
        return os.path.getmtime(self.page._text_filename())

    def isWritable(self):
        return self.page.isWritable()

    def delete(self):
        pass


class MercurialMiddleware:
    def __init__(self, path):
        self.path = path
        self.hgdb = WikiStorage(path, extension='.md')
    def get_adaptor(self, request, pagename_fs):
        return MercurialPageAdaptor(request, pagename_fs, self.hgdb)
    def history(self, request):
        _usercache = {}
        for title, rev, date, author, comment in self.hgdb.history():
            if comment.startswith('HgHidden:'):
                continue
            result = editlog.EditLogLine(_usercache)
            result.ed_time_usecs = wikiutil.timestamp2version((date - datetime.datetime(1970,1,1)).total_seconds())
            result.rev = rev
            result.action = 'SAVE'
            result.pagename = wikiutil.unquoteWikiname(title)
            result.addr = ''
            result.hostname = ''
            result.userid = author
            result.extra = None
            result.comment = '' if comment == 'comment' or comment.startswith('MoinEdited:') else comment
            yield result
    def list_pages(self, request):
        pages = [page for page in self.hgdb.all_pages()]
        return pages

class MercurialPageAdaptor(PageAdaptor):
    def __init__(self, request, pagename_fs, hgdb):
        PageAdaptor.__init__(self, request, pagename_fs)
        self.hgdb = hgdb
    def get_body(self):
        pagename_fs = self.request.cfg.pagename_router(self.pagename_fs)
        try:
            hg_text = self.hgdb.page_text(pagename_fs)
        except:
            hg_text = None
        return hg_text
    def exists(self, rev=0, domain=None, includeDeleted=False):
        # if self.request.cfg.is_target(self.pagename_fs):
        #     return True
        if self.pagename_fs in self.hgdb:
            return True
        return False
    def is_write_file(self, newtext):
        pagename_fs = self.request.cfg.pagename_router(self.pagename_fs)
        newtext = newtext.encode('utf8')
        author = self.request.user.valid and self.request.user.id or ''
        comment = 'MoinEdited: ' + wikiutil.unquoteWikiname(pagename_fs)
        self.hgdb.save_data(pagename_fs, newtext, author=author , comment=comment, parent_rev=None)
        return True
    def last_modified(self):
        pagename_fs = self.request.cfg.pagename_router(self.pagename_fs)
        return self.hgdb.page_meta(pagename_fs)[1]
    def isWritable(self):
        # return os.access(self._text_filename(), os.W_OK) or not self.exists()
        #return not self.exists()
        return True
    def delete(self):
        self.hgdb.delete_page(self.pagename_fs, '', '')


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


class PlatfileMiddleware:
    def __init__(self, path):
        self.path = path
        self.basepath = os.path.abspath(path)
    def get_adaptor(self, request, pagename_fs):
        return PlatfilePageAdaptor(request, pagename_fs, self.path)
    def history(self, request):
        files = self._list_files(request)
        files = sorted(files, lambda x,y:os.path.getmtime(x) < os.path.getmtime(y), reverse=True)
        _usercache = {}
        for filename in files:
            result = editlog.EditLogLine(_usercache)
            result.ed_time_usecs = wikiutil.timestamp2version(os.path.getmtime(filename))
            result.rev = 0
            result.action = 'SAVE'
            result.pagename = wikiutil.quoteWikinameFS(os.path.splitext(os.path.basename(filename))[0].decode(request.cfg.fs_encoding))
            result.addr = ''
            result.hostname = ''
            result.userid = ''
            result.extra = None
            result.comment = ''
            yield result
    def _list_files(self, request):
        return glob.glob(os.path.join(self.basepath, request.cfg.fs_extension))
    def list_pages(self, request):
        fnfilter = lambda x: wikiutil.quoteWikinameFS(os.path.splitext(os.path.basename(x))[0].decode(request.cfg.fs_encoding))
        return map(fnfilter, self._list_files(request))

class PlatfilePageAdaptor(PageAdaptor):
    def __init__(self, request, pagename_fs, basepath):
        PageAdaptor.__init__(self, request, pagename_fs)

        pagename_fs = self.request.cfg.pagename_router(pagename_fs)

        self.basepath = os.path.abspath(basepath)
        self.filepath = self.basepath + os.sep + pagename_fs + request.cfg.fs_extension
    def get_body(self):
        # try to open file
        try:
            f = codecs.open(self.filepath, 'rb', config.charset)
        except IOError, er:
            import errno
            if er.errno == errno.ENOENT:
                # just doesn't exist, return empty text (note that we
                # never store empty pages, so this is detectable and also
                # safe when passed to a function expecting a string)
                return ""
            else:
                raise

        try:
            text = f.read()
        finally:
            f.close()

        return text

    def exists(self, rev=0, domain=None, includeDeleted=False):
        return os.path.isfile(self.filepath)
    def is_write_file(self, newtext):
        # save to page file
        f = codecs.open(self.filepath, 'wb', config.charset)
        # Write the file using text/* mime type
        f.write(newtext)
        f.close()

        # mtime_usecs = wikiutil.timestamp2version(os.path.getmtime(pagefile))
        # # set in-memory content
        # self.set_raw_body(text)
        return True
    def last_modified(self):
        return os.path.getmtime(self._text_filename())
    def isWritable(self):
        return os.access(self.filepath, os.W_OK) or not self.exists()
    def delete(self):
        os.remove(self.filepath)


periods_re = re.compile(r'^[.]|(?<=/)[.]')
slashes_re = re.compile(r'^[/]|(?<=/)[/]')

class DirectoryPlatfileMiddleware:
    def __init__(self, path):
        self.path = path
        self.basepath = os.path.abspath(path)
    def get_adaptor(self, request, pagename_fs):
        return DirectoryPlatfilePageAdaptor(request, pagename_fs, self.path)
    def list_pages(self, request):
        # fnfilter = lambda x: wikiutil.quoteWikinameFS(os.path.splitext(os.path.basename(x))[0])
        # fnfilter = lambda x: wikiutil.quoteWikinameFS(os.path.splitext(os.path.basename(x))[0].decode(request.cfg.fs_encoding))
        def _f(fn):
            fn = os.path.basename(fn)
            if fn.endswith(request.cfg.fs_extension):
                fn = fn[:-len(request.cfg.fs_extension)]
            fn = fn.decode(request.cfg.fs_encoding)
            # fn = wikiutil.quoteWikinameFS(fn)
            return fn
        return map(_f, self._list_files())
    def _list_files(self):
        pages = []
        for root, dirs, files in os.walk(self.basepath):
            for name in dirs: pages.append(os.path.join(root, name)[len(self.basepath)+1:].replace(os.sep, '/'))
            for name in files: pages.append(os.path.join(root, name)[len(self.basepath)+1:].replace(os.sep, '/'))
        return pages
    def history(self, request):
        # files = self._list_files()
        pages = []
        for root, dirs, files in os.walk(self.basepath):
            for name in dirs: pages.append(os.path.join(root, name))
            for name in files: pages.append(os.path.join(root, name))

        # pages = sorted(pages, lambda x,y: os.path.getmtime(x) < os.path.getmtime(y), reverse=True)
        # logging.warning(str(pages))
        pages = sorted(pages, key=lambda(x): os.path.getmtime(x), reverse=True)
        
        _usercache = {}
        for filename in pages:
            result = editlog.EditLogLine(_usercache)
            result.ed_time_usecs = wikiutil.timestamp2version(os.path.getmtime(filename))
            result.rev = 0
            result.action = 'SAVE'
            filename = filename[len(self.basepath)+1:].replace(os.sep, '/')
            if filename.endswith(request.cfg.fs_extension):
                filename = filename[:-len(request.cfg.fs_extension)]
            result.pagename = filename.decode(request.cfg.fs_encoding)
            result.addr = ''
            result.hostname = ''
            result.userid = ''
            result.extra = None
            result.comment = ''
            yield result

class DirectoryPlatfilePageAdaptor(PageAdaptor):
    def __init__(self, request, pagename_fs, basepath):
        PageAdaptor.__init__(self, request, pagename_fs)

        #logging.warning(pagename_fs)
        pagename_fs = self.request.cfg.pagename_router(pagename_fs)

        pagename = wikiutil.unquoteWikiname(pagename_fs)
        # escaped = werkzeug.url_quote(escaped, safe='/ ')
        # escaped = periods_re.sub('%2E', escaped)
        # escaped = slashes_re.sub('%2F', escaped)
        self.pagename = pagename
        self.filename = pagename
        if len(os.path.splitext(pagename)[1]) == 0 or len(os.path.splitext(pagename)[1]) > 4:
        	self.filename += request.cfg.fs_extension

        basepath = os.path.abspath(basepath)
        self.filepath = os.path.join(basepath, self.filename)
        self.basepath = os.path.dirname(self.filepath)
        # print self.filepath

    def get_body(self):
        # try to open file
        try:
            f = codecs.open(self.filepath, 'rb', config.charset)
        except IOError, er:
            import errno
            if er.errno == errno.ENOENT:
                # just doesn't exist, return empty text (note that we
                # never store empty pages, so this is detectable and also
                # safe when passed to a function expecting a string)
                return ""
            else:
                raise

        try:
            text = f.read()
        finally:
            f.close()

        return text

    def exists(self, rev=0, domain=None, includeDeleted=False):
        return os.path.isfile(self.filepath)
    def is_write_file(self, newtext):

        if not os.path.isdir(self.basepath):
            os.makedirs(self.basepath)


        #print '*'*10, self.filepath

        # save to page file
        f = codecs.open(self.filepath, 'wb', config.charset)
        # Write the file using text/* mime type
        f.write(newtext)
        f.close()

        # mtime_usecs = wikiutil.timestamp2version(os.path.getmtime(pagefile))
        # # set in-memory content
        # self.set_raw_body(text)
        return True
    def last_modified(self):
        return os.path.getmtime(self.filepath)
    def isWritable(self):
        return os.access(self.filepath, os.W_OK) or not self.exists()
    def delete(self):
        os.remove(self.filepath)

        #remove if emtpy.
        try:
            os.removedirs(self.basepath)
        except:
            pass
