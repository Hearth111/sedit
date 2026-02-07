@echo off
setlocal

cd /d %~dp0

echo [1/2] Pythonパッケージをインストールします（物理環境）。
py -m pip install --upgrade pip
if errorlevel 1 goto :pip_error

py -m pip install -r requirements.txt
if errorlevel 1 goto :pip_error

echo [2/2] アプリを起動します。
py app.py
if errorlevel 1 goto :run_error

echo 正常終了しました。
exit /b 0

:pip_error
echo パッケージインストールに失敗しました。
exit /b 1

:run_error
echo アプリ実行中にエラーが発生しました。
exit /b 1
