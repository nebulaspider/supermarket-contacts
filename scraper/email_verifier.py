"""
智能邮箱验证器
通过 MX 记录检查和 SMTP 验证来判断邮箱是否有效。
纯免费方案，使用 Python 标准库。
"""
import logging
import re
import smtplib
import socket
from typing import Dict, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class EmailVerifier:
    """邮箱验证器：格式验证 + MX 记录 + SMTP 验证"""

    # 常见的邮箱域名白名单（高可信度）
    FREE_EMAIL_PROVIDERS = {
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'icloud.com', 'protonmail.com', 'qq.com', '163.com', '126.com',
    }

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def verify(self, email: str) -> Dict:
        """
        验证邮箱，返回详细结果。
        返回: {valid, format_valid, mx_valid, smtp_valid, confidence, reason}
        """
        result = {
            'email': email,
            'valid': False,
            'format_valid': False,
            'mx_valid': False,
            'smtp_valid': False,
            'confidence': 'low',
            'reason': '',
        }

        # 1. 格式验证
        if not self._check_format(email):
            result['reason'] = '格式无效'
            return result
        result['format_valid'] = True

        domain = email.split('@')[1].lower()

        # 2. 免费邮箱提供商（高可信度）
        if domain in self.FREE_EMAIL_PROVIDERS:
            result['mx_valid'] = True
            result['smtp_valid'] = True  # 假设免费邮箱有效
            result['valid'] = True
            result['confidence'] = 'high'
            result['reason'] = '免费邮箱提供商'
            return result

        # 3. MX 记录检查
        mx_records = self._check_mx(domain)
        if not mx_records:
            result['reason'] = '无 MX 记录'
            return result
        result['mx_valid'] = True

        # 4. SMTP 验证（可选，可能被防火墙阻止）
        smtp_valid = self._check_smtp(email, mx_records)
        if smtp_valid is not None:
            result['smtp_valid'] = smtp_valid
            if smtp_valid:
                result['valid'] = True
                result['confidence'] = 'high'
                result['reason'] = 'SMTP 验证通过'
            else:
                result['reason'] = 'SMTP 验证失败（邮箱可能不存在）'
        else:
            # SMTP 无法验证时，基于 MX 记录给中等可信度
            result['valid'] = True
            result['confidence'] = 'medium'
            result['reason'] = 'MX 记录存在，SMTP 无法验证'

        return result

    def _check_format(self, email: str) -> bool:
        """验证邮箱格式"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _check_mx(self, domain: str) -> list:
        """检查域名的 MX 记录"""
        try:
            import dns.resolver
            answers = dns.resolver.resolve(domain, 'MX')
            return [str(r.exchange).rstrip('.') for r in answers]
        except ImportError:
            # 如果没有 dnspython，使用 socket 简单检查
            try:
                socket.gethostbyname(domain)
                return [domain]
            except socket.gaierror:
                return []
        except Exception:
            return []

    def _check_smtp(self, email: str, mx_records: list) -> bool:
        """通过 SMTP 验证邮箱是否存在（可能被防火墙阻止）"""
        for mx in mx_records[:2]:  # 只试前两个 MX
            try:
                server = smtplib.SMTP(timeout=self.timeout)
                server.connect(mx, 25)
                server.helo()
                server.mail('verify@cyrus-ai.com')
                code, message = server.rcpt(email)
                server.quit()
                if code == 250:
                    return True
            except Exception as e:
                logger.debug(f"SMTP 验证失败 {email} via {mx}: {e}")
                continue
        return None  # 无法确定

    def generate_patterns(self, first_name: str, last_name: str, domain: str) -> list:
        """根据姓名和域名生成常见邮箱模式"""
        first = first_name.lower().strip()
        last = last_name.lower().strip()
        patterns = []

        if first and last:
            patterns.extend([
                f"{first}.{last}@{domain}",
                f"{first}@{domain}",
                f"{first[0]}{last}@{domain}",
                f"{first}{last[0]}@{domain}",
                f"{first}_{last}@{domain}",
                f"{last}.{first}@{domain}",
            ])
        elif first:
            patterns.extend([
                f"{first}@{domain}",
                f"{first}.{last}@{domain}" if last else f"{first}@{domain}",
            ])

        return list(dict.fromkeys(patterns))  # 去重保序
