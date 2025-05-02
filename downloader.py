#! usr/bin/python3
import os, sys, time, math, json
import requests
import threading as th
from concurrent import futures
from loguru import logger
import subprocess
import pathlib
import shutil
import glob
import tempfile
from addict import Dict

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.live import Live
from rich.text import Text

# filename='480_12_1'
# log_format = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {message}'
log_format = '[green]{time:HH:mm:ss}[/green] | [level]{level: <8}[/level] |.................... {message}'


def create_dir(path):
    try:
        pathlib.Path(path).mkdir(parents=True, exist_ok=False)
        logger.info(f"Created directory {path}")
    except FileExistsError:
        logger.trace(f"Directory {path} already exists")
    except:
        logger.error(f"Error creating directory {path}")
        sys.exit(1)


def path_exists(path):
    return pathlib.Path(path).exists()


def list_filenames(path):
    return [f"file '{x}'" for x in sorted(filter(lambda x: x.endswith('bin'), os.listdir(path)),
                                          key=lambda x: int(x.split('.')[0]))]


def get_active_downloads_panel():
    with active_downloads_lock:
        if active_downloads:
            content = "\n".join([f"{filename:20} --- " +
                                 (lambda
                                      time_val: f"{int(time_val)}s" if time_val < 10 else f"[red]{int(time_val)}s[/red]")
                                 (time.time() - active_downloads[filename]) for filename in active_downloads.keys()])
        else:
            content = "No active downloads"
    return Panel(content, title="Active Downloads", border_style="green")


def make_layout() -> Layout:
    layout = Layout()
    layout.split_row(
        Layout(ratio=2),
        Layout(get_active_downloads_panel(), ratio=1)
    )
    layout.children[0].split_column(
        Layout(Panel(progress, title=f"Downloading videos")),
        Layout(renderable=Panel(title="Actions",
                                renderable=Text(text="dd" * 100, no_wrap=True, overflow="ellipsis")), ratio=2)
        # Text(no_wrap=True, overflow="ellipsis")
    )
    return layout


class LogString():
    size = 10
    text = ""
    lines = []

    def __call__(self, text):
        self.lines.append(text)
        while len(self.lines) > self.size:
            self.lines.pop(0)
        self.text = "".join(self.lines)

    def set_size(self, size):
        self.size = size


def list_links_filenames():
    return glob.glob("**/*.m3u", root_dir=output_dir, recursive=True)


def updater(once=False):
    while True:
        layout.children[1].update(get_active_downloads_panel())

        layout.children[0].children[1].renderable.renderable = (
            layout.children[0].children[1].renderable.renderable.from_markup(log_string.text, overflow="ignore"))

        if once:
            return

        time.sleep(1 / 4)


