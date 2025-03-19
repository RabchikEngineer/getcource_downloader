import os, sys
import requests
import threading as th
from concurrent import futures
from loguru import logger
import subprocess
from tqdm import tqdm
import pathlib
import shutil

links_dir='links/'
temp_dir='temp/'
videos_dir='videos/'

# filename='480_12_1'

log_format = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {message}'
logger.remove()
logger.add(sys.stdout, level=10, format=log_format)
logger.add("log.txt", level=1, format=log_format)


def extract_links(filename):
    with open(os.path.join(links_dir+filename)) as f:
        links=list(filter(lambda x: x.startswith('http'), f.readlines()))
    return links


def download_file(link, filename):
    status_code=0

    if path_exists(filename):
        logger.trace(f"{filename} already exists")
        return
    while status_code != 200:
        resp = requests.get(link)
        status_code=resp.status_code

    with open(filename, 'wb') as f:
        f.write(resp.content)

    # print(f"{filename} downloaded")
    logger.trace(f"{filename} downloaded")



def extract_filenames(links, filename):
    for link in links:
        yield os.path.join(temp_dir,filename,link[link.rfind('/') + 1:link.find('?')])


def list_filenames(path):
    return [f"file '{x}'" for x in sorted(filter(lambda x: x.endswith('bin'),os.listdir(path)),
                                                     key=lambda x: int(x.split('.')[0]))]


def create_dir(path):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)

def path_exists(path):
    return pathlib.Path(path).exists()


def download_video(filename):

    video_filename=os.path.join(videos_dir, filename+'.mp4')
    if path_exists(video_filename):
        logger.warning(f"{filename}.mp4 already exists")
        return

    links = extract_links(filename)

    progress_bar = tqdm(total=len(links), desc=f"Downloading {filename}")

    create_dir(os.path.join(temp_dir,filename))

    with futures.ThreadPoolExecutor(max_workers=20) as executor:
        result=executor.map(download_file, links, extract_filenames(links, filename))
        for _ in result:
            progress_bar.update(1)

    progress_bar.close()

    with open(os.path.join(temp_dir, filename, "list.txt"), 'w') as f:
        f.write('\n'.join(list_filenames(os.path.join(temp_dir, filename))))

    subprocess.run(['ffmpeg', '-f','concat','-i',os.path.join(temp_dir, filename, "list.txt"),'-c','copy',
                    video_filename])

    logger.success(f"{filename}.mp4 downloaded and converted")
    shutil.rmtree(os.path.join(temp_dir, filename))
    logger.info('temp files deleted')


for filename in os.listdir(links_dir):
    download_video(filename)