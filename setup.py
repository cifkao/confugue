import setuptools
import sys

version = {}
with open("confugue/version.py") as f:
    exec(f.read(), version)

setuptools.setup(
    name="confugue",
    version=version['__version__'],
    author="Ondřej Cífka",
    description="Hierarchical configuration framework",
    packages=setuptools.find_packages(),
    python_requires='>=3.3',
    install_requires=[
        'cached_property',
        'pyyaml',
        'wrapt'
    ],
    tests_require=[
        'pytest'
    ]
)
