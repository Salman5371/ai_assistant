import webbrowser
import subprocess
import platform

def open_website(url):
    webbrowser.open(url)

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