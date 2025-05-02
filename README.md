# Video Downloader for M3U/EXTM3U files

## 1. Getting started
1. Install the dependencies
`pip install -r requirements.txt`


2. Run `py downloader.py` or `./downloader.py`(doesn't work with venv)\
to create necessary dirs 


## 2. Manual downloading

1. Put your playlist files to the `output` directory (create if missing)\
or in some subdirectory


2. Run `downloader`


3. Your videos will be placed along with playlist files


## 3. Automatically gather playlist files, videos, and html

1. Set up your browser proxy settings to `127.0.0.1:8080`\
(you can change that in the `proxy.sh` file)


2. Run `./proxy.sh` in the terminal 


3. Browse the pages, and start playing the video on each. Notes:\
Data saved to `output` dir.\
Script will create **subdirs** named the same as lesson title on page\
You can toggle html downloading in the `config.json`\
It will save **separate file** for each **resolution** of video you played.\
If you doesn't want some of them, you need to **manually** remove files,\
otherwise they will be downloaded.


4. If not, check for the match URLs in `config.json`


5. Run `downloader` to download videos. It will find links automatically\
Note that video resolution is highly determines it size, up to 2x between 480 and 720


## 4. Current issues and notes

1. Since video is downloaded by chunks, each chunk may cause data loss.\
As a result we have randomly appeared distortions. It appears on +- 20% of chunk's junctions


2. The match URLs seems not to be universal, improvements are accepted
