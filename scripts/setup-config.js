#!/usr/bin/env node

/**
 * Cross-platform configuration setup script
 * Replaces bash-based setup:config command
 *
 * This script:
 * 1. Creates backend/config/ directory if it doesn't exist
 * 2. Copies default_*.json files from backend/defaults/ to backend/config/
 * 3. Renames them by removing the "default_" prefix
 * 4. Skips files that already exist in config/ directory
 */

const fs = require('fs');
const path = require('path');

// ANSI color codes for better terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  red: '\x1b[31m',
};

function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function setupConfig() {
  const rootDir = path.resolve(__dirname, '..');
  const backendDir = path.join(rootDir, 'backend');
  const defaultsDir = path.join(backendDir, 'defaults');
  const configDir = path.join(backendDir, 'config');

  // Check if defaults directory exists
  if (!fs.existsSync(defaultsDir)) {
    log(`❌ 錯誤：找不到 defaults 目錄：${defaultsDir}`, colors.red);
    log(`請確認您在專案根目錄執行此腳本`, colors.red);
    process.exit(1);
  }

  // Create config directory if it doesn't exist
  if (!fs.existsSync(configDir)) {
    fs.mkdirSync(configDir, { recursive: true });
    log(`📁 已建立目錄：${configDir}`, colors.blue);
  }

  // Read all files from defaults directory
  const defaultFiles = fs.readdirSync(defaultsDir).filter((file) => {
    return file.startsWith('default_') && file.endsWith('.json');
  });

  if (defaultFiles.length === 0) {
    log(`⚠️  警告：在 defaults 目錄中找不到 default_*.json 檔案`, colors.yellow);
    log(`目錄：${defaultsDir}`, colors.yellow);
    return;
  }

  log(`\n找到 ${defaultFiles.length} 個預設配置檔案：`, colors.blue);

  let copiedCount = 0;
  let skippedCount = 0;

  // Copy each file to config directory
  defaultFiles.forEach((file) => {
    const sourcePath = path.join(defaultsDir, file);
    // Remove "default_" prefix from filename
    const targetFileName = file.replace(/^default_/, '');
    const targetPath = path.join(configDir, targetFileName);

    // Check if target file already exists
    if (fs.existsSync(targetPath)) {
      log(`⏭️  跳過 ${file} → ${targetFileName} (檔案已存在)`, colors.yellow);
      skippedCount++;
    } else {
      try {
        // Copy file content
        const content = fs.readFileSync(sourcePath, 'utf8');
        fs.writeFileSync(targetPath, content, 'utf8');
        log(`✅ 複製 ${file} → ${targetFileName}`, colors.green);
        copiedCount++;
      } catch (error) {
        log(`❌ 複製失敗：${file}`, colors.red);
        log(`   錯誤：${error.message}`, colors.red);
      }
    }
  });

  // Summary
  log(`\n${'='.repeat(60)}`, colors.blue);
  log(`🎉 配置檔案設置完成！`, colors.green);
  log(`   ✅ 成功複製：${copiedCount} 個檔案`, colors.green);
  if (skippedCount > 0) {
    log(`   ⏭️  已跳過：${skippedCount} 個檔案 (已存在)`, colors.yellow);
  }
  log(`${'='.repeat(60)}`, colors.blue);

  log(`\n您現在可以編輯以下檔案來自定義配置：`, colors.blue);
  const configFiles = fs.readdirSync(configDir).filter((f) => f.endsWith('.json'));
  configFiles.forEach((file) => {
    log(`  - backend/config/${file}`, colors.blue);
  });

  log(`\n💡 注意：backend/config/ 目錄已被 .gitignore 忽略`, colors.yellow);
  log(`   您的修改不會被提交到 Git\n`, colors.yellow);
}

// Main execution
try {
  setupConfig();
} catch (error) {
  log(`\n❌ 執行過程中發生錯誤：`, colors.red);
  log(error.message, colors.red);
  log(error.stack, colors.red);
  process.exit(1);
}
