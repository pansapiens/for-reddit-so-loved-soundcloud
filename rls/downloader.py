#!/usr/bin/env python3
"""rls

Usage:
  rls help
  rls search [options] SUBREDDIT QUERY
  rls grab [options] SOUNDCLOUD_URL

Options:
  -h --help                 Show this help message.
  -v                        Verbose output.
  --free-only               Only download open license tracks (eg CC-BY) [default: False].
  -o PATH, --output=PATH    Download into this directory. Created if it doesn't exist.
  --time=<time_filter>      Search posts this far back in time (all, year, month, week, day) [default: all]


"""
from docopt import docopt
from . import __version__
import logging
import sys
import os
from os import path
from glob import glob
import re
import string
import pdb
import json
import requests
from urllib.parse import urlparse

from attrdict import AttrDict
from toolz import dicttoolz
import pytoml as toml
import youtube_dl
from youtube_dl.extractor.soundcloud import SoundcloudIE
import soundcloud
import praw
import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3

from . import _REDDIT_CLIENT_ID, _REDDIT_CLIENT_SECRET

logger = logging.getLogger(__name__)

urlre = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

config = AttrDict(dict())

def findlinks(text):
    return urlre.findall(text)


def save_image_url(url):
    resp = requests.get(url)
    fn = path.basename(urlparse(url).path)
    with open(fn, 'wb') as fh:
        fh.write(resp.content)
    logger.info("Downloaded: %s\n" % url)
    return fn


def get_artist_from_url(url):
    artist = urlparse(url).path
    if '/' in artist:
        artist = artist.split('/')[1]
    return artist


def download_soundcloud_tracks(sc_url, output_dir=None, free_only=False):
    if output_dir is None:
        output_dir = os.getcwd()
    output_dir = path.normpath(path.abspath(output_dir))
    os.makedirs(output_dir, exist_ok=True)
    os.chdir(output_dir)

    # If /artist only URL, make it /artist/tracks
    if len(urlparse(sc_url).path.strip('/').split('/')) == 1:
        sc_url = "%s/tracks" % sc_url

    client = soundcloud.Client(client_id=config.soundcloud.client_id)

    resp_obj = client.get('/resolve', url=sc_url)
    # pdb.set_trace()
    tracklist = []
    if isinstance(resp_obj, soundcloud.resource.ResourceList):
        # We might have a list of tracks, or a list of sets,
        # each which contains a list of tracks. We want tracklist
        # to be a flat list of tracks.
        for t in resp_obj:
            if 'tracks' in t.obj:
                tracklist.extend([tt for tt in t.obj['tracks']])
            else:
                tracklist.append(t.obj)
    elif isinstance(resp_obj, soundcloud.resource.Resource):
        tracklist = [resp_obj.obj]

    # pdb.set_trace()

    if not tracklist:
        logger.info("No tracks found.\n")

    if logger.level <= logging.DEBUG:
        sys.stderr.write("%s\n\n" % json.dumps(tracklist, indent=2))

    # artist = get_artist_from_url(sc_url)
    artist = tracklist[0]['user']['permalink']

    artist_path = path.join(output_dir, artist)
    os.makedirs(artist_path, exist_ok=True)
    os.chdir(artist_path)

    with open('metadata.json', 'w') as fh:
        fh.write(json.dumps(tracklist, indent=2))

    if tracklist:
        save_image_url(tracklist[0]['user']['avatar_url'])

    for t in tracklist:
        license = t.get('license', None)
        if license == 'all-rights-reserved' and free_only:
            continue

        artwork = t.get('artwork_url', None)
        artwork_filename = None
        if artwork:
            artwork_filename = save_image_url(artwork)

        track_uri = t.get('uri', None)
        if track_uri:
            # os.system('youtube-dl --audio-format best "%s"' % track_uri)
            ydl_opts = {'format': 'bestaudio/best'} #,
                        #'output': out_filename}
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                exit_code = ydl.download([track_uri])

            if exit_code == 0:
                filematches = glob('*-%s.*' % t['id'])
                if filematches:
                    out_filename = filematches.pop()
                    tag_file(t, out_filename, artwork_filename=artwork_filename)
                else:
                    logger.error("Couldn't find output file for: %s" % t['id'])
            else:
                logger.error("Failed to download: %s" % track_uri)


