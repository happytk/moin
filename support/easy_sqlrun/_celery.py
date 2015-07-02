#!/usr/bin/python
# EASY-INSTALL-ENTRY-SCRIPT: 'celery==3.0.12','console_scripts','celery'
__requires__ = 'celery>=3.0.12'
import sys
from pkg_resources import load_entry_point

import tasks

if __name__ == '__main__':
	# sys.exit(
	#     load_entry_point('celery>=3.0.12', 'console_scripts', 'celery')()
	# )
	while 1:
		try:
			load_entry_point('celery>=3.0.12', 'console_scripts', 'celery')()
		except KeyError:
			import traceback
			print traceback.format_exc()
