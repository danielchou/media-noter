# Media Noter

這是一個用於管理 MP3 文件筆記的應用程式。

## 功能特點

- 掃描目錄中的 MP3 文件
- 為每個 MP3 文件添加和編輯筆記
- 將筆記保存在文字檔中
- 簡單易用的圖形界面

## 安裝需求

```bash
pip install -r requirements.txt
```

## 使用方法

1. 執行 media_noter.exe
2. 選擇要掃描的目錄
3. 選擇 MP3 文件並添加/編輯筆記
4. 筆記會自動保存

## 技術說明

- 使用 PyQt5 構建圖形界面
- 使用 tinytag 讀取 MP3 文件信息
- 使用 PyInstaller 打包成獨立執行檔
