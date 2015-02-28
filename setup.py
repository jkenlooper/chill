from setuptools import setup, find_packages
import os

name = "chill"
version = "0.2.0-mustached-rival.1"

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(
    name=name,
    version=version,
    author='Jake Hickenlooper',
    author_email='jake@weboftomorrow.com',
    description="Database driven web application framework in Flask",
    long_description=read('README.rst'),
    url='https://github.com/jkenlooper/chill',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.6',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Software Development :: Build Tools',
        'Environment :: Web Environment',
        ],
    package_dir={'': 'src'},
    packages=find_packages('src'),
    package_data={'chill': ['selectsql/*.sql']},
    zip_safe=False,
    test_suite="chill.tests",
    install_requires=[
        'setuptools',
        'docutils',
        'Flask',
        'Jinja2',
        'Frozen-Flask',
        'pysqlite',
        'PyYAML',
        'gevent',
        'docopt',
      ],
    entry_points={
        'console_scripts': [
            'chill = chill.script:main'
            ]
        },
)
