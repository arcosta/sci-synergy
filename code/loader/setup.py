# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='dblploader',
    version='0.1.0',
    description='Loader module of Sci-Synergy Project',
    long_description=readme,
    author='Aurelio Costa',
    author_email='arcosta@gmail.com',
    url='https://github.com/arcosta/sci-synergy',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)