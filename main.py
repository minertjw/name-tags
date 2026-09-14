import os
import threading
import webbrowser

from werkzeug.serving import make_server

from core.web import create_app


def main():
    host = "127.0.0.1"
    port = int(os.environ.get("NAME_TAGS_PORT", "5000"))
    app = create_app()

    try:
        server = make_server(host, port, app, threaded=True)
    except OSError as exc:
        raise SystemExit(f"Unable to start the name tag app on {host}:{port}: {exc}") from exc

    url = f"http://{host}:{port}/"
    print(f"Name Tag Combiner is running at {url}")
    print("Press Ctrl+C to stop.")
    threading.Timer(0.25, webbrowser.open_new_tab, args=(url,)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Name Tag Combiner.")
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
