import json
from pathlib import Path

import eel
from weasyprint import CSS, HTML
import tkinter as tk
from tkinter import filedialog

WEB_DIR = Path(__file__).parent / "web"


def _ask_save_path(default_ext: str, filetypes: list[tuple[str, str]]) -> str:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.asksaveasfilename(defaultextension=default_ext, filetypes=filetypes)
    root.destroy()
    return path


def _ask_open_path(filetypes: list[tuple[str, str]]) -> str:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askopenfilename(filetypes=filetypes)
    root.destroy()
    return path


@eel.expose
def save_project(project_payload: dict) -> dict:
    file_path = _ask_save_path(".json", [("JSON file", "*.json")])
    if not file_path:
        return {"ok": False, "message": "保存をキャンセルしました。"}

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(project_payload, f, ensure_ascii=False, indent=2)
        return {"ok": True, "message": f"保存しました: {file_path}"}
    except OSError as exc:
        return {"ok": False, "message": f"保存に失敗しました: {exc}"}


@eel.expose
def load_project() -> dict:
    file_path = _ask_open_path([("JSON file", "*.json")])
    if not file_path:
        return {"ok": False, "message": "読込をキャンセルしました。"}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return {"ok": True, "payload": payload, "message": f"読込しました: {file_path}"}
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "message": f"読込に失敗しました: {exc}"}


@eel.expose
def save_pdf(html_content: str, css_content: str) -> dict:
    file_path = _ask_save_path(".pdf", [("PDF file", "*.pdf")])
    if not file_path:
        return {"ok": False, "message": "PDF出力をキャンセルしました。"}

    try:
        HTML(string=html_content, base_url=str(WEB_DIR)).write_pdf(
            file_path,
            stylesheets=[CSS(string=css_content)],
        )
        return {"ok": True, "message": f"PDFを出力しました: {file_path}"}
    except Exception as exc:  # WeasyPrint runtime errors
        return {"ok": False, "message": f"PDF出力に失敗しました: {exc}"}


if __name__ == "__main__":
    eel.init(str(WEB_DIR))
    eel.start("index.html", size=(1400, 900))
