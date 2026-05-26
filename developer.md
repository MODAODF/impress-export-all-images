# 開發者文件

本檔案說明 **Impress 匯出所有圖片** extension 的原始碼結構、easymacro 的使用方式，以及實際呼叫到的 UNO 服務與指令，供未來維護者參考。

> 觀念：這個 extension 本體是一個註冊在 LibreOffice 內的 **UNO 服務**（`com.sun.star.task.Job`）。Addons.xcu 把工具選單項目、簡報工具列按鈕、Notebookbar 條目都指向同一個 service URL `service:org.ossii.ImpressExportAllImages.do`。LibreOffice 拿到該 URL 後會建立 `main.py` 中的 `MainJob`，呼叫它的 `trigger()`，從那裡進入 Python 邏輯。

---

## 檔案／目錄總覽

```
impress-export-all-images/
├── Addons.xcu                  ← UI 註冊：工具選單、簡報工具列、Notebookbar、Images
├── description.xml             ← extension 中介資料（版本、identifier、套件圖示）
├── META-INF/manifest.xml       ← OXT 內檔案的 media-type 註冊
├── Makefile                    ← 打包 .oxt、產生 .pot / 編譯 .mo
├── update_version.sh           ← Makefile 呼叫，自動把 VERSION 寫進 description.xml
├── VERSION                     ← 當前版本字串
├── README.md / developer.md    ← 使用者／開發者說明
├── icons/                      ← 工具列／選單圖示（32x21.png 小、64x42.png 大、export-to-folder.svg）
├── pkg-desc/                   ← 安裝時顯示的多語描述（en / zh-tw）
├── locales/                    ← gettext 多語檔
│   ├── impress-export-all-images.pot         ← 抽出的 msgid 範本
│   ├── en_US/impress-export-all-images.po     ← 英文（msgstr = msgid）
│   └── zh_TW/impress-export-all-images.po     ← 繁中翻譯來源
│       （.mo 由 `make mo` 編到各自的 LC_MESSAGES/，不入版控）
├── main.py                     ← UNO 進入點：XJobExecutor
└── pythonpath/                 ← OXT 安裝後會自動加入 sys.path 的資料夾
    ├── easymacro/              ← 第三方輔助庫（vendored，GPLv3）
    ├── exportimages.py         ← 全部流程邏輯（run / _run / _collect_images / _ext_of / _save_image）
    └── i18n.py                 ← gettext bootstrap，提供 `_()`
```

### 每個關鍵檔案的職責

| 檔案 | 職責 |
|---|---|
| `Addons.xcu` | 在 LibreOffice 中註冊 UI 入口。四個節點：`OfficeMenuBarMerging`（注意 `Bar` 大寫 B）、`OfficeToolbarMerging`（注意 `bar` 小寫 b）、`OfficeNotebookBar`、`Images`。所有 URL 都指向同一個 service URL。全部以 `com.sun.star.presentation.PresentationDocument` 為 Context，只在 Impress 出現。 |
| `META-INF/manifest.xml` | 告訴 OXT 安裝器：`main.py` 是 Python UNO 元件；`Addons.xcu` 是設定資料；`pkg-desc/*` 是地區化描述。 |
| `main.py` | 22 行的小型入口：`MainJob.__init__` 接 ctx、`trigger(args)` 動態 import `exportimages.run()`。`g_ImplementationHelper.addImplementation` 在 Python 元件載入時自動執行，把 `MainJob` 註冊為 `org.ossii.ImpressExportAllImages.do` 服務。 |
| `pythonpath/exportimages.py` | 整個 extension 的核心。`run()` 是 trigger 進入點，把所有錯誤包進 try/except 顯示在 msgbox；`_run()` 跑真正的流程；`_collect_images` / `_ext_of` / `_save_image` 為輔助函式。 |
| `pythonpath/i18n.py` | gettext bootstrap。依 LibreOffice UI 語系（`app.LANGUAGE`，如 `zh-TW`）載入對應的 `.mo`，對外 export `_`。 |
| `pythonpath/easymacro/` | 第三方輔助庫（Mauricio Baeza，GPLv3），提供 `app.active`、`app.paths`、`app.msgbox`、`IOStream` 等 wrapper。 |
| `locales/*.po` / `*.mo` | gettext 翻譯。`.po` 為來源、`.mo` 為 LibreOffice 執行時讀取的編譯檔（由 `make mo` 產生）。 |
| `Makefile` | `make` 編 mo 後把所有檔案打包成 `.oxt`（並排除 `__pycache__`）；`make pot` 從原始碼抽 msgid；`make mo` 編譯 en_US / zh_TW 兩個語系。 |

