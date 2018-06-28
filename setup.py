#!/usr/bin/env python

from distutils.core import setup

setup(name='Moodle Auto Enroll',
      version='1.0',
      description='Enroll automatically in moodle courses',
      author='cynt4k',
      author_email='github@cynt4k.de',
      url='https://github.com/cynt4k/moodle-auto-enroll',
      packages=['getopt', 'json', 'requests_html', 'bs4', 'time', 'smtplib', 'socket', 'email', 'threading'],
      )
