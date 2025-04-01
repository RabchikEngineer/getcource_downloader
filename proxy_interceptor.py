from mitmproxy import http
from bs4 import BeautifulSoup
import os

current_title:str=""
links_dir:str="links"

def response(flow: http.HTTPFlow):

    # Get the name of current lesson
    if "teach/control/lesson/" in flow.request.url:  # Adjust URL pattern
        global current_title, current_players_count
        soup = BeautifulSoup(flow.response.text, 'html.parser')
        title_element = soup.find('h2', class_='lesson-title-value')
        if title_element:
            lesson_title = title_element.text.strip().split(".")[0][:10]
            print(f"Detected lesson title: {lesson_title}")
            current_title = lesson_title

    # Download the file
    if "getcourse.ru/api/playlist/media" in flow.request.url:

        filename = current_title
        file_path=os.path.join(links_dir, filename)

        # save file with name of current lesson
        with open(file_path, "wb") as f:
            f.write(flow.response.content)
        print(f"Saved file to: {filename}")



