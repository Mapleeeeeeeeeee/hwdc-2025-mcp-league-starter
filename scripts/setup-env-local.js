#!/usr/bin/env node

/**
 * Cross-platform local environment setup script
 * Replaces bash-based setup:env:local command
 *
 * This script:
 * 1. Copies backend/.env.example to backend/.env
 * 2. Displays helpful setup instructions
 */

const fs = require('fs');
const path = require('path');

// ANSI color codes for better terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
  red: '\x1b[31m',
  bold: '\x1b[1m',
};

function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function setupEnvLocal() {
  const rootDir = path.resolve(__dirname, '..');
  const backendDir = path.join(rootDir, 'backend');
  const exampleEnvPath = path.join(backendDir, '.env.example');
  const targetEnvPath = path.join(backendDir, '.env');

  // Check if .env.example exists
  if (!fs.existsSync(exampleEnvPath)) {
    log(`❌ 錯誤：找不到範例檔案：${exampleEnvPath}`, colors.red);
    log(`請確認您在專案根目錄執行此腳本`, colors.red);
    process.exit(1);
  }

  // Check if .env already exists
  if (fs.existsSync(targetEnvPath)) {
    log(`⚠️  警告：backend/.env 已存在！`, colors.yellow);
    log(`為了避免覆蓋您的設定，此操作已取消。`, colors.yellow);
    log(`\n如果您確定要重新建立，請先手動刪除：`, colors.yellow);
    log(`  rm backend/.env`, colors.cyan);
    log(`然後重新執行此腳本。\n`, colors.yellow);
    process.exit(0);
  }

  try {
    // Copy .env.example to .env
    const content = fs.readFileSync(exampleEnvPath, 'utf8');
    fs.writeFileSync(targetEnvPath, content, 'utf8');

    log(`\n${'='.repeat(70)}`, colors.blue);
    log(`✅ 已複製 backend/.env.example 到 backend/.env`, colors.green);
    log(`${'='.repeat(70)}`, colors.blue);

    // Display setup instructions
    log(`\n${colors.bold}📝 接下來請編輯 backend/.env 並設置以下變數：${colors.reset}`, colors.cyan);
    log(`\n${colors.bold}必填變數：${colors.reset}`, colors.yellow);
    log(`  1. ${colors.bold}OPENAI_API_KEY${colors.reset}`, colors.cyan);
    log(`     └─ 您的 OpenAI API 金鑰`, colors.cyan);
    log(`     └─ 格式範例：sk-proj-xxxxxxxxxxxx...`, colors.cyan);
    log(`     └─ 申請連結：https://platform.openai.com/api-keys\n`, colors.cyan);

    log(`  2. ${colors.bold}MCP_SERVER_AUTH_TOKEN${colors.reset}`, colors.cyan);
    log(`     └─ MCP 伺服器認證 Token`, colors.cyan);
    log(`     └─ 可以使用任意字串，或用以下指令生成：`, colors.cyan);
    log(`     └─ ${colors.yellow}openssl rand -base64 32${colors.reset}\n`, colors.yellow);

    log(`${colors.bold}可選變數：${colors.reset}`, colors.yellow);
    log(`  3. ${colors.bold}AS_A_MCP_SERVER${colors.reset} (預設: false)`, colors.cyan);
    log(`     └─ 設為 ${colors.green}true${colors.reset} 將後端作為 MCP 服務器運行`, colors.cyan);
    log(`     └─ 啟用後可讓其他節點透過 HTTP 呼叫此伺服器的工具\n`, colors.cyan);

    log(`${colors.bold}快速編輯指令：${colors.reset}`, colors.blue);
    log(`  # 使用 VS Code`, colors.cyan);
    log(`  code backend/.env\n`, colors.yellow);
    log(`  # 使用 Vim`, colors.cyan);
    log(`  vim backend/.env\n`, colors.yellow);
    log(`  # 使用 Nano`, colors.cyan);
    log(`  nano backend/.env\n`, colors.yellow);
    log(`  # Windows Notepad`, colors.cyan);
    log(`  notepad backend\\.env\n`, colors.yellow);

    log(`💡 ${colors.bold}提示：${colors.reset}編輯完成後，請執行以下指令啟動開發伺服器：`, colors.blue);
    log(`  pnpm dev\n`, colors.yellow);

    log(`${'='.repeat(70)}\n`, colors.blue);
  } catch (error) {
    log(`\n❌ 複製檔案時發生錯誤：`, colors.red);
    log(error.message, colors.red);
    process.exit(1);
  }
}

// Main execution
try {
  setupEnvLocal();
} catch (error) {
  log(`\n❌ 執行過程中發生錯誤：`, colors.red);
  log(error.message, colors.red);
  log(error.stack, colors.red);
  process.exit(1);
}
