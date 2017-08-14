from os import path
from distutils.core import setup
from setuptools import find_packages

# from rls import __version__
__version__ = '0.1.2'

here = path.abspath(path.dirname(__file__))

setup(
    name='rls',
    version=__version__,
    packages=['rls'],
    url='http://github.com/pansapiens/rls',
    license='MIT',
    author='Andrew Perry',
    author_email='ajperry@pansapiens.com',
    description='Downloads SoundCloud tracks linked from Reddit',
    keywords="SoundCloud Reddit music mp3 download",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        'Topic :: Multimedia :: Sound/Audio',
        'Operating System :: POSIX :: Linux',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    download_url='https://github.com/pansapiens/'
                 'for-reddit-so-loved-soundcloud/'
                 'archive/%s.tar.gz' % __version__,
    # install_requires=get_requirements(),
    install_requires=[
        'attrdict',
        'docopt',
        'mutagen',
        'praw',
        'pytoml',
        'soundcloud',
        'toolz',
        'youtube-dl',
    ],
    entry_points={
        'console_scripts': [
            'rls=rls.downloader:run_in_console',
        ],
    },
)
