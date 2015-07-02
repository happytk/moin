#!/opt/bin/python
#-*-encoding:utf-8-*-
import os
import sys
import re
import baker
import shutil

def unquote(pagename):
	from MoinMoin import wikiutil
	return wikiutil.quoteWikinameFS(pagename.decode('utf8'))

"""
위키페이지이름으로 디렉토리이동
"""
@baker.command
def cdp(pagename, wiki='wecanfly'):
	pagename = unquote(pagename)
	cfg = getattr(__import__('wiki_' + wiki), 'Config')
	path = os.path.join(cfg.data_dir, 'pages', pagename)
	if os.path.isdir(path):
		os.chdir(path)
	print path

"""
위키페이지이름으로 첨부파일의 디렉토리이동
"""
@baker.command
def cda(pagename, wiki='wecanfly', create=False):
	pagename = unquote(pagename)
	cfg = getattr(__import__('wiki_' + wiki), 'Config')
	path = os.path.join(cfg.data_dir, 'pages', pagename, 'attachments')
	if os.path.isdir(path):
		os.chdir(path)
	elif create:
		shutil.mkdir(path)
		os.chdir(path)
	print path

UNSAFE = re.compile(r'[^a-zA-Z0-9_]+')

def quoteWikinameFS(wikiname): #, charset='utf8'):
    """ Return file system representation of a Unicode WikiName.

    Warning: will raise UnicodeError if wikiname can not be encoded using
    charset. The default value of config.charset, 'utf-8' can encode any
    character.

    @param wikiname: Unicode string possibly containing non-ascii characters
    @param charset: charset to encode string
    @rtype: string
    @return: quoted name, safe for any file system
    """
    # filename = wikiname.decode(charset)
    filename = wikiname

    quoted = []
    location = 0
    for needle in UNSAFE.finditer(filename):
        # append leading safe stuff
        quoted.append(filename[location:needle.start()])
        location = needle.end()
        # Quote and append unsafe stuff
        quoted.append('(')
        for character in needle.group():
            quoted.append('%02x' % ord(character))
        quoted.append(')')

    # append rest of string
    quoted.append(filename[location:])
    return ''.join(quoted)


@baker.command
def wikiname(pagename):
    path = os.environ.get('DEFAULT_WIKI_DIR', None)
    if not path:
        print >> sys.stderr, 'export DEFAULT_WIKI_DIR='
        print quoteWikinameFS(pagename)
    else:
        print >> sys.stderr, 'DEFAULT_WIKI_DIR ->', path
        print os.path.join(path, quoteWikinameFS(pagename))	


if __name__ == "__main__":
	baker.run()





