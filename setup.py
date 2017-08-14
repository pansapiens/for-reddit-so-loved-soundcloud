from os import path
from distutils.core import setup
from setuptools import find_packages
from rls import __version__
here = path.abspath(path.dirname(__file__))


def get_requirements():
    from pip.req import parse_requirements
    from pip.download import PipSession

    # parse_requirements() returns generator of pip.req.InstallRequirement
    # objects
    pip_reqs = parse_requirements(path.join(here, 'requirements.txt'),
                                  session=PipSession())
    # reqs is a list of requirements
    requirements = [str(ir.req) for ir in pip_reqs]

    return requirements


setup(
    name='rls',
    version=__version__,
    packages=[''],
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
    install_requires=get_requirements(),
    entry_points={
        'console_scripts': [
            'rls=rls.downloader:run_in_console',
        ],
    },
)