def tag_file(t, out_filename, artwork_filename=None):
    # Create an ID3 tag
    if out_filename.endswith('.mp3'):
        audio = ID3()
        if artwork_filename:
            with open(artwork_filename, 'rb') as art_image:
                audio['APIC'] = mutagen.id3.APIC(
                    encoding=3, mime='image/jpeg', type=3, desc='Cover',
                    data=art_image.read()
                )
        audio.save(out_filename)
        # Reopen using the easy interface
        audio = EasyID3(out_filename)

    elif out_filename.endswith('.ogg'):
        audio = mutagen.File(out_filename)
    else:
        return

    audio['title'] = t.get('title', '')
    audio['artist'] = "%s (%s)" % (t['user'].get('username', ''),
                                   t['user'].get('permalink', ''))
    audio['copyright'] = t['license']
    audio['date'] = t.get('created_at', '')
    audio['genre'] = t.get('genre', '')
    audio['website'] = t.get('permalink_url', '')
    # audio['length'] = int(t.get('duration', 0))
    audio.save(out_filename)


def find_links(subreddit_name, query,
               time_filter='all',
               domains=None):
    logger.info("Searching /r/%s for links ('%s', time=%s)." % (subreddit_name, query, time_filter))

    if domains is None:
        domains = ['soundcloud.com']

    reddit = praw.Reddit(user_agent='RLS (Reddit Loves SoundCloud) (/u/pansapiens)',
                         client_id=config.reddit.client_id,
                         client_secret=config.reddit.client_secret)
    subreddit = reddit.subreddit(subreddit_name)
    links = []
    for post in subreddit.search(query,
                                 sort='top',
                                 time_filter=time_filter,
                                 syntax='plain'):
        links.extend(findlinks(post.title))
        links.extend(findlinks(post.url))
        links.extend(findlinks(post.selftext))
        post.comment_sort = 'top'
        post.comments.replace_more(limit=0)
        for comment in post.comments.list():
            links.extend(findlinks(comment.body))

    links = set(links)

    sc_links = []
    for domain in domains:
        links_ = list(filter(lambda l: domain in l.lower(), links))

        links__ = []
        for l in links_:
            if '(http' in l:
                links__.extend(l.split('('))
            else:
                links__.append(l)

        sc_links.extend([l.strip().strip(string.punctuation) for l in links__])

    return set(sc_links)


def single(sc_url, output_dir=None, free_only=False):
    if not sc_url.startswith('http://') and not sc_url.startswith('https://'):
        sc_url = "http://soundcloud.com/%s" % sc_url

    download_soundcloud_tracks(sc_url, output_dir=output_dir, free_only=free_only)


def search(subreddit='gamedev', query='soundcloud CC-BY',
           time_filter='all',
           output_dir=None, free_only=False):

    if output_dir is None:
        output_dir = os.getcwd()

    output_dir = path.join(output_dir, subreddit)

    sc_links = find_links(subreddit, query, time_filter=time_filter)
    if not sc_links:
        logger.info("No links found :/")
    else:
        logger.debug("Links: %s" % sc_links)

    for link in sc_links:
        logger.info("Grabbing: %s\n" % link)
        try:
            download_soundcloud_tracks(link, output_dir=output_dir, free_only=free_only)
        except Exception as ex:
            logger.info("Failed on: %s\n" % link)
            logger.exception(ex)

    logger.info("Done !")


def set_config_defaults(config):
    soundcloud_config = {'soundcloud':
                             {'client_id': SoundcloudIE._CLIENT_ID}}
    reddit_config = {'reddit':
                         {'client_id': _REDDIT_CLIENT_ID,
                          'client_secret': _REDDIT_CLIENT_SECRET}}
    config = dicttoolz.merge(soundcloud_config, reddit_config, config)
    return AttrDict(config)


def run_in_console():
    global config

    args = AttrDict(docopt(__doc__, version='rls %s' % __version__))
    # print(args)
    # sys.exit()
    # print(args.search)

    if args.help:
        print(docopt(__doc__, argv=['--help']))
        sys.exit()

    with open('config.toml', 'r') as fh:
        config = AttrDict(toml.load(fh))

    config = set_config_defaults(config)

    # print(config.soundcloud.client_id)

    logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.INFO)
    logger.setLevel(level=logging.INFO)
    if args['-v']:
        logger.setLevel(logging.DEBUG)

    output_dir = None
    if args['--output']:
        output_dir = path.normpath(path.abspath(args['--output']))
    else:
        output_dir = os.getcwd()

    if args.search:
        time_filter = args['--time']
        if time_filter not in ['all', 'year', 'month', 'week', 'day']:
            logger.error("Invalid --time, must be one of all, year, month, week or day.")
            sys.exit(1)

        search(args.SUBREDDIT, args.QUERY,
               time_filter=time_filter,
               output_dir=output_dir,
               free_only=args['--free-only'])
    elif args.grab:
        single(args.SOUNDCLOUD_URL, output_dir=output_dir,
               free_only=args['--free-only'])


if __name__ == '__main__':
    run_in_console()