---

## 啟動流程（按下任何一個入口都會走這一遍）

```
使用者在 Impress 按「匯出所有圖片」（選單 / 工具列 / Notebookbar）
       │  （URL = service:org.ossii.ImpressExportAllImages.do）
       ▼
LibreOffice JobExecutor 找到註冊在 main.py 的 MainJob
       │
       ▼
MainJob.trigger(args)
       │  from exportimages import run
       ▼
exportimages.run()             ← 全域 try/except 邊界
       │
       ▼
exportimages._run()            ← 真正的流程
```

`_run()` 內部的順序：

1. **取得目前文件**：`doc = app.active`。
2. **前置檢查**：沒有開啟文件、或 `doc.type != "impress"` → 顯示 `Please open an Impress presentation first.` 後 return。
   （`app.active` 經 `ModuleManager.identify` 對應到 `LOImpress`，其 `type` 為 `"impress"`。）
3. **蒐集圖片** `_collect_images(doc)`（見下方「圖片蒐集」）。若回空 list → 顯示 `This presentation contains no images.` 後 return。
4. **選擇目標資料夾** `folder = app.paths.get_dir()`。使用者按取消（回空字串）→ 直接 return，不寫任何檔。
5. **逐張匯出**：對每個 `(name, shape)` 呼叫 `_save_image(shape, app.paths.join(folder, name))`，成功則 `count += 1`。
6. **結果 msgbox**：`Exported {n} image(s) to:\n{path}`。

> 流程刻意極簡：沒有對話框、沒有進度條。匯出是直接讀原始位元組寫檔，速度足夠快，不需要非 modal 進度視窗（對照 writer-batch-compress 的 `pixprogress`）。

---

## 使用者動作對應的程式流程

### 圖片蒐集（`_collect_images`）

1. 取 `doc.obj.DrawPages`（presentation 文件的投影片集合）。
2. 外層用索引走訪每張投影片 `pages.getByIndex(s)`；內層走訪該頁每個 shape `page.getByIndex(i)`。
3. 判斷是否為圖片：`shape.supportsService("com.sun.star.drawing.GraphicObjectShape")`。
4. 每頁內維護一個計數 `n`，組出檔名 `slide{s+1}_image{n}.{ext}`。
   - `s`、`n` 皆從 1 起算（對使用者直覺）。
   - 因為含投影片編號，跨投影片不會撞名；同頁內以 `n` 遞增，也不會撞名 → **不需要去重邏輯**。
5. 回傳 `[(filename, shape), ...]`。

> 為什麼用索引而非 easymacro 的 `LODrawPage` 迭代器？這裡直接操作底層 `doc.obj`（UNO model）走訪最單純可靠，且 `_save_image` 需要原生 shape 物件來取 `GraphicStream`。

### 副檔名推導（`_ext_of`）

1. 讀 `shape.Graphic.MimeType`（例如 `image/png`、`image/jpeg`）。
2. 取 `/` 後的子型別，轉小寫。
3. 經 `_EXT_MAP` 正規化：`jpeg→jpg`、`svg+xml→svg`、`x-ms-bmp→bmp`、`tiff→tif`。
4. 對應不到就用子型別原字串；完全取不到 MimeType 時 fallback `png`。

### 單張匯出（`_save_image`）— 保留原始位元組

1. `data = IOStream.to_bin(shape.GraphicStream)`：`GraphicStream` 是該圖片**原始、未經重新編碼**的位元組串流（`com.sun.star.io.XInputStream`）。
2. 空資料回 `False`（計入失敗但不中斷整體）。
3. `app.paths.save_bin(path, data)` 寫檔。
4. 整段以 try/except 包住，單張失敗回 `False`，不影響其他圖片。

> **設計取捨**：刻意用 `GraphicStream` 而非 `com.sun.star.drawing.GraphicExportFilter` 或 `GraphicProvider.storeGraphic`。後兩者都會**重新編碼**（JPEG 會再壓一次、向量會點陣化）。`GraphicStream` 取得的是內嵌在簡報中的原檔位元組，匯出結果與原圖**逐位元相同**（已實測 MD5 一致）。

