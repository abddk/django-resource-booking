from setuptools import setup, find_packages
import sys
import os

version = '0.1'

setup(name='django_resource_booking',
      version=version,
      description="Resource booking and allocation for large organizations.",
      long_description="""
Resource booking and allocation for large organizations - specifically
designed for the University of Copenhagen.""",
      classifiers=[],
      keywords='',
      author='Magenta ApS',
      author_email='info@magenta.dk',
      url='http://magenta.dk',
      license='GLPv3',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          'Django==1.8.18',
          'flake8==2.5.0',
          'psycopg2',
          'djorm-ext-pgfulltext==0.10',
          'django-npm==1.0.0',
          'django-timedeltafield',
          'django-recurrence',
          'django-tinymce==2.0.4',
          'djangosaml2==0.13.0',
          'django-cron==0.4.6',
          'django-ckeditor==5.1.1',
          'django-macros==0.4.0',
          'requests==2.20.0',
          'django-debug-toolbar==1.9',
          'django-hijack'
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
