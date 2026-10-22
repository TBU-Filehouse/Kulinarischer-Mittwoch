"""Lokaler Einstiegspunkt: ``python -m app``."""

import os

from . import create_app


def main() -> None:
    app = create_app()
    port = int(os.environ.get("KUMI_PORT", app.config["PORT"]))
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
