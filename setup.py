# https://packaging.python.org/en/latest/distributing.html
from setuptools import setup, find_packages

__version__ = "0.9.0-alpha.1"  # Also set in src/chill/_version.py

setup(
    name="chill",
    version=__version__,
    author="Jake Hickenlooper",
    author_email="jake@weboftomorrow.com",
    keywords="static website SQL sqlite Flask web framework",
    description="Database driven web application framework in Flask",
    long_description="""
        This involves creating custom SQL queries to pull your data from an
        sqlite3 database into jinja2 HTML templates for a website.  Chill
        creates a static version of the website or can run as a Flask app. There
        are a few tables that are specific to Chill in order to handle page
        routes and what SQL query should be used and such.
    """,
    url="https://github.com/jkenlooper/chill",
    license="GPL",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Framework :: Flask",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Natural Language :: English",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Software Development :: Build Tools",
    ],
    package_dir={"": "src"},
    packages=find_packages("src"),
    package_data={"chill": ["queries/*.sql"]},
    zip_safe=False,
    test_suite="chill.tests",
    install_requires=[
        "Flask>=2,<3",
        "Jinja2>=3",
        "Flask-Caching>=1,<2",
        "Frozen-Flask==0.18",
        "Flask-Markdown==0.3",
        "PyYAML",
        "gevent",
        "docopt==0.6.2",
        "MarkupSafe>=2,<3",
        "babel",
        "humanize",
    ],
    python_requires=">=3.8",
    entry_points={"console_scripts": ["chill = chill.script:main"]},
)
