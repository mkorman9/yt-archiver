from distutils.core import setup
from setuptools import find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE.txt') as f:
    license = f.read()


setup(
    name='yt-archiver',
    version='0.1.0',
    description='Daemon for monitoring YouTube channels for new videos. Offers automatic backup of uploaded content',
    long_description=readme,
    license=license,
    author='Michal Korman',
    author_email='michal.korman@icloud.com',
    url='https://github.com/mkorman9/yt-archiver',
    packages=find_packages(),
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS',
        'Operating System :: Microsoft',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python',
        'Environment :: Console',
    ],
    entry_points={
        'console_scripts': [
            'ytarchiver = ytarchiver.main:main'
        ]
    },
    install_requires=['pytube', 'google-api-python-client'],
)
