from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

import flet as ft


ACCENT = "#dd0000"
BG = "#111111"


def markdown_like_to_typst(text: str, title: str) -> str:
    """要件定義の簡易マークアップをTypst本文へ変換する。"""
    lines: list[str] = []

    for raw in text.splitlines():
        line = raw.rstrip()

        if not line:
            lines.append("")
            continue

        if line.startswith("# "):
            heading = line[2:].strip().replace('"', '\\"')
            lines.append(f"= {heading}")
            continue

        if line.startswith(">"):
            quote = line[1:].strip().replace('"', '\\"')
            lines.append(f"#quote(block: true)[{quote}]")
            continue

        line = re.sub(r"\{\{(.*?)\}\}", r"*【\\1】*", line)
        lines.append(line)

    body = "\n".join(lines)

    return f'''#set page(paper: "a4", margin: 16pt)
#set text(fill: rgb("#f0f0f0"), size: 10pt)
#set heading(fill: rgb("{ACCENT}"))

#rect(fill: rgb("{BG}"), inset: 0pt, radius: 0pt)[
  #set text(fill: rgb("#f0f0f0"), size: 10pt)
  #set heading(fill: rgb("{ACCENT}"))
  #align(center)[
    #text(weight: "bold", size: 18pt, fill: rgb("{ACCENT}"))[{title.replace('"', '\\"')}]
  ]

  #v(8pt)
  #columns(2, gutter: 14pt)[
{indent_typst_block(body, 4)}
  ]
]
'''


def indent_typst_block(text: str, spaces: int) -> str:
    pad = " " * spaces
    return "\n".join(f"{pad}{line}" if line else "" for line in text.splitlines())


def export_pdf(title: str, body: str, output_pdf: Path) -> None:
    typst_content = markdown_like_to_typst(body, title)

    with tempfile.TemporaryDirectory() as temp_dir:
        typ_file = Path(temp_dir) / "scenario.typ"
        typ_file.write_text(typst_content, encoding="utf-8")

        command = [
            "typst",
            "compile",
            str(typ_file),
            str(output_pdf),
        ]
        subprocess.run(command, check=True)


def main(page: ft.Page) -> None:
    page.title = "Shinobi Writer"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 1280
    page.window.height = 800
    page.padding = 16

    title_input = ft.TextField(label="タイトル", value="シナリオタイトル", border_color=ACCENT)
    output_path_input = ft.TextField(label="出力先PDFパス", border_color=ACCENT)
    body_input = ft.TextField(
        label="本文",
        multiline=True,
        min_lines=30,
        expand=True,
        border_color=ACCENT,
    )

    status_text = ft.Text(color=ACCENT)

    def pick_output(_: ft.ControlEvent) -> None:
        if page.file_picker:
            return

    def on_save_result(e: ft.FilePickerResultEvent) -> None:
        if e.path:
            output_path_input.value = e.path
            page.update()

    picker = ft.FilePicker(on_result=on_save_result)
    page.overlay.append(picker)

    def do_export(_: ft.ControlEvent) -> None:
        if not output_path_input.value:
            status_text.value = "出力先PDFパスを指定してください。"
            page.update()
            return

        try:
            out = Path(output_path_input.value)
            export_pdf(title_input.value or "無題", body_input.value or "", out)
            status_text.value = f"PDF出力が完了しました: {out}"
        except FileNotFoundError:
            status_text.value = "typst コマンドが見つかりません。Typstをインストールしてください。"
        except subprocess.CalledProcessError as err:
            status_text.value = f"PDF出力に失敗しました: {err}"

        page.update()

    left = ft.Container(
        content=body_input,
        expand=3,
        bgcolor=BG,
        border_radius=8,
        padding=8,
    )

    right = ft.Container(
        expand=2,
        bgcolor=BG,
        border_radius=8,
        padding=12,
        content=ft.Column(
            controls=[
                ft.Text("設定", color=ACCENT, size=20, weight=ft.FontWeight.BOLD),
                title_input,
                output_path_input,
                ft.Row(
                    controls=[
                        ft.ElevatedButton(
                            text="保存先を選択",
                            on_click=lambda _: picker.save_file(file_name="scenario.pdf", allowed_extensions=["pdf"]),
                            bgcolor=ACCENT,
                            color="#ffffff",
                        ),
                    ]
                ),
                ft.ElevatedButton(
                    text="PDF出力",
                    on_click=do_export,
                    bgcolor=ACCENT,
                    color="#ffffff",
                ),
                status_text,
            ],
            spacing=12,
        ),
    )

    page.add(ft.Row([left, right], expand=True, spacing=12))


if __name__ == "__main__":
    ft.app(target=main)