class VideoDownloader:

    def __init__(self, links_path):
        self.links_path = links_path
        self.dirname = '/'.join(links_path.split('/')[:-1])
        self.filename = links_path.split('/')[-1].split(".")[0]
        self.temp_dir = os.path.join(temp_dir, tempfile.mkdtemp())
        self.task_id = 0

    def extract_links(self):
        with open(os.path.join(output_dir, self.links_path)) as f:
            links = list(filter(lambda x: x.startswith('http'), f.readlines()))
        return links

    def download_file(self, link, chunk_filename):
        status_code = 0

        if path_exists(chunk_filename):
            logger.trace(f"{chunk_filename} already exists")
            progress.advance(self.task_id, 1)
            return

        try:

            with active_downloads_lock:
                active_downloads.update({chunk_filename: time.time()})

            while status_code != 200:
                resp = requests.get(link, timeout=30)
                status_code = resp.status_code

            with open(chunk_filename, 'wb') as f:
                f.write(resp.content)

            logger.trace(f"{chunk_filename} downloaded")
            progress.advance(self.task_id, 1)

        except requests.exceptions.RequestException:
            logger.trace(f'error while downloading {chunk_filename}, retrying')
            self.download_file(link, chunk_filename)
            return

        with active_downloads_lock:
            del active_downloads[chunk_filename]

    def extract_chunk_paths(self, links):
        for link in links:
            yield os.path.join(self.temp_dir, link[link.rfind('/') + 1:link.find('?')])

    def download_video(self):

        dirname = self.dirname
        filename = self.filename
        video_filepath = os.path.join(output_dir, dirname, f'{self.filename}.mp4')

        if path_exists(video_filepath):
            logger.warning(f"{video_filepath} already exists")
            return
        # pathlib.Path(video_filepath).unlink(missing_ok=True)

        # links = self.extract_links()[:50]
        links = self.extract_links()

        task_id = progress.add_task(f"Downloading {dirname}/{filename}", total=len(links))
        self.task_id = task_id
        if len(progress.tasks) > progressbar_count:
            progress.remove_task(progress.task_ids[0])

        with futures.ThreadPoolExecutor(max_workers=20) as executor:
            result = executor.map(self.download_file, links, self.extract_chunk_paths(links))
            for _ in result:
                pass
                # progress.advance(task_id,1)

        with open(os.path.join(self.temp_dir, "list.txt"), 'w') as f:
            f.write('\n'.join(list_filenames(self.temp_dir)))

        try:
            # proc=subprocess.Popen(['ffmpeg', '-f','concat','-i',os.path.join(temp_dir, filename, "list.txt"),'-c','copy',
            #                 video_filepath],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
            proc = subprocess.Popen(
                ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', os.path.join(self.temp_dir, "list.txt"), '-c:v',
                 'copy', '-c:a', 'copy',
                 '-movflags', '+faststart', video_filepath], stdin=subprocess.PIPE, stderr=subprocess.PIPE)

        except subprocess.SubprocessError:
            logger.error('Conversion failed')
            sys.exit(1)

        logger.info('Conversion started')
        proc.stdin.write("y".encode('utf-8'))
        proc.wait()
        result = proc.communicate()[1].decode('utf-8')
        logger.info(result.split('\n')[-2])

        logger.success(f"{video_filepath} downloaded and converted")
        shutil.rmtree(self.temp_dir)
        logger.info('temp files deleted')


with open("config.json") as f:
    config = Dict(json.load(f))

output_dir: str = config.output_dir
temp_dir: str = config.temp_dir
downloaded_mark = config.downloader.downloaded_mark

log_string = LogString()

logger.remove()
logger.add(log_string, level=9, format=log_format)
logger.add("log.txt", level=1, format=log_format)

active_downloads = dict()
active_downloads_lock = th.Lock()

console = Console()

progress = Progress(
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TimeElapsedColumn(),
    TimeRemainingColumn(),
)

try:
    subprocess.check_call(["ffmpeg", '-h'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except subprocess.CalledProcessError:
    logger.error("Could not find ffmpeg, install and add it to your PATH")
    sys.exit(1)

for path in (output_dir, temp_dir):
    if not path_exists(path):
        create_dir(path)

layout = make_layout()

th.Thread(target=updater, daemon=True).start()

try:

    links_filenames = list_links_filenames()

    with Live(layout, refresh_per_second=4, console=console):

        if not links_filenames:
            logger.error("No M3U/EXTM3U files found.")
            updater(once=True)
            sys.exit(0)

        while links_filenames:

            links_filename = links_filenames.pop(0)

            terminal_size = console.size

            log_string.set_size(math.floor(terminal_size.height / 3 * 2) - 3)
            progressbar_count = int(terminal_size.height / 3) - 3

            downloader = VideoDownloader(links_filename)
            downloader.download_video()

            shutil.move(os.path.join(output_dir, links_filename),
                        os.path.join(output_dir, links_filename + downloaded_mark))

            new_links_filenames = list_links_filenames()

            diff = set(new_links_filenames) - set(links_filenames)
            if diff:
                logger.success(f"files {' '.join(diff)} added to download")
            links_filenames = new_links_filenames


except KeyboardInterrupt:
    logger.info("Exiting...")
    # updater(once=True)
