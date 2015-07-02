## Customized moin19 for a private CMS.

customized features.

- multi-backend (filesystem, mercurial, moin-wiki)
- dayone integration (list, view, edit)
- attachment charset
- page router


I'm always waiting for moin2.0 - because it's going to support hg backend, multi-backend-routing. but I found moin2.0 changed the milestone not having vcs-backend. so I've implemented this by myself quickly not by decent design. I've done for a just working. code is messy, not well-organized. but I'm trying to modifiy less original moin-code.

multi-backend works well for me. it has some limitations

- hatta-wiki storage class used for a mercurial backend.  (*let me know if this is not right*)
- always works with original-wiki-backend. (every backends save the document in its storage. and original-wiki-backend as well.)
- attachment files only located in wiki-backend.
- only RecentChanges can show filesystem, mercurial history. (info-action does not.)
- Filesystem, Mercurial backend saves as `pagename_fs`. it is filesystem-safe name be quoted by `MoinMoin.wikiutil.quoteWikiName`

check the wikiconfig_sample.py

### Multi-backend configuration (wikiconfig.py)

define the multiple backends.

```python
middlewares = {
'hg1': (MercurialMiddleware,         (os.path.abspath(os.path.dirname(__file__)) + '\moinhg1',)),
'hg2': (MercurialMiddleware,         (os.path.abspath(os.path.dirname(__file__)) + '\moinhg2',)),
'fs1': (DirectoryPlatfileMiddleware, (os.path.abspath(os.path.dirname(__file__)) + '\moindpl',)),
'fs2': (PlatfileMiddleware,          (os.path.abspath(os.path.dirname(__file__)) + '\moinpl',)),
'wiki': (MoinWikiMiddleware,         ()),
'dayone': (DayoneMiddleware,         ('/volume1/dropbox_rainyblue/Apps/Day One/Journal.dayone',)),
}
```

match the pagename with backends. Assume that pagename is quoted.

```python
routes = OrderedDict()
routes[_RE_DAYONE]  = 'dayone'
routes[_RE_FILEDIR] = 'fs1'
routes[_RE_FILE]    = 'fs2'
routes[_RE_CATE]    = 'wiki'
routes[_RE_HELPON]  = 'wiki'
routes[_RE_ALL]     = 'hg1'
```

if nothing is defined, matched, then original wiki-backend works.

### Backend migration

I wrote the migration script at `MoinMoin/script/maint/migratestorage.py`. you can edit for your own purpose.

### Mercurial-backend

### Filesystem-backend

### Dayone-backend

### Attachment charset

This is required for attachment files named as Korean (cp949). when Korean attachment files is saved at Windows, couldn't be saved as UTF-8.

```python
attachment_charset = 'cp949'` # default is utf8.
```

