import setuptools
import sys

version = {}
with open('confugue/version.py') as f:
    exec(f.read(), version)

with open('README.rst', 'r') as f:
    long_description = f.read()

setuptools.setup(
    name='confugue',
    version=version['__version__'],
    author='Ondřej Cífka',
    author_email='ondra@cifka.com',
    description='Hierarchical configuration framework',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/cifkao/confugue',
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    python_requires='>=3.5',
    install_requires=[
        'pyyaml',
        'wrapt'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research'
    ],
)
