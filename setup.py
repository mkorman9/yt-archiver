from distutils.core import setup
from setuptools import find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE.txt') as f:
    license = f.read()

runtime_requirements = [
    'pytube==9.2.2',
    'streamlink==0.12.1',
    'google-api-python-client==1.6.4'
]

test_requirements = [
    'mock==2.0.0',
    'pytest==3.6.1'
]

setup(
    name='yt-archiver',
    version='0.5.0',
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
    install_requires=runtime_requirements,
    tests_require=test_requirements,
    extras_require={'test': test_requirements}
)