### i18n 字串解析

1. `pythonpath/i18n.py` 在 module load 時：
   - `PATH_LOCALES = app.paths.join(app.paths.extension(ID_EXTENSION), "locales")` 取得已安裝 OXT 內的 locales 路徑。
   - 由 `app.LANGUAGE`（如 `zh-TW`）算出候選語系 `["zh_TW", "zh"]`。
   - `gettext.translation(APPNAME, PATH_LOCALES, languages=_langs, fallback=True)`。
2. `_ = t.gettext`，`exportimages.py` 以 `from i18n import _` 引入。
3. 字串以 `_("...")` 包住，動態值用 `.format(n=..., path=...)`，故 pygettext 能正確抽出 msgid。

> 與 writer-batch-compress 不同：那邊靠 gettext 預設讀環境變數 `LANG`；這裡**顯式傳入 `languages=`**，直接綁定 LibreOffice 的 UI 語系設定，較不受啟動環境影響。

---

## 呼叫到的 UNO 服務與指令一覽

### Service URL（UI 入口 → 程式）

| 名稱 | 用途 |
|---|---|
| `service:org.ossii.ImpressExportAllImages.do` | Addons.xcu 中選單／工具列／Notebookbar 共用的 dispatch URL，對應 `main.py` 註冊的 Job。 |
| `com.sun.star.task.Job` | `main.py` 把 `MainJob` 註冊成此服務（`XJobExecutor`）。 |

### Addons.xcu 的合併錨點（決定按鈕長在哪）

| 位置 | 設定 |
|---|---|
| 工具選單 | `MergePoint=.uno:ToolsMenu\.uno:PresentationMinimizer`、`MergeCommand=AddAfter`、`MergeFallback=AddPath`。即「縮小簡報」(`.uno:PresentationMinimizer`) 之後。 |
| 簡報工具列 | `MergeToolBar=commontaskbar`（Impress 的「簡報」工具列資源名）、`MergePoint=.uno:MoveSlideLast`、`MergeCommand=AddAfter`、`MergeFallback=AddLast`。即工具列最後。 |
| Notebookbar | `OfficeNotebookBar` 節點，自動歸入「Extension」群組。 |
| 圖示 | `Images` 節點：`ImageSmallURL=%origin%/icons/32x21.png`、`ImageBigURL=%origin%/icons/64x42.png`。 |

> 這些 `.uno:` 指令名稱與工具列資源名可在 `<LibreOffice>/share/config/soffice.cfg/modules/simpress/`（`menubar/menubar.xml`、`toolbar/commontaskbar.xml`）查證。

### 文件與圖片操作（執行期透過 easymacro / 原生 model）

| API | 在哪裡用 | 用途 |
|---|---|---|
| `app.active` → `doc.obj` | `_run` / `_collect_images` | 取得目前 presentation 文件 model。 |
| `doc.obj.DrawPages` + `getByIndex` + `.Count` | `_collect_images` | 走訪每張投影片與其 shapes。 |
| `shape.supportsService("com.sun.star.drawing.GraphicObjectShape")` | `_collect_images` | 判斷 shape 是否為圖片。 |
| `shape.Graphic.MimeType` | `_ext_of` | 推導副檔名。 |
| `shape.GraphicStream` | `_save_image` | 取得圖片**原始位元組**串流（`XInputStream`）。 |
| `com.sun.star.frame.ModuleManager` (`identify`) | （由 easymacro `app.active` 內部呼叫） | 判定文件型別 → 對應 `LOImpress`。 |

---

## easymacro 怎麼用

easymacro 以 `import easymacro as app` 引入，常用入口（皆為 lazy 屬性，定義在 `easymacro/__init__.py` 的 `__getattr__`）：

