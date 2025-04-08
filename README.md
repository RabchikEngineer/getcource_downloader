# Video Downloader for M3U/EXTM3U files

## 1. Getting started
1. Install the dependencies
`pip install -r requirements.txt`


2. Put your files to the `links` directory (try firstly 3 or create if missing)


3. Run "py downloader.py"


4. Get your videos from the `videos` directory


## 2. Automatically gather playlist files

1. Set up your browser proxy settings to `127.0.0.1:8080`\
(you can change that in the `proxy.sh` file)


2. Start the `proxy.sh` script in the terminal


3. Browse the pages, and start playing the video on each.\
the files will appear directly in the `links` directory


4. If not, check for the match URLs in `config.json`


## 3. Current issues and notes

1. Since video is downloaded by chunks, each chunk may cause data loss.\
As a result we have randomly appeared distortions. It appears on +- 20% of chunk's junctions


2. ~~We still have to download the M3U files by hands from the browser console~~\
partially works, but improvements about recognition of lesson name are required

