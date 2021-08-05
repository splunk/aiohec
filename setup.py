import os
import re

from setuptools import setup  # type: ignore

with open("README.md", "r") as fh:
    long_description = fh.read()


def version():
    version_pattern = r"__version__\W*=\W*\"([^\"]+)\""
    src = os.path.join(os.path.dirname(__file__), 'aiohec/__init__.py')
    with open(src, 'r') as f:
        (v,) = re.findall(version_pattern, f.read())
    return v


setup(
    name='aiohec',
    version=version(),
    author='Marcus LaFerrera',
    author_email='mlaferrera@splunk.com',
    description='An async Splunk module for Getting Data In (GDI)',
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='Apache License 2.0',
    url='https://github.com/splunk/aiohec',
    include_package_data=True,
    packages=['aiohec'],
    install_requires=open('requirements.txt').read().split(),
    keywords='splunk',
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: Utilities',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
