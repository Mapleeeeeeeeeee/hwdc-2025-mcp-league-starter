# Google Cloud Run 部署指南

> 完整的環境變數設定和部署流程說明

## 📋 環境變數總覽

### ✅ 必填變數（部署時必須提供）

| 變數名稱 | 說明 | 範例值 | 取得方式 |
|---------|------|--------|---------|
| `_OPENAI_API_KEY` | OpenAI API 金鑰 | `sk-proj-xxx...` | [OpenAI Platform](https://platform.openai.com/api-keys) |
| `_CORS_ALLOWED_ORIGINS` | CORS 允許的來源 | `https://your-app.run.app` | 部署後取得 Cloud Run URL |
| `_MCP_SERVER_AUTH_TOKEN` | MCP Server 認證 Token | `a1b2c3d4e5f6...` | 執行 `openssl rand -hex 32` 生成 |

⚠️ **重要**：
- 生產環境 `CORS_ALLOWED_ORIGINS` **必須明確設定**，否則會阻擋所有跨域請求
- `_OPENAI_API_KEY` 是必填項，沒有此值應用無法正常運作
- `_MCP_SERVER_AUTH_TOKEN` 是 MCP Server 認證所需，建議使用強隨機字串（64 字元）

---

### 🔧 已在 cloudbuild.yaml 中設定的變數

以下變數已在 `cloudbuild.yaml` 中預設配置，**不需要手動設定**：

| 變數名稱 | 預設值 | 說明 |
|---------|--------|------|
| `ENVIRONMENT` | `production` | 運行環境 |
| `HOST` | `0.0.0.0` | 服務監聽地址 |
| `PORT` | `8000` | 後端服務端口 |
| `LOG_LEVEL` | `INFO` | 日誌級別 |
| `ENABLE_MCP_SYSTEM` | `true` | 啟用 MCP 系統 |
| `AS_A_MCP_SERVER` | `false` | 是否作為 MCP Server 運行 |

**Container 配置**（cloudbuild.yaml 設定）：
- Memory: `2Gi`
- CPU: `2`
- Timeout: `300s`
- Max instances: `10`
- Min instances: `0`
- Port: `8080` (Nginx)
- Region: `asia-east1`

---

### 🎛️ 進階選填變數（若需調整預設值）

如需修改預設值，可在 `cloudbuild.yaml` 的 `--set-env-vars` 中調整：

| 變數名稱 | 預設值 | 可選值 | 說明 |
|---------|--------|--------|------|
| `ENVIRONMENT` | `production` | `development`, `staging`, `test` | 運行環境 |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `WARNING`, `ERROR`, `CRITICAL` | 日誌級別 |
| `ENABLE_MCP_SYSTEM` | `true` | `true`, `false` | 是否啟用 MCP |

---

## 🚀 部署步驟

### 前置準備

1. **安裝 Google Cloud SDK**
   ```bash
   # macOS
   brew install google-cloud-sdk

   # 或下載安裝
   # https://cloud.google.com/sdk/docs/install
   ```

2. **初始化 gcloud 並登入**
   ```bash
   gcloud init
   gcloud auth login
   ```

3. **設定專案 ID**
   ```bash
   export PROJECT_ID=你的專案ID
   gcloud config set project $PROJECT_ID
   ```

4. **啟用必要的 API**
   ```bash
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   ```

---

### 方式 1：使用 Cloud Build 部署（推薦）

#### 步驟 1: 準備環境變數

```bash
# 設定你的 OpenAI API Key
export OPENAI_API_KEY="sk-proj-你的實際key"

# 生成 MCP Server 認證 Token（建議使用強隨機字串）
export MCP_AUTH_TOKEN=$(openssl rand -hex 32)
echo "生成的 MCP Token: $MCP_AUTH_TOKEN"  # 請妥善保存此 token

# 預留 CORS origins（先部署後再更新）
export CORS_ORIGINS=""
```

#### 步驟 2: 執行部署

```bash
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_OPENAI_API_KEY="$OPENAI_API_KEY",_CORS_ALLOWED_ORIGINS="$CORS_ORIGINS",_MCP_SERVER_AUTH_TOKEN="$MCP_AUTH_TOKEN"
```

#### 步驟 3: 取得 Cloud Run URL

```bash
gcloud run services describe hwdc-2025-mcp-league \
  --region=asia-east1 \
  --format='value(status.url)'
```

輸出範例：
```
https://hwdc-2025-mcp-league-xxxxxxxxxx-de.a.run.app
```

#### 步驟 4: 更新 CORS 設定

使用剛才取得的 URL 更新 CORS：

```bash
export SERVICE_URL="https://hwdc-2025-mcp-league-xxxxxxxxxx-de.a.run.app"

gcloud run services update hwdc-2025-mcp-league \
  --region=asia-east1 \
  --update-env-vars=CORS_ALLOWED_ORIGINS="$SERVICE_URL"
```

如果有多個域名：
```bash
gcloud run services update hwdc-2025-mcp-league \
  --region=asia-east1 \
  --update-env-vars=CORS_ALLOWED_ORIGINS="https://your-app.run.app,https://www.your-domain.com,https://app.your-domain.com"
```

---

### 方式 2：自訂域名部署

如果你已經有自訂域名：

```bash
# 0. 生成 MCP Token
export MCP_AUTH_TOKEN=$(openssl rand -hex 32)

# 1. 部署時直接設定正確的 CORS
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_OPENAI_API_KEY="$OPENAI_API_KEY",_CORS_ALLOWED_ORIGINS="https://www.your-domain.com,https://app.your-domain.com",_MCP_SERVER_AUTH_TOKEN="$MCP_AUTH_TOKEN"

# 2. 設定域名對應
gcloud run domain-mappings create \
  --service=hwdc-2025-mcp-league \
  --domain=www.your-domain.com \
  --region=asia-east1
```

---

## 🔍 驗證部署

### 1. 檢查服務狀態

```bash
gcloud run services describe hwdc-2025-mcp-league \
  --region=asia-east1 \
  --format=yaml
```

### 2. 測試健康檢查

```bash
curl https://your-service-url.run.app/health
```

預期輸出：
```
healthy
```

### 3. 測試 API 文檔

在瀏覽器開啟：
```
https://your-service-url.run.app/api/docs
```

### 4. 檢查環境變數

```bash
gcloud run services describe hwdc-2025-mcp-league \
  --region=asia-east1 \
  --format='value(spec.template.spec.containers[0].env)'
```

### 5. 查看日誌

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=hwdc-2025-mcp-league" \
  --limit=50 \
  --format=json
```

---

## 🛠️ 常用管理指令

### 查看服務列表
```bash
gcloud run services list --region=asia-east1
```

### 查看特定服務詳情
```bash
gcloud run services describe hwdc-2025-mcp-league --region=asia-east1
```

### 更新環境變數
```bash
gcloud run services update hwdc-2025-mcp-league \
  --region=asia-east1 \
  --update-env-vars=KEY=VALUE
```

### 查看修訂版本
```bash
gcloud run revisions list \
  --service=hwdc-2025-mcp-league \
  --region=asia-east1
```

### 回滾到特定版本
```bash
gcloud run services update-traffic hwdc-2025-mcp-league \
  --region=asia-east1 \
  --to-revisions=REVISION_NAME=100
```

### 刪除服務
```bash
gcloud run services delete hwdc-2025-mcp-league --region=asia-east1
```

---

## ⚠️ 常見問題

### 問題 1: CORS 錯誤

**症狀**：瀏覽器顯示 CORS policy error

**解決方案**：
```bash
# 檢查當前 CORS 設定
gcloud run services describe hwdc-2025-mcp-league \
  --region=asia-east1 \
  --format='value(spec.template.spec.containers[0].env)' | grep CORS

# 更新為正確的值
gcloud run services update hwdc-2025-mcp-league \
  --region=asia-east1 \
  --update-env-vars=CORS_ALLOWED_ORIGINS="https://your-actual-url.run.app"
```

### 問題 2: OpenAI API 金鑰無效

**症狀**：應用啟動正常但 API 呼叫失敗

**解決方案**：
```bash
# 更新 API key
gcloud run services update hwdc-2025-mcp-league \
  --region=asia-east1 \
  --update-env-vars=OPENAI_API_KEY="sk-proj-新的key"
```

### 問題 3: 容器啟動失敗

**診斷步驟**：
```bash
# 1. 查看最新日誌
gcloud logging read "resource.type=cloud_run_revision" --limit=50

# 2. 檢查容器健康狀態
gcloud run services describe hwdc-2025-mcp-league \
  --region=asia-east1 \
  --format='value(status.conditions)'
```

### 問題 3.1: MCP_SERVER_AUTH_TOKEN 未設定

**症狀**：容器啟動時報錯 `ValueError: MCP_SERVER_AUTH_TOKEN environment variable is required`

**解決方案**：
```bash
# 1. 生成新的 token
export MCP_AUTH_TOKEN=$(openssl rand -hex 32)

# 2. 更新環境變數
gcloud run services update hwdc-2025-mcp-league \
  --region=asia-east1 \
  --update-env-vars=MCP_SERVER_AUTH_TOKEN="$MCP_AUTH_TOKEN"

# 3. 或重新部署
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=_OPENAI_API_KEY="$OPENAI_API_KEY",_CORS_ALLOWED_ORIGINS="$CORS_ORIGINS",_MCP_SERVER_AUTH_TOKEN="$MCP_AUTH_TOKEN"
```

### 問題 4: 記憶體或 CPU 不足

**調整資源配置**（需修改 `cloudbuild.yaml`）：
```yaml
- '--memory'
- '4Gi'  # 增加到 4GB
- '--cpu'
- '4'    # 增加到 4 CPU
```

---

## 📊 成本估算

**Cloud Run 計費項目**：
- CPU 使用時間
- 記憶體使用時間
- 請求次數
- 網路輸出流量

**範例計算**（每月）：
- 假設：10,000 requests/月，平均 100ms/request
- CPU: 2 vCPU × 0.1s × 10,000 = 2,000 vCPU-seconds
- Memory: 2GB × 0.1s × 10,000 = 2,000 GB-seconds
- 費用: 約 $1-2 USD/月（在免費額度內）

**免費額度**（每月）：
- 2 million requests
- 360,000 vCPU-seconds
- 180,000 GiB-seconds

---

## 🔐 安全性建議

### 1. 使用 Secret Manager 儲存敏感資料

```bash
# 建立 secret
echo -n "sk-proj-your-key" | gcloud secrets create openai-api-key --data-file=-

# 授權 Cloud Run 存取
gcloud secrets add-iam-policy-binding openai-api-key \
  --member=serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# 更新 cloudbuild.yaml 使用 secret
# --set-secrets=OPENAI_API_KEY=openai-api-key:latest
```

### 2. 限制流量來源

```bash
# 設定 Cloud Armor 或 IAP
# 僅允許特定 IP 訪問
```

### 3. 啟用容器掃描

```bash
gcloud container images scan gcr.io/$PROJECT_ID/hwdc-2025-mcp-league:latest
```

---

## 📚 相關資源

- [Cloud Run 官方文檔](https://cloud.google.com/run/docs)
- [Cloud Build 文檔](https://cloud.google.com/build/docs)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Cloud Run 定價](https://cloud.google.com/run/pricing)

---

## 🎯 快速部署檢查清單

部署前確認：

- [ ] 已安裝並設定 gcloud CLI
- [ ] 已設定正確的 GCP Project ID
- [ ] 已啟用必要的 API（Cloud Build, Cloud Run, Container Registry）
- [ ] 已準備 OpenAI API Key
- [ ] 已確認 CORS origins（或計劃兩階段部署）
- [ ] 已測試本地 Docker 環境

部署後確認：

- [ ] 健康檢查通過（`/health` 返回 "healthy"）
- [ ] API 文檔可訪問（`/api/docs`）
- [ ] CORS 設定正確
- [ ] 日誌無錯誤訊息
- [ ] 前端可正常呼叫 API

---

**最後更新**: 2025-10-10
**維護者**: Claude Code
