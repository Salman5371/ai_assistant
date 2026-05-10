import webbrowser
import subprocess
import platform
from urllib.parse import quote_plus


def open_website(url):
    webbrowser.open(url)


def search_google(query):
    search_url = "https://www.google.com/search?q=" + quote_plus(query)
    webbrowser.open(search_url)



def search_youtube(query):
    search_url = "https://www.youtube.com/results?search_query=" + quote_plus(query)
    webbrowser.open(search_url)


def open_app(app_name):
    system = platform.system()

    try:
        if system == "Windows":
            if app_name == "chrome":
                subprocess.Popen("chrome")
            elif app_name == "notepad":
                subprocess.Popen("notepad")
            elif app_name == "calculator":
                subprocess.Popen("calc")

        elif system == "Darwin":
            subprocess.Popen(["open", "-a", app_name])

        elif system == "Linux":
            subprocess.Popen([app_name])

        return True

    except Exception as e:
        print("App open error:", e)
        return False