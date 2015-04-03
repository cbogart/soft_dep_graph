from setuptools import setup, find_packages
import sys, os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()


version = '0.1'

install_requires = [
    "numpy", "scipy", "community", "networkx"
]


setup(name='soft_dep_graphing',
    version=version,
    description="Graph manipulation library for software dependency mapping",
    long_description=README,
    classifiers=[
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    ],
    keywords='hpc database xalt',
    author='Christopher Bogart',
    author_email='cbogart@cs.cmu.edu',
    url='',
    dependency_links=[
      'https://bitbucket.org/taynaud/python-louvain/get/f56ac904d92c.zip',
    ],
    license='Apache 2.0',
    packages=find_packages(),
    zip_safe=False,
    install_requires=install_requires,
    setup_requires = install_requires,
)
