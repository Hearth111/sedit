import flet as ft
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
import os

def main(page: ft.Page):
    # ■ 1. アプリ設定
    page.title = "Shinobi-Writer (v0.2)"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    page.window_width = 1400
    page.window_height = 900
    page.bgcolor = "#111111"

    # フォント登録（前回と同じ）
    try:
        pdfmetrics.registerFont(TTFont('Japanese', 'C:\\Windows\\Fonts\\meiryo.ttc'))
    except:
        pass

    # アプリの状態変数
    current_img_path = ""

    # ■ 2. 機能の実装

    # 目次更新機能
    def update_toc(e):
        # 目次リストをクリア
        toc_view.controls.clear()
        
        # 本文を行ごとに解析
        lines = editor_field.value.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('# '):
                # 見出し (# )
                toc_view.controls.append(
                    ft.Container(
                        content=ft.Text(f"■ {line.replace('# ', '')}", size=12, weight="bold", color="#dd0000"),
                        padding=ft.padding.only(top=10, bottom=5),
                        on_click=lambda _, pos=i: scroll_to_line(pos) # ジャンプ機能(簡易)
                    )
                )
            elif line.startswith('## '):
                # 小見出し (## )
                toc_view.controls.append(
                    ft.Container(
                        content=ft.Text(f"  - {line.replace('## ', '')}", size=11, color="#aaaaaa"),
                        padding=ft.padding.only(left=10, bottom=2),
                        on_click=lambda _, pos=i: scroll_to_line(pos)
                    )
                )
        toc_view.update()

    # エディタのスクロール機能（現在はFletの制限で完全な行ジャンプは難しいが、枠組みだけ用意）
    def scroll_to_line(line_index):
        # 将来的にここにスクロール処理を実装
        print(f"Jump to line: {line_index}")
        page.snack_bar = ft.SnackBar(ft.Text(f"行ジャンプ: {line_index}行目 (機能開発中)"), bgcolor="#333")
        page.snack_bar.open = True
        page.update()

    # 画像選択機能
    def on_img_picked(e: ft.FilePickerResultEvent):
        nonlocal current_img_path
        if e.files:
            file_path = e.files[0].path
            current_img_path = file_path
            # プレビュー更新
            img_preview.src = file_path
            img_preview.visible = True
            img_info.value = os.path.basename(file_path)
            img_info.update()
            img_preview.update()

    # 画像選択ダイアログ
    img_picker = ft.FilePicker(on_result=on_img_picked)
    page.overlay.append(img_picker)

    # PDF保存機能
    def save_pdf(e: ft.FilePickerResultEvent):
        save_path = e.path
        if save_path:
            try:
                c = canvas.Canvas(save_path, pagesize=A4)
                width, height = A4
                
                # 日本語フォント設定
                try: c.setFont("Japanese", 10)
                except: pass

                # --- 1ページ目の描画 ---
                cursor_y = height - 20*mm
                
                # 画像描画 (選択されていたら)
                if current_img_path:
                    try:
                        # 画像を上部に描画 (幅いっぱい、高さアスペクト維持は省略して固定)
                        c.drawImage(current_img_path, 20*mm, height - 100*mm, width=170*mm, height=80*mm, preserveAspectRatio=True)
                        cursor_y -= 90*mm
                    except:
                        pass

                # タイトル描画
                c.setFont("Japanese", 24)
                c.drawString(20*mm, cursor_y, title_field.value)
                cursor_y -= 15*mm

                # --- 本文描画 (簡易) ---
                c.setFont("Japanese", 10)
                text = editor_field.value
                for line in text.split('\n'):
                    if cursor_y < 20*mm:
                        c.showPage()
                        cursor_y = height - 20*mm
                        try: c.setFont("Japanese", 10)
                        except: pass
                    
                    c.drawString(20*mm, cursor_y, line)
                    cursor_y -= 6*mm

                c.save()
                page.snack_bar = ft.SnackBar(ft.Text(f"保存しました: {save_path}"), bgcolor="green")
                page.snack_bar.open = True
                page.update()
            except Exception as err:
                page.snack_bar = ft.SnackBar(ft.Text(f"エラー: {err}"), bgcolor="red")
                page.snack_bar.open = True
                page.update()

    save_dialog = ft.FilePicker(on_result=save_pdf)
    page.overlay.append(save_dialog)

    # ■ 3. UIコンポーネント作成

    # [左カラム] 目次・ツール
    toc_view = ft.Column(scroll=ft.ScrollMode.AUTO)
    left_col = ft.Container(
        content=ft.Column([
            ft.Text("INDEX", size=12, weight="bold", color="#555"),
            ft.Divider(color="#333"),
            toc_view
        ]),
        bgcolor="#161616",
        padding=10,
        border=ft.border.only(right=ft.BorderSide(1, "#333"))
    )

    # [中カラム] エディタ
    editor_field = ft.TextField(
        multiline=True,
        min_lines=40,
        text_size=14,
        bgcolor="#111",
        color="#ddd",
        border_color="transparent", # 枠線を消して没入感アップ
        cursor_color="#d00",
        hint_text="# タイトル\n\n> ここに描写を書く...",
        on_change=update_toc, # 文字入力のたびに目次更新
        expand=True
    )

    # [右カラム] 設定・情報
    title_field = ft.TextField(label="タイトル", bgcolor="#222", border_color="#444", text_size=12)
    
    img_preview = ft.Image(src="", width=200, height=120, fit=ft.ImageFit.CONTAIN, visible=False)
    img_info = ft.Text("画像未選択", size=10, color="#666")
    
    img_btn = ft.ElevatedButton(
        "画像を選択", 
        icon=ft.icons.IMAGE,
        style=ft.ButtonStyle(bgcolor="#333", color="white"),
        on_click=lambda _: img_picker.pick_files(allow_multiple=False, allowed_extensions=["png", "jpg", "jpeg"])
    )

    save_btn = ft.ElevatedButton(
        "PDF保存", 
        icon=ft.icons.SAVE_ALT,
        style=ft.ButtonStyle(bgcolor="#d00", color="white", shape=ft.RoundedRectangleBorder(radius=4)),
        on_click=lambda _: save_dialog.save_file(file_name=f"{title_field.value}.pdf")
    )

    right_col = ft.Container(
        content=ft.Column([
            ft.Text("SETTINGS", size=12, weight="bold", color="#555"),
            ft.Divider(color="#333"),
            title_field,
            ft.Container(height=10),
            ft.Text("トレーラー画像", size=11, color="#aaa"),
            ft.Container(
                content=img_preview,
                bgcolor="#000",
                alignment=ft.alignment.center,
                border=ft.border.all(1, "#333"),
                height=120
            ),
            ft.Row([img_info, img_btn], alignment="spaceBetween"),
            ft.Divider(color="#333"),
            ft.Container(content=save_btn, padding=ft.padding.only(top=20))
        ]),
        bgcolor="#161616",
        padding=10,
        border=ft.border.only(left=ft.BorderSide(1, "#333"))
    )

    # ■ 4. レイアウト配置 (3カラム)
    page.add(
        ft.Row(
            [
                ft.Container(content=left_col, expand=2),  # 左 (20%)
                ft.Container(content=editor_field, expand=6, padding=20), # 中 (60%)
                ft.Container(content=right_col, expand=2)  # 右 (20%)
            ],
            expand=True,
            spacing=0 # 隙間なく配置
        )
    )

    # 初期更新
    update_toc(None)

ft.app(target=main)
