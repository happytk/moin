# -*- coding: utf-8 -*-
"""
MoinMoin - do global changes to all pages in a wiki.

@copyright: 2004-2006 MoinMoin:ThomasWaldmann
@license: GNU GPL, see COPYING for details.
"""

debug = False

from MoinMoin import Page
# from MoinMoin.Page import MercurialPageAdaptor, DirectoryPlatfilePageAdaptor
from MoinMoin.storage import DayoneMiddleware, DirectoryPlatfileMiddleware, MercurialMiddleware, PlatfileMiddleware, MoinWikiMiddleware
from MoinMoin.script import MoinScript
# from MoinMoin import wikiutil
# from pagelib.hgdb import WikiStorage


class PluginScript(MoinScript):

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)

    def mainloop(self):

        self.init_request()
        request = self.request

        # configuration

        # 'hg1': (MercurialMiddleware,         (os.path.abspath(os.path.dirname(__file__)) + '\moinhg1',)),
        # 'hg2': (MercurialMiddleware,         (os.path.abspath(os.path.dirname(__file__)) + '\moinhg2',)),
        # 'fs1': (DirectoryPlatfileMiddleware, (os.path.abspath(os.path.dirname(__file__)) + '\moindpl',)),
        # 'fs2': (PlatfileMiddleware,          (os.path.abspath(os.path.dirname(__file__)) + '\moinpl',)),
        # 'wiki': (MoinWikiMiddleware,         ()),
        # 'dayone': (DayoneMiddleware,         ('/volume1/dropbox_rainyblue/Apps/Day One/Journal.dayone',)),


        # src, target
        data_hg_dir = 'd:/__cloud/moinprv'
        source = MercurialMiddleware(data_hg_dir)

        data_dpl_dir = 'd:/__cloud/prv_target'
        target = DirectoryPlatfileMiddleware(data_dpl_dir)

        #read source pages
        for pagename_fs in source.list_pages():

            body = source.get_adaptor(request, pagename_fs).get_body()

            pagename_fs = pagename_fs.replace('(3f)', '') #? -> ''
            print pagename_fs
            target.get_adaptor(request, pagename_fs).is_write_file(body)

