# https://packaging.python.org/en/latest/distributing.html
from setuptools import setup, find_packages

__version__ = ''
execfile('src/chill/_version.py')

setup(
    name='chill',
    version=__version__,
    author='Jake Hickenlooper',
    author_email='jake@weboftomorrow.com',
    keywords='static website SQL sqlite Flask web framework',
    description="Database driven web application framework in Flask",
    long_description="""
        This involves creating custom SQL queries to pull your data from your database
        into your jinja2 HTML templates for your website.  Chill creates a static
        version of the website or can run as a Flask app. Their are a few tables that
        are specific to Chill in order to handle page routes and what SQL query should
        be used and such.
    """,
    url='https://github.com/jkenlooper/chill',
    license='GPL',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Framework :: Flask',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Software Development :: Build Tools',
        ],
    package_dir={'': 'src'},
    packages=find_packages('src'),
    package_data={'chill': ['queries/*.sql']},
    zip_safe=False,
    test_suite="chill.tests",
    install_requires=[
        'setuptools',
        'docutils',
        'Flask==0.10.1',
        'Jinja2',
        'Flask-Cache',
        'Frozen-Flask',
        'Flask-Markdown',
        'psycopg2',
        'sqlalchemy',
        'PyYAML',
        'gevent',
        'docopt',
        'pyselect',
        'MarkupSafe',
    ],
    entry_points={
        'console_scripts': [
            'chill = chill.script:main'
            ]
        },
)
