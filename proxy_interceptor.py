from mitmproxy import http
from bs4 import BeautifulSoup
import os, json
import pathlib


def create_dir(path):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def path_exists(path):
    return pathlib.Path(path).exists()


class Page:

    def __init__(self, title, html):
        self.title = title
        self.html = html
        self.videos = {}

    def add_video(self, file):
        split_url=str(file[file.find(b"https"):file.find(b"?")]).split('/')
        vid_id = "-".join(split_url[5:7])
        resolution=split_url[-2]
        if not vid_id in self.videos.keys():
            self.videos.update({vid_id: (len(self.videos), file, resolution)})

    def save_to_files(self):

        create_dir(os.path.join(config["output_dir"], self.title))
        print(len(self.videos))
        for i, file, resolution in self.videos.values():
            file_path = os.path.join(config["output_dir"], self.title, f"{i + 1}_{resolution}.m3u")
            if not path_exists(file_path) or config["proxy"]["overwrite_links_files"]:
                with open(file_path, "wb") as f:
                    f.write(file)
                print(f"Saved file to: {file_path}")

        if config["proxy"]["save_html"]:
            html_file_path = os.path.join(config["output_dir"], self.title, "page.html")
            if not path_exists(html_file_path):
                with open(html_file_path, "w") as f:
                    f.write(self.html)
                print(f"Saved HTML to: {html_file_path}")


def response(flow: http.HTTPFlow):
    # Get the name of current lesson
    if config["proxy"]["html_match"] in flow.request.url:  # Adjust URL pattern
        global current_page
        soup = BeautifulSoup(flow.response.text, 'html.parser')
        title_element = soup.find('h2', class_='lesson-title-value')

        if title_element:
            lesson_title = title_element.text.strip().split(".")[0][:config["proxy"]["name_trimming"]]
            print(f"Detected lesson title: {lesson_title}")
            current_page = Page(lesson_title, flow.response.text)

    # add the videos
    if config["proxy"]["playlist_match"] in flow.request.url:
        if isinstance(current_page, Page):
            current_page.add_video(flow.response.content)
            current_page.save_to_files()


with open("config.json") as f:
    config = json.load(f)

if config["proxy"]["name_trimming"] <= 0:
    config["proxy"]["name_trimming"] = None

current_page = None

for path in (config["output_dir"],):
    if not path_exists(path):
        create_dir(path)
