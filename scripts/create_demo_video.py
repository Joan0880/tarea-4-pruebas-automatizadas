"""Create a short MP4 evidence reel from the latest Selenium HTML report."""

from __future__ import annotations

import json
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "evidencias" / "reporte.html"
SCREENSHOTS = ROOT / "evidencias" / "capturas"
OUTPUT = ROOT / "evidencias" / "video-demo.mp4"
SIZE = (1280, 720)
FPS = 12

STORIES = {
    "us01": "US-01 · Inicio de sesión",
    "us02": "US-02 · Agregar libros",
    "us03": "US-03 · Consultar y buscar",
    "us04": "US-04 · Actualizar libros",
    "us05": "US-05 · Eliminar libros",
}


class ReportData(HTMLParser):
    def __init__(self):
        super().__init__()
        self.value = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if attributes.get("id") == "data-container":
            self.value = attributes.get("data-jsonblob")


def font(size: int, bold: bool = False):
    candidates = [
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def report_results() -> dict[str, str]:
    if not REPORT.exists():
        raise SystemExit("No existe evidencias/reporte.html. Ejecuta primero python -m pytest.")
    parser = ReportData()
    parser.feed(REPORT.read_text(encoding="utf-8"))
    if not parser.value:
        raise SystemExit("No pude leer los resultados del reporte HTML.")
    tests = json.loads(parser.value).get("tests", {})
    results = {nodeid.split("::")[-1]: rows[-1].get("result", "") for nodeid, rows in tests.items() if rows}
    if not results or any(result != "Passed" for result in results.values()):
        raise SystemExit("El video solo se genera cuando todos los escenarios del reporte están aprobados.")
    return results


def label_for(test_name: str) -> tuple[str, str]:
    parts = test_name.split("_")
    story_key = parts[1]
    story = STORIES.get(story_key, story_key.upper())
    scenario = test_name
    for prefix in (
        f"test_{story_key}_login_",
        f"test_{story_key}_crear_libro_",
        f"test_{story_key}_busqueda_",
        f"test_{story_key}_editar_libro_",
        f"test_{story_key}_eliminar_libro_",
        f"test_{story_key}_eliminar_",
    ):
        if scenario.startswith(prefix):
            scenario = scenario[len(prefix):]
            break
    scenario = scenario.replace("_", " ").strip().capitalize()
    scenario_key = scenario.casefold()
    if "camino feliz" in scenario_key:
        category = "CAMINO FELIZ"
    elif any(word in scenario_key for word in ("limite", "último", "ultimo")):
        category = "PRUEBA DE LÍMITES"
    else:
        category = "PRUEBA NEGATIVA"
    return story, f"{category} · {scenario}"


def title_card(title: str, subtitle: str, index: str | None = None) -> Image.Image:
    image = Image.new("RGB", SIZE, "#f5f4ef")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((54, 48, 1226, 672), radius=22, fill="#ffffff", outline="#e4e1d8", width=2)
    draw.rounded_rectangle((54, 48, 1226, 62), radius=7, fill="#526d52")
    draw.text((104, 177), "BIBLIOTECA AURORA", font=font(17, True), fill="#526d52")
    draw.text((104, 236), title, font=font(48, True), fill="#24251f")
    draw.multiline_text((106, 320), subtitle, font=font(23), fill="#74756e", spacing=12)
    draw.rounded_rectangle((104, 466, 1176, 468), radius=1, fill="#e8e5de")
    draw.text((104, 506), "TAREA 4 · PRUEBAS AUTOMATIZADAS CON SELENIUM", font=font(15, True), fill="#526d52")
    if index:
        draw.text((104, 550), index, font=font(13), fill="#92928a")
    return image


def scenario_card(image_path: Path, number: int, total: int, test_name: str) -> Image.Image:
    canvas = Image.new("RGB", SIZE, "#f3f2ed")
    draw = ImageDraw.Draw(canvas)
    story, label = label_for(test_name)
    draw.rounded_rectangle((28, 18, 1252, 80), radius=11, fill="#ffffff", outline="#e4e1d8")
    draw.text((49, 25), story.upper(), font=font(11, True), fill="#526d52")
    draw.text((49, 45), label, font=font(17, True), fill="#24251f")
    marker = f"{number:02d}/{total:02d} · PASÓ"
    marker_width = draw.textbbox((0, 0), marker, font=font(12, True))[2]
    draw.rounded_rectangle((1198 - marker_width, 32, 1220, 62), radius=14, fill="#eaf0e7")
    draw.text((1209 - marker_width, 40), marker, font=font(12, True), fill="#456146")

    with Image.open(image_path) as source:
        source = source.convert("RGB")
        source.thumbnail((1170, 610), Image.Resampling.LANCZOS)
        x = (SIZE[0] - source.width) // 2
        y = 94 + (610 - source.height) // 2
        canvas.paste(source, (x, y))
    draw.text((49, 692), "Captura de pantalla del escenario guardada automáticamente por Selenium", font=font(10), fill="#92928a")
    return canvas


def write_repeated_frame(process: subprocess.Popen, image: Image.Image, seconds: float) -> None:
    raw = image.convert("RGB").tobytes()
    for _ in range(round(FPS * seconds)):
        process.stdin.write(raw)


def main() -> int:
    results = report_results()
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{SIZE[0]}x{SIZE[1]}", "-r", str(FPS), "-i", "-", "-an",
        "-c:v", "mpeg4", "-q:v", "4", "-pix_fmt", "yuv420p", str(OUTPUT),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        write_repeated_frame(
            process,
            title_card(
                "Demostración Selenium",
                f"Aplicación CRUD de biblioteca\n5 historias · {len(results)} escenarios automatizados",
                "Login · alta · búsqueda · edición · eliminación",
            ),
            2.5,
        )
        total = len(results)
        for number, test_name in enumerate(results, start=1):
            screenshot = SCREENSHOTS / f"{test_name}.png"
            if not screenshot.exists():
                raise FileNotFoundError(f"Falta la captura Selenium: {screenshot}")
            write_repeated_frame(process, scenario_card(screenshot, number, total, test_name), 1.5)
        write_repeated_frame(
            process,
            title_card(
                f"{len(results)} de {len(results)} escenarios aprobados",
                "Camino feliz · pruebas negativas · límites\nReporte HTML autocontenido y capturas incluidos",
                "Las historias y criterios de aceptación/rechazo acompañan el código fuente.",
            ),
            3,
        )
        process.stdin.close()
        error_output = process.stderr.read().decode("utf-8", errors="replace")
        exit_code = process.wait(timeout=120)
        if exit_code != 0:
            raise RuntimeError(f"FFmpeg terminó con código {exit_code}: {error_output}")
    except BaseException:
        if process.poll() is None:
            process.kill()
            process.wait()
        raise
    print(f"Video creado: {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
