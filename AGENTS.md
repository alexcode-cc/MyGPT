# AGENTS.md - AI 代理指引

本文件為 AI 代理在本專案中執行任務時的規範指引。

## 專案資訊

- **專案名稱**: 本地 AI 助手 (Ollama ChatBot)
- **技術棧**: Vue 3 + TypeScript + Express.js + Ollama
- **語言偏好**: 繁體中文

---

## Git Commit 規範

### 必須遵循 AngularJS Git Commit Message Conventions

**所有 Commit 訊息必須使用繁體中文**

### 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 類型對照表

| Type | 中文說明 | 使用時機 |
|------|----------|----------|
| `feat` | 新增功能 | 新增一個功能 |
| `fix` | 修復錯誤 | 修復 bug |
| `docs` | 文件更新 | 僅更新文件 |
| `style` | 格式調整 | 不影響程式碼意義的變更（空白、格式化、缺少分號等） |
| `refactor` | 重構 | 既不是新增功能也不是修復錯誤的程式碼變更 |
| `perf` | 效能優化 | 改善效能的程式碼變更 |
| `test` | 測試 | 新增或修正測試 |
| `chore` | 雜務 | 建置過程或輔助工具的變更 |
| `ci` | CI 設定 | CI 設定檔和腳本的變更 |
| `revert` | 還原 | 還原先前的 commit |

### Scope 範圍對照表

| Scope | 說明 |
|-------|------|
| `frontend` | Vue.js 前端 |
| `backend` | Express.js 後端 |
| `api` | API 端點 |
| `ui` | 使用者介面元件 |
| `config` | 設定檔 |
| `deps` | 依賴套件 |
| `docs` | 文件 |

### Commit 訊息撰寫規則

1. **Subject（主旨）**
   - 使用繁體中文
   - 簡潔描述（不超過 50 字元）
   - 使用動詞開頭（新增、修復、更新、移除、重構）
   - 不加句號結尾

2. **Body（內文）**
   - 使用繁體中文
   - 說明「為什麼」和「做了什麼」
   - 每行不超過 72 字元
   - 與 Subject 之間空一行

3. **Footer（頁尾）**
   - 關聯 Issue: `Closes #123` 或 `Fixes #123`
   - Breaking Change: `BREAKING CHANGE: 說明`

### Commit 範例

#### 新增功能
```
feat(frontend): 新增系統提示詞設定功能

- 實作側邊欄設定面板
- 支援自訂系統提示詞輸入
- 提供六種預設提示詞範本
- 自動儲存設定至 localStorage
```

#### 修復錯誤
```
fix(backend): 修復串流回應中斷問題

當 Ollama 回應時間過長時，連線會意外中斷。
增加 keep-alive 設定以維持連線穩定。

Closes #42
```

#### 文件更新
```
docs: 新增完整技術文件

新增 docs 目錄，包含以下文件：
- architecture.md: 系統架構說明
- frontend.md: 前端實作細節
- backend.md: 後端實作細節
- api.md: API 規格文件
- deployment.md: 部署指南
```

#### 重構
```
refactor(frontend): 重構訊息處理邏輯

將訊息處理邏輯抽取為獨立函式，提高程式碼可讀性和可維護性。
```

#### 設定變更
```
chore(config): 更新 Vite 設定

新增開發伺服器 proxy 設定，將 /api 請求轉發至後端。
```

---

## 程式碼修改指引

### 前端修改

- 檔案位置: `src/`
- 主要元件: `src/App.vue`
- 使用 TypeScript
- 遵循 Vue 3 Composition API

### 後端修改

- 檔案位置: `server/`
- 主要檔案: `server/app.js`
- 使用 CommonJS 模組

### 文件修改

- 技術文件: `docs/`
- 專案說明: `README.md`
- 使用繁體中文撰寫

---

## 執行指令

```bash
# 安裝依賴
npm install
cd server && npm install

# 開發模式
npm run dev          # 前端
cd server && npm start  # 後端

# 建置
npm run build
```
