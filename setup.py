from setuptools import setup, find_packages
import os

name = "chill"
version = "0.1.1"

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(
    name=name,
    version=version,
    author='Jake Hickenlooper',
    author_email='jake@weboftomorrow.com',
    description="Simple Frozen website management",
    long_description=read('README.txt'),
    url='http://www.weboftomorrow.com',
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
    include_package_data=True,
    package_data={name:['chill/data/*','chill/themes/*']},
    zip_safe=False,
    install_requires=[
        'setuptools',
        'Flask',
        'Frozen-Flask',
        'PyYAML',
        'pystache',
      ],
    entry_points="""
    [console_scripts]
    run = chill.script:run
    freeze = chill.script:freeze
    """,
)
