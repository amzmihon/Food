import os
import sys
import threading
import time
import webbrowser

try:
    import webview
except ImportError:
    webview = None  # type: ignore

try:
    from waitress import serve
    from django.core.wsgi import get_wsgi_application
except ImportError as e:
    raise ImportError("Make sure you have installed the required packages: waitress, django.") from e

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meal_tracker.settings')

# Add the project directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Get the WSGI application
application = get_wsgi_application()
APP_URL = 'http://127.0.0.1:8000/daily-meals/'


def run_server():
    serve(application, host='127.0.0.1', port=8000)


def open_ui():
    """
    Try to open the app in an embedded window (pywebview if available),
    otherwise fall back to the default browser and keep the process alive.
    """
    if webview is not None:
        try:
            webview.create_window('Meal Tracker', APP_URL)
            webview.start()
            return
        except Exception:
            # If pywebview fails (missing runtime, etc.), continue to browser fallback
            pass

    webbrowser.open(APP_URL)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    # Start the server in a separate thread
    t = threading.Thread(target=run_server)
    t.daemon = True
    t.start()

    open_ui()
