# https://packaging.python.org/en/latest/distributing.html
from setuptools import setup, find_packages
import pathlib


here = pathlib.Path(__file__).parent.resolve()
__version__ = "0.9.0"  # Also set in src/chill/_version.py
long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name="chill",
    version=__version__,
    author="Jake Hickenlooper",
    author_email="jake@weboftomorrow.com",
    keywords="static website generator SQL sqlite Flask web framework",
    description="Database driven web application framework in Flask",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/jkenlooper/chill",
    license="LGPLv3+",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: Web Environment",
        "Framework :: Flask",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
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
        "Frozen-Flask==0.18",
        "Flask-Markdown==0.3",
        "PyYAML",
        "gevent",
        "docopt==0.6.2",
        "MarkupSafe>=2,<3",
        "babel",
        "humanize",
    ],
    python_requires='>=3.8, <4',
    entry_points={"console_scripts": ["chill = chill.script:main"]},
)
