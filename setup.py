import setuptools
import sys


setuptools.setup(
    name="confugue",
    author="Ondřej Cífka",
    description="A configuration framework",
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
    install_requires=[
        'cached_property',
        'pyyaml',
    ],
)
