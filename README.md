# sedit (Python + Eel)

Python バックエンドで動くデスクトップ向けシナリオエディタです。

## 技術スタック

- Python 3.x
- Eel
- WeasyPrint
- HTML/CSS/Vanilla JavaScript

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate
pip install eel weasyprint
```

## 起動

```bash
python main.py
```

## 主な機能

- 独自記法のリアルタイムプレビュー
  - `# 見出し`
  - `> 描写`
  - `:::secret 内容 :::`
  - `{{HO1}}`
- ツールバーから定型文挿入
- JSON 形式での保存 / 読込（ネイティブダイアログ）
- WeasyPrint による A4・2段組 PDF 出力
