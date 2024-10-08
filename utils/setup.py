#!/usr/bin/env python

# setuptools is required
from setuptools import setup, find_packages


with open('README.md') as fp:
    description = fp.read()

setup(
    # The package
    name="utils",
    version="2025.2.dev0",
    packages=["utils",
              "utils.helpers",
              ],
    package_dir={'utils': '',
                 'utils.helpers': 'helpers'},

    description='Database and helper utilities',
    long_description=description,
    author='Mark Sienkiewicz, Vicki Laidler',
    author_email='help@stsci.edu',

    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
    ],

    package_data={
        'utils': ["*.sql", "*.html"]
        },
    install_requires=[
        "setuptools"
    ],
    zip_safe=False
)