| 呼叫 | 說明 |
|---|---|
| `app.active` | 回傳目前作用中文件的包裝物件（Impress 為 `LOImpress`）。`.type` 給 `"impress"`，`.obj` 給底層 UNO model。 |
| `app.msgbox(message, title)` | 顯示資訊訊息框。本專案的 title 統一用 `_("Impress Export All Images")`。 |
| `app.paths.get_dir(init_dir="")` | 叫出 **FolderPicker**（`com.sun.star.ui.dialogs.FolderPicker`），回傳所選資料夾的系統路徑字串；取消回空字串。 |
| `app.paths.join(*parts)` | 跨平台路徑串接。 |
| `app.paths.save_bin(path, data)` | 把 `bytes` 寫到檔案（內部用 `pathlib.Path.write_bytes`）。 |
| `app.paths.extension(id)` | 回傳已安裝 extension 的根目錄路徑（i18n.py 用來定位 `locales/`）。 |
| `app.LANGUAGE` | LibreOffice UI 語系字串（如 `zh-TW`）。i18n.py 用它選語系。 |
| `IOStream.to_bin(stream)` | **不在** `app` 命名空間，需 `from easymacro.easyuno import IOStream`。把 `XInputStream` 讀成 `bytes`。 |

> 注意：easymacro 在 module load 時抓的是 `uno.getComponentContext()`（本地元件 context）。在 LibreOffice 內以 Job 形式執行時這就是正確的 office context；但若想以**外部 socket 連線**的方式跑測試，easymacro 的 `app.active` 不會看到遠端文件——這時要直接用原生 UNO（見下方測試說明）。

---

## PyUNO／整合上的注意事項（給後續維護者）

1. **`OfficeMenuBarMerging` vs `OfficeToolbarMerging` 大小寫**：前者 `Bar` 大寫、後者 `bar` 小寫，schema 規定，打錯整段被忽略且不報錯。
2. **MergePoint 路徑分隔用反斜線 `\`**：選單合併點是「父選單\項目」，例如 `.uno:ToolsMenu\.uno:PresentationMinimizer`。
3. **Context 必須是 `com.sun.star.presentation.PresentationDocument`**：用 `com.sun.star.drawing.DrawingDocument` 會連 Draw 也跑出來；用錯則按鈕不出現。
4. **`GraphicStream` 才能拿到原始位元組**：`GraphicExportFilter` / `GraphicProvider.storeGraphic` 會重新編碼，破壞「保留原檔」的需求。
5. **打包要排除 `__pycache__`**：`make` 已加 `-x '*__pycache__*' '*.pyc'`，避免把編譯快取塞進 .oxt。
6. **`.mo` 不入版控**：由 `make mo` 產生並 `mkdir -p LC_MESSAGES`；只追蹤 `.po` / `.pot`。

---

## 加新功能的常見路徑

| 需求 | 動哪些檔 |
|---|---|
| 改變匯出檔名規則 | `exportimages._collect_images`（組 filename 的那行） |
| 支援更多圖片格式副檔名 | `exportimages._EXT_MAP` 加對應 |
| 改變「無圖片 / 完成」訊息 | `exportimages.py` 的 `_(...)` 字串 → `make pot` → 各語系 `.po` 補 `msgstr` → `make mo` |
| 加新語系 | 在 `Makefile` 的 `LANGS` 加語系碼 → 建 `locales/<lang>/impress-export-all-images.po` → `make mo` |
| 改 toolbar / menu / notebookbar 位置 | `Addons.xcu`（注意上方大小寫與 MergePoint 規則） |
| 改套件圖示 / 安裝描述 | `description.xml` 的 `<icon>`、`pkg-desc/*` |

---

## 建置與測試

```bash
make            # 產生 impress-export-all-images-X.Y.Z.oxt（含 make mo）
make pot        # 從 exportimages.py / i18n.py 抽 msgid 到 locales/*.pot
make mo         # 編譯 en_US / zh_TW 的 .po 成 .mo
make clean      # 移除 .oxt 與所有 .mo
```

安裝測試（用獨立 user profile，不污染日常設定）：

```bash
PROFILE=/tmp/lo_iea
/opt/libreoffice25.2/program/unopkg add -f \
    "-env:UserInstallation=file://$PROFILE" \
    impress-export-all-images-*.oxt
```

UNO 原語的 headless 驗證：因 easymacro 綁本地 context，測試核心邏輯時建議**直接用原生 UNO** 連到 headless soffice：建立 simpress 文件 → 用 `GraphicProvider.queryGraphic` 從檔案塞一張圖到 `GraphicObjectShape` → 驗證 `supportsService` / `Graphic.MimeType` / `GraphicStream` 能取到位元組，並可 `cmp`／`md5sum` 確認與原檔逐位元相同。
