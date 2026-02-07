import json
import os
import re

import flet as ft
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

RUBY_PATTERN = re.compile(r"\{(.+?)\}\((.+?)\)")


def normalize_ruby(text: str) -> str:
    return RUBY_PATTERN.sub(r"\1(\2)", text)


def parse_blocks(text: str):
    blocks = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            blocks.append(("blank", ""))
        elif stripped.startswith("# "):
            blocks.append(("heading", stripped[2:].strip()))
        elif stripped.startswith(">"):
            blocks.append(("quote", stripped[1:].strip()))
        elif stripped.startswith("{{") and stripped.endswith("}}"):
            blocks.append(("ho", stripped[2:-2].strip()))
        elif stripped.startswith(":::secret") and stripped.endswith(":::"):
            body = stripped[len(":::secret") : -3].strip()
            blocks.append(("secret", body or "(secret)"))
        else:
            blocks.append(("paragraph", stripped))
    return blocks


def main(page: ft.Page):
    page.title = "Shinobi-Writer (v0.3)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10
    page.window_width = 1600
    page.window_height = 920
    page.bgcolor = "#f6f6f6"

    pdf_font_name = "Helvetica"

    font_candidates = [
        "C:\\Windows\\Fonts\\meiryo.ttc",
        "C:\\Windows\\Fonts\\msgothic.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]

    for candidate in font_candidates:
        if os.path.exists(candidate):
            try:
                pdfmetrics.registerFont(TTFont("Japanese", candidate))
                pdf_font_name = "Japanese"
                break
            except Exception:
                continue

    if pdf_font_name != "Japanese":
        try:
            pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
            pdf_font_name = "HeiseiKakuGo-W5"
        except Exception:
            pass

    current_img_path = ""
    current_project_path = ""

    def toast(message: str, color: str = "#2e7d32"):
        page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def get_editor_text() -> str:
        return editor_field.value or ""

    def get_styles():
        base = getSampleStyleSheet()["BodyText"]
        base.fontName = pdf_font_name
        base.fontSize = 10
        base.leading = 14

        heading = ParagraphStyle(
            "HeadingStyle",
            parent=base,
            fontSize=13,
            leading=18,
            textColor=colors.HexColor("#111111"),
            backColor=colors.HexColor("#f4f4f4"),
            borderPadding=(6, 8, 6),
            leftIndent=0,
            borderWidth=0,
        )
        quote = ParagraphStyle(
            "QuoteStyle",
            parent=base,
            backColor=colors.HexColor("#eeeeee"),
            textColor=colors.HexColor("#222222"),
            borderPadding=(6, 8, 6),
            leftIndent=6,
            rightIndent=6,
        )
        normal = ParagraphStyle("NormalStyle", parent=base)
        return heading, quote, normal

    def build_story(text: str):
        heading_style, quote_style, normal_style = get_styles()
        story = [NextPageTemplate("Later")]
        for block_type, body in parse_blocks(text):
            body = normalize_ruby(body)
            if block_type == "blank":
                story.append(Spacer(1, 4 * mm))
            elif block_type == "heading":
                heading_tbl = Table(
                    [[Paragraph(f"<b>{body}</b>", heading_style)]],
                    colWidths=[170 * mm],
                )
                heading_tbl.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f4f4")),
                            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#111111")),
                            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dadada")),
                            ("LEFTPADDING", (0, 0), (-1, -1), 6),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                            ("TOPPADDING", (0, 0), (-1, -1), 6),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ]
                    )
                )
                story.extend([heading_tbl, Spacer(1, 3 * mm)])
            elif block_type == "quote":
                story.extend([Paragraph(body, quote_style), Spacer(1, 2 * mm)])
            elif block_type == "ho":
                ho_tbl = Table([[Paragraph(f"HO: <b>{body}</b>", normal_style)]], colWidths=[170 * mm])
                ho_tbl.setStyle(
                    TableStyle(
                        [
                            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#555555")),
                            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7f7f7")),
                            ("LEFTPADDING", (0, 0), (-1, -1), 8),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                            ("TOPPADDING", (0, 0), (-1, -1), 6),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ]
                    )
                )
                story.extend([ho_tbl, Spacer(1, 2 * mm)])
            elif block_type == "secret":
                secret_tbl = Table([[Paragraph(f"SECRET: {body}", normal_style)]], colWidths=[170 * mm])
                secret_tbl.setStyle(
                    TableStyle(
                        [
                            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#333333")),
                            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eeeeee")),
                            ("LEFTPADDING", (0, 0), (-1, -1), 8),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                            ("TOPPADDING", (0, 0), (-1, -1), 6),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ]
                    )
                )
                story.extend([secret_tbl, Spacer(1, 2 * mm)])
            else:
                story.extend([Paragraph(body, normal_style), Spacer(1, 2 * mm)])
        return story

    def save_project(path: str):
        nonlocal current_project_path
        data = {
            "title": title_field.value or "",
            "text_content": get_editor_text(),
            "header_image_path": current_img_path,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        current_project_path = path
        project_path_label.value = os.path.basename(path)
        project_path_label.update()

    def load_project(path: str):
        nonlocal current_img_path, current_project_path
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        title_field.value = data.get("title", "")
        editor_field.value = data.get("text_content", "")
        current_img_path = data.get("header_image_path", "")

        if current_img_path and os.path.exists(current_img_path):
            img_preview.src = current_img_path
            img_preview.visible = True
            img_info.value = os.path.basename(current_img_path)
        else:
            current_img_path = ""
            img_preview.src = ""
            img_preview.visible = False
            img_info.value = "画像未選択"

        current_project_path = path
        project_path_label.value = os.path.basename(path)
        title_field.update()
        editor_field.update()
        img_preview.update()
        img_info.update()
        project_path_label.update()
        update_toc(None)
        update_preview()

    def handle_project_save(e: ft.FilePickerResultEvent):
        if e.path:
            try:
                save_project(e.path)
                toast(f"プロジェクト保存: {e.path}")
            except Exception as err:
                toast(f"保存失敗: {err}", "#b71c1c")

    def handle_project_load(e: ft.FilePickerResultEvent):
        if e.files:
            try:
                load_project(e.files[0].path)
                toast(f"プロジェクト読込: {e.files[0].path}")
            except Exception as err:
                toast(f"読込失敗: {err}", "#b71c1c")

    def on_img_picked(e: ft.FilePickerResultEvent):
        nonlocal current_img_path
        if e.files:
            file_path = e.files[0].path
            current_img_path = file_path
            img_preview.src = file_path
            img_preview.visible = True
            img_info.value = os.path.basename(file_path)
            img_info.update()
            img_preview.update()
            update_preview()

    def save_pdf_file(path: str):
        doc = BaseDocTemplate(
            path,
            pagesize=A4,
            leftMargin=12 * mm,
            rightMargin=12 * mm,
            topMargin=12 * mm,
            bottomMargin=12 * mm,
        )
        width, height = A4

        first_frame = Frame(
            12 * mm,
            15 * mm,
            width - 24 * mm,
            height - 120 * mm,
            id="first_frame",
        )
        gap = 6 * mm
        col_w = (width - 24 * mm - gap) / 2
        later_frame_l = Frame(12 * mm, 15 * mm, col_w, height - 27 * mm, id="col_left")
        later_frame_r = Frame(12 * mm + col_w + gap, 15 * mm, col_w, height - 27 * mm, id="col_right")

        def draw_first_page(c, _):
            c.saveState()
            c.setFillColor(colors.white)
            c.rect(0, 0, width, height, fill=1, stroke=0)
            y = height - 15 * mm
            if current_img_path and os.path.exists(current_img_path):
                try:
                    img_w = width - 24 * mm
                    img_h = 70 * mm
                    c.drawImage(current_img_path, 12 * mm, y - img_h, width=img_w, height=img_h, preserveAspectRatio=True, anchor='n')
                    y -= img_h + 8 * mm
                except Exception:
                    pass
            c.setFillColor(colors.HexColor("#111111"))
            c.setFont(pdf_font_name, 22)
            c.drawString(15 * mm, y, title_field.value or "No Title")
            c.restoreState()

        def draw_later_page(c, _):
            c.saveState()
            c.setFillColor(colors.white)
            c.rect(0, 0, width, height, fill=1, stroke=0)
            c.restoreState()

        doc.addPageTemplates(
            [
                PageTemplate(id="First", frames=[first_frame], onPage=draw_first_page),
                PageTemplate(id="Later", frames=[later_frame_l, later_frame_r], onPage=draw_later_page),
            ]
        )

        story = build_story(get_editor_text())
        doc.build(story)

    def save_pdf(e: ft.FilePickerResultEvent):
        if e.path:
            try:
                save_pdf_file(e.path)
                toast(f"PDF保存: {e.path}")
            except Exception as err:
                toast(f"PDF保存失敗: {err}", "#b71c1c")

    def scroll_to_line(line_index):
        toast(f"行ジャンプ: {line_index + 1}行目", "#424242")

    def update_toc(_):
        toc_view.controls.clear()
        lines = get_editor_text().split("\n")
        for i, line in enumerate(lines):
            text = line.strip()
            if text.startswith("# "):
                toc_view.controls.append(
                    ft.Container(
                        content=ft.Text(f"■ {text[2:]}", size=12, weight="bold", color="#dd0000"),
                        padding=ft.padding.only(top=8, bottom=4),
                        on_click=lambda _, pos=i: scroll_to_line(pos),
                    )
                )
            elif text.startswith("## "):
                toc_view.controls.append(
                    ft.Container(
                        content=ft.Text(f"  - {text[3:]}", size=11, color="#aaaaaa"),
                        padding=ft.padding.only(left=10, bottom=2),
                        on_click=lambda _, pos=i: scroll_to_line(pos),
                    )
                )
        toc_view.update()

    def apply_insert(snippet: str, line_start: bool = False):
        value = get_editor_text()
        selection = getattr(editor_field, "selection", None)
        start = len(value)
        end = len(value)
        if selection is not None:
            start = getattr(selection, "start", start)
            end = getattr(selection, "end", end)
        start = max(0, min(start, len(value)))
        end = max(0, min(end, len(value)))

        if line_start:
            line_head = value.rfind("\n", 0, start) + 1
            editor_field.value = value[:line_head] + snippet + value[line_head:]
        else:
            editor_field.value = value[:start] + snippet + value[end:]
        editor_field.update()
        update_toc(None)
        update_preview()

    def update_preview():
        preview_column.controls.clear()
        preview_column.controls.append(ft.Text(title_field.value or "(タイトル未設定)", size=22, weight="bold", color="#111"))
        if current_img_path and os.path.exists(current_img_path):
            preview_column.controls.append(
                ft.Image(src=current_img_path, height=140, fit=ft.ImageFit.COVER)
            )
        preview_column.controls.append(ft.Divider(color="#ddd"))

        for block_type, body in parse_blocks(get_editor_text()):
            body = normalize_ruby(body)
            if block_type == "blank":
                preview_column.controls.append(ft.Container(height=8))
            elif block_type == "heading":
                preview_column.controls.append(
                    ft.Container(
                        content=ft.Text(body, color="#111", weight="bold"),
                        bgcolor="#f8f8f8",
                        border=ft.border.only(left=ft.BorderSide(3, "#666")),
                        padding=8,
                    )
                )
            elif block_type == "quote":
                preview_column.controls.append(
                    ft.Container(content=ft.Text(body, color="#222"), bgcolor="#dddddd", padding=8, border_radius=4)
                )
            elif block_type == "ho":
                preview_column.controls.append(
                    ft.Container(
                        content=ft.Text(f"HO: {body}", color="#333"),
                        border=ft.border.all(1, "#888"),
                        bgcolor="#f6f6f6",
                        padding=8,
                    )
                )
            elif block_type == "secret":
                preview_column.controls.append(
                    ft.Container(
                        content=ft.Text(f"SECRET: {body}", color="#111"),
                        bgcolor="#cccccc",
                        border=ft.border.all(1, "#666"),
                        padding=8,
                    )
                )
            else:
                preview_column.controls.append(ft.Text(body, color="#333"))
        preview_column.update()

    def on_editor_change(_):
        update_toc(None)
        update_preview()

    def save_project_shortcut():
        if current_project_path:
            try:
                save_project(current_project_path)
                toast(f"上書き保存: {current_project_path}")
            except Exception as err:
                toast(f"保存失敗: {err}", "#b71c1c")
        else:
            project_save_picker.save_file(file_name=f"{title_field.value or 'project'}.json")

    def on_keyboard(e: ft.KeyboardEvent):
        if getattr(e, "ctrl", False) and str(getattr(e, "key", "")).lower() == "s":
            save_project_shortcut()

    page.on_keyboard_event = on_keyboard

    img_picker = ft.FilePicker(on_result=on_img_picked)
    pdf_save_dialog = ft.FilePicker(on_result=save_pdf)
    project_save_picker = ft.FilePicker(on_result=handle_project_save)
    project_load_picker = ft.FilePicker(on_result=handle_project_load)
    page.overlay.extend([img_picker, pdf_save_dialog, project_save_picker, project_load_picker])

    toc_view = ft.Column(scroll=ft.ScrollMode.AUTO, height=220)

    title_field = ft.TextField(
        label="タイトル",
        bgcolor="#ffffff",
        border_color="#d8d8d8",
        text_size=12,
        on_change=lambda _: update_preview(),
    )
    editor_field = ft.TextField(
        multiline=True,
        min_lines=40,
        text_size=14,
        bgcolor="#ffffff",
        color="#222",
        border_color="#e3e3e3",
        cursor_color="#555",
        hint_text="# タイトル\n\n> ここに描写を書く...",
        on_change=on_editor_change,
        expand=True,
    )

    img_preview = ft.Image(src="", width=200, height=120, fit=ft.ImageFit.CONTAIN, visible=False)
    img_info = ft.Text("画像未選択", size=10, color="#666")
    project_path_label = ft.Text("未保存", size=10, color="#888")

    snippet_buttons = ft.Column(
        [
            ft.Text("スニペット", size=12, weight="bold", color="#aaa"),
            ft.ElevatedButton("シーン表", on_click=lambda _: apply_insert("{{SceneTable}}")),
            ft.ElevatedButton("HO枠", on_click=lambda _: apply_insert("{{HO1}}")),
            ft.ElevatedButton("描写ボックス", on_click=lambda _: apply_insert("> ", line_start=True)),
            ft.ElevatedButton("袋とじ", on_click=lambda _: apply_insert(":::secret 内容 :::")),
            ft.ElevatedButton("ルビ", on_click=lambda _: apply_insert("{漢字}(よみ)")),
        ],
        spacing=6,
    )

    left_col = ft.Container(
        content=ft.Column(
            [
                ft.Text("TOOLS", size=12, weight="bold", color="#888"),
                ft.Divider(color="#ddd"),
                title_field,
                ft.Row(
                    [
                        ft.ElevatedButton("JSON保存", on_click=lambda _: project_save_picker.save_file(file_name=f"{title_field.value or 'project'}.json")),
                        ft.ElevatedButton("JSON読込", on_click=lambda _: project_load_picker.pick_files(allow_multiple=False, allowed_extensions=["json"])),
                    ]
                ),
                ft.Text("現在のプロジェクト", size=10, color="#777"),
                project_path_label,
                ft.Divider(color="#ddd"),
                ft.Text("ヘッダー画像", size=11, color="#aaa"),
                ft.Container(content=img_preview, bgcolor="#fff", alignment=ft.alignment.center, border=ft.border.all(1, "#ddd"), height=120),
                ft.Row(
                    [
                        img_info,
                        ft.IconButton(icon=ft.icons.IMAGE, on_click=lambda _: img_picker.pick_files(allow_multiple=False, allowed_extensions=["png", "jpg", "jpeg"])),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.ElevatedButton("PDF保存", icon=ft.icons.SAVE_ALT, on_click=lambda _: pdf_save_dialog.save_file(file_name=f"{title_field.value or 'output'}.pdf")),
                ft.Divider(color="#ddd"),
                snippet_buttons,
                ft.Divider(color="#ddd"),
                ft.Text("INDEX", size=12, weight="bold", color="#888"),
                toc_view,
            ],
            scroll=ft.ScrollMode.AUTO,
        ),
        bgcolor="#fafafa",
        padding=10,
        border=ft.border.only(right=ft.BorderSide(1, "#e1e1e1")),
    )

    preview_column = ft.Column(scroll=ft.ScrollMode.AUTO)
    right_col = ft.Container(
        content=ft.Column([ft.Text("PREVIEW", size=12, weight="bold", color="#888"), ft.Divider(color="#ddd"), preview_column]),
        bgcolor="#fafafa",
        padding=10,
        border=ft.border.only(left=ft.BorderSide(1, "#e1e1e1")),
    )

    page.add(
        ft.Row(
            [
                ft.Container(content=left_col, expand=3),
                ft.Container(content=editor_field, expand=7, padding=20),
                ft.Container(content=right_col, expand=4),
            ],
            expand=True,
            spacing=0,
        )
    )

    update_toc(None)
    update_preview()


ft.app(target=main)
