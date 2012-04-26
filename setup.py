from setuptools import setup, find_packages
import os

name = "chill"
version = "0.0.0"

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
    license='',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'Flask',
        'pystache',
      ],
    entry_points="""
    [console_scripts]
    flask-ctl = chill.script:run

    [paste.app_factory]
    main = chill.script:make_app
    debug = chill.script:make_debug
    """,
)
