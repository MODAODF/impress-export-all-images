# Impress Export All Images

A LibreOffice extension that exports every picture embedded in an Impress
presentation to a folder of your choice.

This extension uses [easymacro](https://git.cuates.net/elmau/easymacro)
developed by Mauricio Baeza, released under GPLv3.

## Features

- Adds **Export All Images** to the *Tools* menu (after *Minimize
  Presentation*), to the *Presentation* toolbar, and to the Notebookbar
  (Extension group).
- When triggered, it first checks whether the presentation contains any
  pictures. If none, it shows a message and stops.
- Otherwise it asks for a target folder and exports every picture there,
  preserving the original image bytes and format.
- Files are named `slide<N>_image<M>.<ext>`.
- The UI follows the LibreOffice UI language (en-US and zh-TW bundled).

## Development

```bash
make            # produces impress-export-all-images-X.Y.Z.oxt
make pot        # regenerate the translation template
make mo         # compile .po files to .mo
```

---

# Impress 匯出所有圖片

一個將 Impress 簡報中內嵌的每一張圖片匯出至指定資料夾的 LibreOffice 延伸套件。

此延伸套件使用 Mauricio Baeza 所開發之
[easymacro](https://git.cuates.net/elmau/easymacro)（GPLv3 授權）。

## 功能

- 於「工具」選單（「縮小簡報」之後）、「簡報」工具列、Notebookbar（Extension
  群組）加入「匯出所有圖片」。
- 按下後先檢查簡報中是否有圖片，若沒有則顯示訊息並結束。
- 若有圖片，讓使用者選擇目標資料夾，並將每張圖片匯出至該處，保留原始位元組與格式。
- 檔名格式為 `slide<N>_image<M>.<副檔名>`。
- 介面語系跟隨 LibreOffice UI（內含 en-US 與 zh-TW）。

## 開發

```bash
make            # 產生 impress-export-all-images-X.Y.Z.oxt
make pot        # 重新產生翻譯範本
make mo         # 將 .po 編譯成 .mo
```
