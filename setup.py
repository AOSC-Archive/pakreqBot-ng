#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

import os
import re

from setuptools import find_packages, setup


def read_version():
    regexp = re.compile(r"^__version__\W*=\W*'([\d.abrc]+)'")
    init_py = os.path.join(os.path.dirname(__file__),
                           'pakreq', '__init__.py')
    with open(init_py) as f:
        for line in f:
            match = regexp.match(line)
            if match is not None:
                return match.group(1)
        else:
            msg = 'Cannot find version in pakreq/__init__.py'
            raise RuntimeError(msg)


install_requires = ['aiohttp',
                    'aiosqlite3',
                    'sqlalchemy',
                    'aiohttp-jinja2',
                    'trafaret-config']


setup(name='pakreq',
      version=read_version(),
      description='Here\'s another pakreq for ya!',
      platforms=['POSIX'],
      packages=find_packages(),
      package_data={
          '': ['templates/*.html', 'static/*.*']
      },
      include_package_data=True,
      install_requires=install_requires,
      zip_safe=False)
