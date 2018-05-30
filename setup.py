from distutils.core import setup
from setuptools import find_packages

setup(
    name='yt-archiver',
    version='0.1.0',
    description='Daemon for monitoring YouTube channels for new videos. Offers automatic backup of uploaded content',
    author='Michal Korman',
    author_email='michal.korman@icloud.com',
    packages=find_packages(),
    install_requires=['pytube', 'google-api-python-client']
)
