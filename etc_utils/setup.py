#!/usr/bin/env python

# setuptools is required
from setuptools import setup


with open('README.md') as fp:
    description = fp.read()

setup(
    # The package
    name="etc_utils",
    version="2026.2.dev0",
    packages=["etc_utils",
              "etc_utils.helpers",
              ],
    package_dir={'etc_utils': '',
                 'etc_utils.helpers': 'helpers'},

    description='Database and helper utilities',
    long_description=description,
    author='Mark Sienkiewicz, Vicki Laidler',

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
        'etc_utils': ["*.sql", "*.html"]
        },
    install_requires=[
        "setuptools"
    ],
    zip_safe=False
)
