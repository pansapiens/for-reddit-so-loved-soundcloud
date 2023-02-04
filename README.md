# RLS (for Reddit so Loved SoundCloud)

RLS searches Reddit, finds posts and comments with links to SoundCloud 
and downloads any tracks it can get (single track, whole artist or set/playlist).

## Features

  * Search for specific keywords by subreddit (eg 'soundcloud CC-BY' in `/r/gamedev`)
  * Allows non-Creative Commons tracks to be excluded (`--free-only`)
  * Creates one directory per artist to keep things organized.
  * Doesn't download tracks again if they already exist locally<sup><strong>*</strong></sup>
  * Downloads album cover art.
  * Downloads SoundCloud metadata for the artist (`metadata.json`).

<small>
* (strictly, this is a feature of the wonderful `youtube-dl` used in the backend that we get for free)
</small>

## Installation
```
virtualenv -p python3 ~/.virtualenvs/rls
source ~/.virtualenvs/rls/bin/activate
python3 setup.py develop

# pip3 install -U -r requirements.txt
```

## Setup

```
cp config.toml.example config.toml
```

Edit config.toml to include required API keys for Reddit (and maybe SoundCloud)

## Usage

See the help message
```
./rls
```

Search `/r/gamedev` for "soundcloud" and "CC-BY" and download any tracks in links to SoundCloud.
```
./rls search gamedev "soundcloud CC-BY"
```

Search `/r/gamedev` for "soundcloud" and "CC-0" and download only free/open licenced tracks.
```
./rls search gamedev "soundcloud CC-0" --free-only
```

Search `/r/futuresynth` for "soundcloud" and "CC-0", only free/open tracks, output to a directory `/tmp/futuresynth`.
```
./rls search futuresynth "soundcloud CC-0" --free-only --output=/tmp/futuresynth
```

Search `/r/dreampop` posts up to one week old for "soundcloud", download linked tracks.
```
./rls search futuresynth "soundcloud" --time=week
```

## A note about music licensing

Please always check and respect the license a musician applies to their music. "Creative Commons" licenses come in different flavours that usually require proper attribution and might restrict commercial use and/or remixing. Read the license and understand it.

Be aware that using the Reddit search term "CC-BY" or "CC-0" etc does not guaranetee that 
the tracks downloaded are free to use, they simply narrow the search to make it more likely
you will find tracks with a Creative Commons license. You should always check the license yourself
on the associated SoundCloud page (or in `metadata.json`) if you plan to reuse a track for some creative purpose. 

Often musicians and composers post links to Reddit with a statement that "these tracks are under a CC-BY license", but fail to update the license on SoundCloud, making the status of the license potetially unclear. 
The `--free-only` flag excludes any tracks licensed as `all-rights-reserved` on SoundCloud, allowing
you to have more certainty that you are downloading only Creative Commons (or similar) licensed tracks.

## TODO / wishlist

  * Make m3u playlists for 'sets'.
