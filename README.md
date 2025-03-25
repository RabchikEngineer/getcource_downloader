# Video Downloader for M3U/EXTM3U files

## 1. Getting started
1. Install the dependencies
`pip install -r requirements.txt`


2. Put your files to the `links` directory (try firstly 3 or create if missing)


3. Run "py downloader.py"


4. Get your videos from the `videos` directory

## 2. Current issues and notes

1. Since video is downloaded by chunks, each chunk may cause data loss.\
As a result we have randomly appeared distortions. It appears on +- 20% of chunk's junctions


3. We still have to download the M3U files by hands from the browser console\
Improvements are encouraged