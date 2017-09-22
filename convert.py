import requests as req
import sys
import os
import json
import re
import youtube_dl
import configparser
import io

from os.path import splitext
from functools import partial
from postprocessor import PythonExecAfterDownloadPP

upload_urls  = {
    'deezer': "https://upload.deezer.com/?sid={}&id={}&resize=1&directory=user&type=audio&referer={}&file={}"
}

def hook(d):
    if d['status'] in ['finished', 'error']:
        db_state(d['status'])

def trunc(s, n=25):
    return len(s) > n and s[:n] or s + (' '*(n-len(s)))

def db_state(state, is_end=False):
    state = state == 'finished' and 'OK' or 'ERROR'
    params = {'flush': True}
    if not is_end:
       params['end'] = ''

    print(trunc(state, 12), **params)

class Logger(object):
    def debug(self, msg):
        if len(msg) > 0 :
            if msg[:8] == 'Deleting':
                # Finished the convert postprocessor
                db_state('finished')
            elif '[' not in [msg[0], msg[2]] and msg[:8] != 'Deleting':
                print(trunc(msg), end='   ')

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)

def prepare_name(file_name):
    result = splitext(file_name)[0]
    result = re.sub(r'[^a-zA-Z0-9 \-]', r'', result)
    result = re.sub(r'\s+',r'+', result)

    return result

def upload(upload_url, file_name):
    try:
        files = {'file': open(file_name, 'rb')}
    except FileNotFoundError as e:
        db_state('error', True)
        # print("{} has not been found".format(file_name))
        return

    url = upload_url.format(prepare_name(file_name))

    try:
        r = req.post(url, files=files)
    except (req.ConnectionError , req.Timeout ) as e:
        db_state('error', True)
        #print('The service is inaccessible, is your internet connection up?')
    else:
        result = r.json()
        if result['error']:
            db_state('error', True)
            #print('NOK file \'{}\': {}'.format(file_name, result['error'].get('message', '')))
        else:
            db_state('finished', True)
            os.remove(file_name)

ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': '%(title)s.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'logger': Logger(),
    'ignoreerrors': True,
    'progress_hooks': [hook],
    'forcetitle': True
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('usage: {} {}'.format(sys.argv[0], 'youtube_urls'))
        exit(1)

    config_file = os.path.expanduser('~/.y2drc')
    if not config_file:
        print('A config file is required')
        exit(1)

    config = configparser.ConfigParser()
    config.read(config_file)

    upload_platform = 'deezer'

    upload_url = upload_urls[upload_platform]
    upload_url = upload_url.format(
        config.get(upload_platform, 'sid'),
        config.get(upload_platform, 'id'),
        config.get(upload_platform, 'referer'),
        '{}')

    upload = partial(upload, upload_url)
    urls = sys.argv[1:]

    print(trunc('Title', 28) + trunc('Download', 12) + trunc('Convert', 12) + trunc('Upload', 12))
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        upload_pp = PythonExecAfterDownloadPP(ydl, upload)
        ydl.add_post_processor(upload_pp)
        ydl.download(urls)
        print()









