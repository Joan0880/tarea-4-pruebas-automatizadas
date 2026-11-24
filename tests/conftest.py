from __future__ import annotations

import os
import re
import socket
import sqlite3
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "evidencias"
SCREENSHOT_DIR = REPORT_DIR / "capturas"


@pytest.fixture(scope="session")
def database_path(tmp_path_factory):
    return tmp_path_factory.mktemp("aurora-selenium") / "biblioteca-test.db"


@pytest.fixture(scope="session")
def server_url(database_path):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    server_log = database_path.with_suffix(".server.log")
    env = os.environ.copy()
    env.update({"DATABASE_PATH": str(database_path), "PORT": str(port), "HOST": "127.0.0.1"})
    with server_log.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [sys.executable, str(ROOT / "app.py")],
            cwd=ROOT,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
    try:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"La aplicación se cerró. Registro: {server_log.read_text(encoding='utf-8')}")
            try:
                with urllib.request.urlopen(url + "/login", timeout=1):
                    break
            except Exception:
                time.sleep(0.2)
        else:
            raise RuntimeError(f"La aplicación no inició a tiempo. Registro: {server_log.read_text(encoding='utf-8')}")
        yield url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


@pytest.fixture
def library(database_path, server_url):
    """Start each scenario with the same three predictable books."""
    with sqlite3.connect(database_path) as db:
        db.execute("DELETE FROM books")
        db.execute("DELETE FROM sqlite_sequence WHERE name = 'books'")
        db.executemany(
            "INSERT INTO books (title, author, genre, year) VALUES (?, ?, ?, ?)",
            [
                ("Cien años de soledad", "Gabriel García Márquez", "Realismo mágico", 1967),
                ("La casa de los espíritus", "Isabel Allende", "Novela", 1982),
                ("Ficciones", "Jorge Luis Borges", "Cuento", 1944),
            ],
        )
    return database_path


@pytest.fixture
def driver(server_url, request):
    options = Options()
    if os.environ.get("HEADLESS", "true").lower() not in {"0", "false", "no"}:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1000")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--lang=es")
    browser = webdriver.Chrome(options=options)
    browser.implicitly_wait(1)
    browser.set_page_load_timeout(15)
    request.node._selenium_driver = browser
    yield browser
    browser.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return
    browser = getattr(item, "_selenium_driver", None)
    if browser is None:
        return

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", item.name).strip("_")
    target = SCREENSHOT_DIR / f"{slug}.png"
    try:
        browser.save_screenshot(str(target))
        try:
            from pytest_html import extras

            report.extras = getattr(report, "extras", [])
            report.extras.append(
                extras.image(browser.get_screenshot_as_base64(), mime_type="image/png", name="Captura del escenario")
            )
        except (ImportError, AttributeError):
            report.sections.append(("Captura Selenium", str(target.relative_to(ROOT))))
    except Exception as error:
        report.sections.append(("Error al guardar captura", str(error)))
