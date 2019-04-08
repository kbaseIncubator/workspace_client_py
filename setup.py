#!/usr/bin/env python
from distutils.core import setup

setup(
    name='kbase_workspace_client',
    version='0.0.2',
    description='KBase workspace client',
    author='KBase Team',
    author_email='info@kbase.us',
    url='https://github.com/kbaseincubator/kbase_workspace_client',
    package_dir={'': 'src'},
    packages=[
        'kbase_workspace_client'
    ],
    install_requires=[
        'requests>=2'
    ],
    python_requires='>3'
)
