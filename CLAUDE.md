# CLAUDE.md - AI 助手指引

本文件提供 AI 助手（如 Claude）在本專案中工作時的指引規則。

## 專案概述

這是一個使用 Ollama 本地大型語言模型服務，搭建類似 ChatGPT 的網頁聊天應用程式。

- **前端**: Vue 3 + TypeScript + Vite
- **後端**: Express.js + Node.js
- **AI 服務**: Ollama

## Git Commit 規範

本專案遵循 **AngularJS Git Commit Message Conventions**，所有提交訊息必須使用**繁體中文**。

### Commit 訊息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 類型（必填）

| 類型 | 說明 |
|------|------|
| `feat` | 新增功能 |
| `fix` | 修復錯誤 |
| `docs` | 文件更新 |
| `style` | 程式碼格式調整（不影響程式邏輯） |
| `refactor` | 重構程式碼（不新增功能也不修復錯誤） |
| `perf` | 效能優化 |
| `test` | 新增或修改測試 |
| `chore` | 建置流程或輔助工具變動 |
| `ci` | CI/CD 設定變更 |
| `revert` | 還原先前的 commit |

### Scope 範圍（選填）

| 範圍 | 說明 |
|------|------|
| `frontend` | 前端相關 |
| `backend` | 後端相關 |
| `api` | API 相關 |
| `ui` | 使用者介面 |
| `config` | 設定檔 |
| `deps` | 依賴套件 |

### Subject 主旨（必填）

- 簡短描述變更內容
- 使用繁體中文
- 不超過 50 個字元
- 開頭不需大寫
- 結尾不加句號

### Body 內文（選填）

- 詳細說明變更原因和內容
- 使用繁體中文
- 每行不超過 72 個字元

### Footer 頁尾（選填）

- 關聯的 Issue 編號
- Breaking Changes 說明

### 範例

```
feat(frontend): 新增系統提示詞設定功能

- 新增側邊欄設定面板
- 支援自訂系統提示詞
- 新增預設提示詞範本
- 設定自動儲存至 localStorage
```

```
fix(backend): 修復 Ollama API 連線逾時問題

增加 axios 請求的 timeout 設定，避免長時間等待造成連線中斷。

Closes #123
```

```
docs: 新增專案技術文件

新增 docs 目錄，包含：
- 系統架構說明
- 前後端實作細節
- API 規格文件
- 部署指南
```

## 程式碼規範

### 前端 (Vue.js)

- 使用 Composition API (`<script setup>`)
- 使用 TypeScript
- 元件檔案使用 PascalCase 命名
- CSS 使用 scoped 樣式

### 後端 (Express.js)

- 使用 CommonJS 模組
- API 路由以 `/api` 為前綴
- 錯誤回應使用一致的格式

## 重要檔案位置

- 前端入口: `src/main.ts`
- 主要元件: `src/App.vue`
- 後端入口: `server/app.js`
- 設定檔: `vite.config.ts`, `tsconfig.json`
- 技術文件: `docs/`
