# -*- coding: utf-8 -*-
"""
This module contains the tool of cs.pfg.mipago
"""
import os
from setuptools import setup, find_packages


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

version = '1.0b9'

long_description = (
    open('README.rst').read() + '\n' +
    open('CHANGES.rst').read() + '\n'
)

setup(name='cs.pfg.mipago',
      version=version,
      description="PloneFormGen adapter to pay with Basque Government's payment service",
      long_description=long_description,
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        'Framework :: Plone',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        ],
      keywords='',
      author='Mikel Larreategi',
      author_email='mlarreategi@codesyntax.com',
      url='https://github.com/codesyntax/cs.pfg.mipago',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['cs', 'cs.pfg'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
            'setuptools',
            'Products.PloneFormGen',
            'pymipago',
            'pytz',
            'Plone',
            'zope.configuration',
            'tablib',
      ],
      extras_require={'test': [
          'plone.app.testing [robot]',
          'plone.api',
          'plone.app.robotframework'

      ]},
      entry_points="""
      # -*- entry_points -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
