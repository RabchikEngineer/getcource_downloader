from mitmproxy import http
from bs4 import BeautifulSoup
import os, json
import pathlib


def create_dir(path):
    pathlib.Path(path).mkdir(parents=True, exist_ok=False)


def path_exists(path):
    return pathlib.Path(path).exists()


def response(flow: http.HTTPFlow):
    # Get the name of current lesson
    if config["proxy"]["html_match"] in flow.request.url:  # Adjust URL pattern
        global current_title, current_html
        soup = BeautifulSoup(flow.response.text, 'html.parser')
        title_element = soup.find('h2', class_='lesson-title-value')

        if title_element:
            lesson_title = title_element.text.strip().split(".")[0][:config["proxy"]["name_trimming"]]
            print(f"Detected lesson title: {lesson_title}")
            current_title = lesson_title

        current_html=flow.response.text


    # Download the file
    if config["proxy"]["playlist_match"] in flow.request.url:
        filename = current_title
        file_path = os.path.join(config["links_dir"], filename)

        # save file with name of current lesson
        with open(file_path, "wb") as f:
            f.write(flow.response.content)
        print(f"Saved file to: {filename}")

        if config["proxy"]["save_html"]:
            html_file_path = os.path.join(config["html_dir"], f"{current_title}.html")
            with open(html_file_path, "w") as f:
                f.write(current_html)
            print(f"Saved HTML to: {html_file_path}")


with open("config.json") as f:
    config = json.load(f)

if config["proxy"]["name_trimming"]<=0:
    config["proxy"]["name_trimming"]=None

current_title: str = ""
current_html = None

for path in (config["html_dir"],):
    if not path_exists(path):
        create_dir(path)
