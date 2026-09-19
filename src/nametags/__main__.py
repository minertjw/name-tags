import os
import webview
import logging

from werkzeug.serving import make_server

from nametags.web.app import create_app

def main():
    logging.basicConfig(level=logging.WARN)
    logger = logging.getLogger("nametags")

    host = "127.0.0.1"
    port = int(os.environ.get("NAME_TAGS_PORT", "5000"))
    url = f"http://{host}:{port}/"
    
    app = create_app()

    try:
        server = make_server(host, port, app, threaded=True)
    except OSError as exc:
        raise SystemExit(f"Unable to start the name tag app on {host}:{port}: {exc}") from exc
    
    logger.debug(f"Name Tag Server is running at {url}")

    webview.create_window("Test", url=url, zoomable=True, easy_drag=False)
    webview.start(server.serve_forever, ssl=True, gui="edgechromium")

    server.shutdown()

if __name__ == "__main__":
    main()
