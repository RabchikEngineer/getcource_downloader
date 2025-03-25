import os, sys, time, math
import requests
import threading as th
from concurrent import futures
from loguru import logger
import subprocess
import pathlib
import shutil

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.live import Live
from rich.text import Text

links_dir='links/'
temp_dir='temp/'
videos_dir='videos/'


# filename='480_12_1'
# log_format = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {message}'
log_format = '[green]{time:HH:mm:ss}[/green] | [level]{level: <8}[/level] |.................... {message}'





def extract_links(filename):
    with open(os.path.join(links_dir+filename)) as f:
        links=list(filter(lambda x: x.startswith('http'), f.readlines()))
    return links


def download_file(link, filename):
    status_code=0

    if path_exists(filename):
        logger.trace(f"{filename} already exists")
        return

    with active_lock:
        active_downloads.update({filename:time.time()})

    while status_code != 200:
        resp = requests.get(link)
        status_code=resp.status_code

    with open(filename, 'wb') as f:
        f.write(resp.content)

    # print(f"{filename} downloaded")
    logger.trace(f"{filename} downloaded")

    with active_lock:
        del active_downloads[filename]



def extract_filenames(links, filename):
    for link in links:
        yield os.path.join(temp_dir,filename,link[link.rfind('/') + 1:link.find('?')])


def list_filenames(path):
    return [f"file '{x}'" for x in sorted(filter(lambda x: x.endswith('bin'),os.listdir(path)),
                                                     key=lambda x: int(x.split('.')[0]))]


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


def get_active_panel():
    """Return a Panel showing current active downloads."""
    with active_lock:
        if active_downloads:
            content = "\n".join([f"{filename:20} --- "+
                 (lambda time_val: f"{int(time_val)}s" if time_val<10 else f"[red]{int(time_val)}s[/red]")
                 (time.time()-active_downloads[filename]) for filename in active_downloads.keys()])
        else:
            content = "No active downloads"
    return Panel(content, title="Active Downloads", border_style="green")


def make_layout() -> Layout:
    """Create a layout with two columns: progress on the left, active downloads on the right."""
    layout = Layout()
    layout.split_row(
        Layout(ratio=2),
        Layout(get_active_panel(), ratio=1)
    )
    layout.children[0].split_column(
        Layout(Panel(progress, title=f"Downloading videos")),
        Layout(renderable=Panel(title="Actions", renderable=Text(text="dd"*100,no_wrap=True, overflow="ellipsis")),ratio=2) # Text(no_wrap=True, overflow="ellipsis")
    )
    return layout


class LogString():
    size=10
    text=""
    lines=[]

    def __call__(self, text):
        self.lines.append(text)
        while len(self.lines)>self.size:
            self.lines.pop(0)
        self.text="".join(self.lines)
        # print(self.lines)

    def set_size(self, size):
        self.size=size


def updater(once=False):
    while True:
        layout.children[1].update(get_active_panel())
        # text=layout.children[0].children[1].renderable.renderable
        # print(log_string.text)

        # Text().from_markup()

        layout.children[0].children[1].renderable.renderable=(
            layout.children[0].children[1].renderable.renderable.from_markup(log_string.text,overflow="ignore"))

        if once:
            return

        time.sleep(1/4)


def download_video(filename):

    video_filename=os.path.join(videos_dir, filename+'.mp4')
    if path_exists(video_filename):
        logger.warning(f"{filename}.mp4 already exists")
        return
    # pathlib.Path(video_filename).unlink(missing_ok=True)


    # links = extract_links(filename)[:50]
    links = extract_links(filename)

    task_id = progress.add_task(f"Downloading {filename}", total=len(links))
    if len(progress.tasks)>progressbar_count:
        progress.remove_task(progress.task_ids[0])

    create_dir(os.path.join(temp_dir,filename))


    with futures.ThreadPoolExecutor(max_workers=20) as executor:
        result=executor.map(download_file, links, extract_filenames(links, filename))
        for _ in result:
            pass
            progress.advance(task_id,1)


    with open(os.path.join(temp_dir, filename, "list.txt"), 'w') as f:
        f.write('\n'.join(list_filenames(os.path.join(temp_dir, filename))))

    # subprocess.run(['ffmpeg', '-f','concat','-i',os.path.join(temp_dir, filename, "list.txt"),'-c','copy',
    #                 video_filename],capture_output=True, input="y".encode('utf-8'))

    try:
        # proc=subprocess.Popen(['ffmpeg', '-f','concat','-i',os.path.join(temp_dir, filename, "list.txt"),'-c','copy',
        #                 video_filename],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
        proc=subprocess.Popen(['ffmpeg', '-f','concat','-safe','0','-i',os.path.join(temp_dir, filename, "list.txt"),'-c:v','copy','-c:a','copy',
                               '-movflags','+faststart',video_filename],stdin=subprocess.PIPE,stderr=subprocess.PIPE)

    except subprocess.SubprocessError:
        logger.error('Conversion failed')
        sys.exit(1)

    logger.info('Conversion started')
    proc.stdin.write("y".encode('utf-8'))
    proc.wait()
    result=proc.communicate()[1].decode('utf-8')
    logger.info(result.split('\n')[-2])

    logger.success(f"{filename}.mp4 downloaded and converted")
    # shutil.rmtree(os.path.join(temp_dir, filename))
    # logger.info('temp files deleted')


log_string=LogString()

logger.remove()
logger.add(log_string, level=9, format=log_format)
logger.add("log.txt", level=1, format=log_format)

active_downloads = dict()
active_lock = th.Lock()


console = Console()

progress = Progress(
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TimeElapsedColumn(),
    TimeRemainingColumn(),
)


try:
    subprocess.check_call(["ffmpeg",'-h'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except subprocess.CalledProcessError:
    logger.error("Could not find ffmpeg, install and add it to your PATH")
    sys.exit(1)


for path in (links_dir, temp_dir, videos_dir):
    if not path_exists(path):
        create_dir(path)


layout = make_layout()


th.Thread(target=updater,daemon=True).start()
# time.sleep(10)


try:

    links_files = os.listdir(links_dir)


    with Live(layout, refresh_per_second=4, console=console):

        if not links_files:
            logger.error("No M3U/EXTM3U files found in the links directory.")
            updater(once=True)
            sys.exit(0)


        for filename in links_files:

            terminal_size = console.size

            log_string.set_size(math.floor(terminal_size.height/3*2)-3)
            progressbar_count=int(terminal_size.height/3)-3

            download_video(filename)

except KeyboardInterrupt:
    # layout.children[0].children[1].renderable.renderable="EXITING..."
    logger.info("Exiting...")
    # updater(once=True)
