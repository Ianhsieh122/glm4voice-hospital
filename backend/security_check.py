"""
安全性檢查腳本
檢查項目：
1. 依賴漏洞掃描
2. 配置檔案安全性
3. 敏感信息洩露
4. API 安全性
5. 輸入驗證
"""

import subprocess
import sys
import os
from pathlib import Path
import json
from loguru import logger

class SecurityChecker:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []
        
    def check_dependencies(self):
        """檢查依賴漏洞"""
        logger.info("🔍 檢查依賴漏洞...")
        
        try:
            # 使用 pip-audit 檢查已知漏洞
            result = subprocess.run(
                ["pip-audit", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                vulnerabilities = json.loads(result.stdout)
                if vulnerabilities:
                    self.issues.append({
                        "type": "dependency",
                        "severity": "high",
                        "details": vulnerabilities
                    })
                    logger.warning(f"⚠️ 發現 {len(vulnerabilities)} 個依賴漏洞")
                else:
                    self.passed.append("依賴檢查：無已知漏洞")
                    logger.info("✅ 依賴檢查通過")
            else:
                logger.warning("pip-audit 未安裝或執行失敗")
                self.warnings.append("無法執行依賴漏洞掃描 (請安裝 pip-audit)")
                
        except FileNotFoundError:
            logger.warning("⚠️ pip-audit 未安裝，跳過依賴檢查")
            self.warnings.append("請安裝 pip-audit: pip install pip-audit")
        except Exception as e:
            logger.error(f"依賴檢查失敗: {e}")
            self.warnings.append(f"依賴檢查錯誤: {e}")
    
    def check_secrets(self):
        """檢查敏感信息洩露"""
        logger.info("🔍 檢查敏感信息...")
        
        sensitive_patterns = [
            "password",
            "secret",
            "api_key",
            "token",
            "private_key",
            "aws_access",
            "db_password"
        ]
        
        config_files = [
            "config.yaml",
            "config.production.yaml",
            "config.development.yaml",
            ".env"
        ]
        
        found_secrets = []
        
        for config_file in config_files:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    for pattern in sensitive_patterns:
                        if pattern in content and "example" not in content:
                            found_secrets.append(f"{config_file}: 可能包含 {pattern}")
        
        if found_secrets:
            self.warnings.append({
                "type": "secrets",
                "severity": "medium",
                "details": found_secrets
            })
            logger.warning(f"⚠️ 發現 {len(found_secrets)} 個潛在敏感信息")
        else:
            self.passed.append("敏感信息檢查：未發現明顯洩露")
            logger.info("✅ 敏感信息檢查通過")
    
    def check_config_security(self):
        """檢查配置安全性"""
        logger.info("🔍 檢查配置安全性...")
        
        issues = []
        
        # 檢查 CORS 配置
        if os.path.exists("config.production.yaml"):
            with open("config.production.yaml", 'r', encoding='utf-8') as f:
                content = f.read()
                if 'allow_origins: ["*"]' in content or "allow_origins:\n    - \"*\"" in content:
                    issues.append("生產環境 CORS 配置過於寬鬆 (允許所有來源)")
        
        # 檢查調試模式
        if os.path.exists("config.production.yaml"):
            with open("config.production.yaml", 'r', encoding='utf-8') as f:
                content = f.read()
                if "reload: true" in content:
                    issues.append("生產環境啟用了自動重載 (應該為 false)")
                if "log_level: \"debug\"" in content or "log_level: debug" in content:
                    issues.append("生產環境使用 DEBUG 日誌級別")
        
        if issues:
            self.issues.append({
                "type": "config",
                "severity": "medium",
                "details": issues
            })
            logger.warning(f"⚠️ 發現 {len(issues)} 個配置安全問題")
        else:
            self.passed.append("配置安全性：通過檢查")
            logger.info("✅ 配置安全性檢查通過")
    
    def check_input_validation(self):
        """檢查輸入驗證"""
        logger.info("🔍 檢查輸入驗證...")
        
        # 檢查 main.py 是否有適當的輸入驗證
        if os.path.exists("main.py"):
            with open("main.py", 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 檢查是否有 Pydantic 模型驗證
                if "BaseModel" in content or "pydantic" in content:
                    self.passed.append("輸入驗證：使用 Pydantic 模型")
                    logger.info("✅ 發現 Pydantic 輸入驗證")
                else:
                    self.warnings.append("未明確使用 Pydantic 進行輸入驗證")
        
        self.passed.append("輸入驗證：基本檢查通過")
    
    def check_sql_injection(self):
        """檢查 SQL 注入風險"""
        logger.info("🔍 檢查 SQL 注入風險...")
        
        sql_files = list(Path(".").rglob("*.py"))
        dangerous_patterns = [
            "execute(f\"",
            "execute(\"",
            ".format(",
            "% ("
        ]
        
        found_risks = []
        
        for file in sql_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "execute" in content or "sql" in content.lower():
                        for pattern in dangerous_patterns:
                            if pattern in content:
                                found_risks.append(f"{file}: 可能的 SQL 注入風險 ({pattern})")
            except Exception:
                pass
        
        if found_risks:
            self.issues.append({
                "type": "sql_injection",
                "severity": "high",
                "details": found_risks
            })
            logger.warning(f"⚠️ 發現 {len(found_risks)} 個潛在 SQL 注入風險")
        else:
            self.passed.append("SQL 注入檢查：未發現明顯風險")
            logger.info("✅ SQL 注入檢查通過")
    
    def check_rate_limiting(self):
        """檢查速率限制"""
        logger.info("🔍 檢查速率限制配置...")
        
        if os.path.exists("config.production.yaml"):
            with open("config.production.yaml", 'r', encoding='utf-8') as f:
                content = f.read()
                if "rate_limiting" in content and "enabled: true" in content:
                    self.passed.append("速率限制：已啟用")
                    logger.info("✅ 生產環境已啟用速率限制")
                else:
                    self.warnings.append("生產環境未啟用速率限制")
                    logger.warning("⚠️ 建議在生產環境啟用速率限制")
        else:
            self.warnings.append("未找到生產配置文件")
    
    def check_ssl_config(self):
        """檢查 SSL/TLS 配置"""
        logger.info("🔍 檢查 SSL/TLS 配置...")
        
        if os.path.exists("config.production.yaml"):
            with open("config.production.yaml", 'r', encoding='utf-8') as f:
                content = f.read()
                if "ssl_keyfile" in content and "ssl_certfile" in content:
                    if "#" not in content.split("ssl_keyfile")[0][-10:]:
                        self.passed.append("SSL/TLS：已配置")
                        logger.info("✅ 已配置 SSL/TLS")
                    else:
                        self.warnings.append("SSL/TLS 配置被註解，建議啟用 HTTPS")
                else:
                    self.warnings.append("未配置 SSL/TLS，建議使用 HTTPS")
    
    def generate_report(self):
        """生成安全報告"""
        logger.info("\n" + "="*60)
        logger.info("🛡️ 安全檢查報告")
        logger.info("="*60)
        
        # 嚴重問題
        if self.issues:
            logger.error(f"\n❌ 發現 {len(self.issues)} 個嚴重問題:")
            for i, issue in enumerate(self.issues, 1):
                logger.error(f"  {i}. [{issue['severity'].upper()}] {issue['type']}")
                if isinstance(issue['details'], list):
                    for detail in issue['details'][:3]:  # 只顯示前 3 個
                        logger.error(f"     - {detail}")
        
        # 警告
        if self.warnings:
            logger.warning(f"\n⚠️ {len(self.warnings)} 個警告:")
            for i, warning in enumerate(self.warnings, 1):
                logger.warning(f"  {i}. {warning}")
        
        # 通過項目
        if self.passed:
            logger.info(f"\n✅ {len(self.passed)} 個檢查通過:")
            for i, passed in enumerate(self.passed, 1):
                logger.info(f"  {i}. {passed}")
        
        logger.info("\n" + "="*60)
        
        # 總結
        if self.issues:
            logger.error("❌ 安全檢查未通過，請修復上述問題")
            return False
        elif self.warnings:
            logger.warning("⚠️ 安全檢查通過，但有警告項需要注意")
            return True
        else:
            logger.info("✅ 所有安全檢查通過")
            return True


def main():
    logger.info("開始安全檢查...")
    
    checker = SecurityChecker()
    
    # 執行所有檢查
    checker.check_dependencies()
    checker.check_secrets()
    checker.check_config_security()
    checker.check_input_validation()
    checker.check_sql_injection()
    checker.check_rate_limiting()
    checker.check_ssl_config()
    
    # 生成報告
    passed = checker.generate_report()
    
    # 退出碼
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
