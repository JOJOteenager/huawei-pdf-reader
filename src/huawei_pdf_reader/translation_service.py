"""
华为平板PDF阅读器 - 翻译服务

提供英汉互译功能，支持百度翻译 API。
"""

import hashlib
import random
import time
from abc import ABC, abstractmethod
from typing import Optional
import urllib.parse

try:
    import requests
except ImportError:
    requests = None

from .models import TranslationDirection, TranslationResult


class ITranslationService(ABC):
    """翻译服务接口"""
    
    @abstractmethod
    def translate(self, text: str, direction: TranslationDirection) -> TranslationResult:
        """翻译文本"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查服务是否可用"""
        pass


class TranslationService(ITranslationService):
    """
    翻译服务实现
    
    使用百度翻译 API 进行英汉互译。
    
    Requirements: 5.4, 5.5
    - 英译汉
    - 汉译英
    """
    
    # 百度翻译 API 配置
    BAIDU_API_URL = "https://fanyi-api.baidu.com/api/trans/vip/translate"
    
    def __init__(self, app_id: Optional[str] = None, secret_key: Optional[str] = None):
        """
        初始化翻译服务
        
        Args:
            app_id: 百度翻译 API 的 APP ID
            secret_key: 百度翻译 API 的密钥
        """
        if requests is None:
            raise ImportError(
                "requests library is not installed. "
                "Please install it with: pip install requests"
            )
        
        self._app_id = app_id
        self._secret_key = secret_key
        self._last_request_time = 0
        self._min_request_interval = 1.0  # 最小请求间隔（秒）
    
    def configure(self, app_id: str, secret_key: str) -> None:
        """
        配置 API 凭证
        
        Args:
            app_id: 百度翻译 API 的 APP ID
            secret_key: 百度翻译 API 的密钥
        """
        self._app_id = app_id
        self._secret_key = secret_key
    
    def is_available(self) -> bool:
        """
        检查服务是否可用
        
        Returns:
            如果 API 凭证已配置且网络可用，返回 True
        """
        if not self._app_id or not self._secret_key:
            return False
        
        # 简单的网络检查
        try:
            response = requests.head("https://fanyi-api.baidu.com", timeout=5)
            return response.status_code < 500
        except Exception:
            return False
    
    def translate(self, text: str, direction: TranslationDirection) -> TranslationResult:
        """
        翻译文本
        
        Args:
            text: 要翻译的文本
            direction: 翻译方向 (EN_TO_ZH 或 ZH_TO_EN)
        
        Returns:
            TranslationResult 对象，包含翻译结果
        
        Requirements: 5.4, 5.5
        """
        if not text or not text.strip():
            return TranslationResult(
                original=text,
                translated="",
                direction=direction,
                success=False,
                error_message="输入文本为空"
            )
        
        # 检查 API 凭证
        if not self._app_id or not self._secret_key:
            return TranslationResult(
                original=text,
                translated="",
                direction=direction,
                success=False,
                error_message="翻译服务未配置，请设置 API 凭证"
            )
        
        # 确定源语言和目标语言
        if direction == TranslationDirection.EN_TO_ZH:
            from_lang = "en"
            to_lang = "zh"
        elif direction == TranslationDirection.ZH_TO_EN:
            from_lang = "zh"
            to_lang = "en"
        else:
            return TranslationResult(
                original=text,
                translated="",
                direction=direction,
                success=False,
                error_message=f"不支持的翻译方向: {direction}"
            )
        
        # 限流：确保请求间隔
        self._rate_limit()
        
        try:
            # 调用百度翻译 API
            result = self._call_baidu_api(text, from_lang, to_lang)
            
            if result.get("error_code"):
                error_msg = self._get_error_message(result.get("error_code"))
                return TranslationResult(
                    original=text,
                    translated="",
                    direction=direction,
                    success=False,
                    error_message=error_msg
                )
            
            # 提取翻译结果
            trans_result = result.get("trans_result", [])
            if trans_result:
                translated_text = "\n".join([item.get("dst", "") for item in trans_result])
                return TranslationResult(
                    original=text,
                    translated=translated_text,
                    direction=direction,
                    success=True
                )
            else:
                return TranslationResult(
                    original=text,
                    translated="",
                    direction=direction,
                    success=False,
                    error_message="翻译结果为空"
                )
        
        except requests.exceptions.Timeout:
            return TranslationResult(
                original=text,
                translated="",
                direction=direction,
                success=False,
                error_message="请求超时，请检查网络连接"
            )
        except requests.exceptions.ConnectionError:
            return TranslationResult(
                original=text,
                translated="",
                direction=direction,
                success=False,
                error_message="网络不可用，请检查连接"
            )
        except Exception as e:
            return TranslationResult(
                original=text,
                translated="",
                direction=direction,
                success=False,
                error_message=f"翻译失败: {str(e)}"
            )
    
    def _call_baidu_api(self, text: str, from_lang: str, to_lang: str) -> dict:
        """
        调用百度翻译 API
        
        Args:
            text: 要翻译的文本
            from_lang: 源语言代码
            to_lang: 目标语言代码
        
        Returns:
            API 响应的 JSON 数据
        """
        # 生成签名
        salt = str(random.randint(32768, 65536))
        sign = self._generate_sign(text, salt)
        
        # 构建请求参数
        params = {
            "q": text,
            "from": from_lang,
            "to": to_lang,
            "appid": self._app_id,
            "salt": salt,
            "sign": sign
        }
        
        # 发送请求
        response = requests.get(
            self.BAIDU_API_URL,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        return response.json()
    
    def _generate_sign(self, text: str, salt: str) -> str:
        """
        生成百度翻译 API 签名
        
        签名算法: MD5(appid + q + salt + secret_key)
        
        Args:
            text: 要翻译的文本
            salt: 随机数
        
        Returns:
            签名字符串
        """
        sign_str = f"{self._app_id}{text}{salt}{self._secret_key}"
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest()
    
    def _rate_limit(self) -> None:
        """限流：确保请求间隔不小于最小间隔"""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        
        self._last_request_time = time.time()
    
    def _get_error_message(self, error_code: str) -> str:
        """
        获取错误信息
        
        Args:
            error_code: 百度翻译 API 错误码
        
        Returns:
            错误信息描述
        """
        error_messages = {
            "52000": "成功",
            "52001": "请求超时，请重试",
            "52002": "系统错误，请重试",
            "52003": "未授权用户，请检查 APP ID",
            "54000": "必填参数为空",
            "54001": "签名错误，请检查密钥",
            "54003": "访问频率受限，请降低调用频率",
            "54004": "账户余额不足",
            "54005": "长 query 请求频繁，请降低长文本频率",
            "58000": "客户端 IP 非法",
            "58001": "译文语言方向不支持",
            "58002": "服务当前已关闭",
            "90107": "认证未通过或未生效",
        }
        return error_messages.get(str(error_code), f"未知错误: {error_code}")


class MockTranslationService(ITranslationService):
    """
    模拟翻译服务
    
    用于测试和离线模式，提供简单的模拟翻译功能。
    """
    
    def __init__(self):
        """初始化模拟翻译服务"""
        self._available = True
        
        # 简单的词典映射（用于演示）
        self._en_to_zh = {
            "hello": "你好",
            "world": "世界",
            "book": "书",
            "read": "阅读",
            "write": "写",
            "pen": "笔",
            "paper": "纸",
            "document": "文档",
            "file": "文件",
            "page": "页面",
            "text": "文本",
            "translate": "翻译",
            "convert": "转换",
            "chinese": "中文",
            "english": "英文",
            "traditional": "繁体",
            "simplified": "简体",
        }
        
        # 反向映射
        self._zh_to_en = {v: k for k, v in self._en_to_zh.items()}
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self._available
    
    def set_available(self, available: bool) -> None:
        """设置服务可用性（用于测试）"""
        self._available = available
    
    def translate(self, text: str, direction: TranslationDirection) -> TranslationResult:
        """
        模拟翻译文本
        
        Args:
            text: 要翻译的文本
            direction: 翻译方向
        
        Returns:
            TranslationResult 对象
        """
        if not self._available:
            return TranslationResult(
                original=text,
                translated="",
                direction=direction,
                success=False,
                error_message="翻译服务不可用"
            )
        
        if not text or not text.strip():
            return TranslationResult(
                original=text,
                translated="",
                direction=direction,
                success=False,
                error_message="输入文本为空"
            )
        
        # 选择词典
        if direction == TranslationDirection.EN_TO_ZH:
            dictionary = self._en_to_zh
        else:
            dictionary = self._zh_to_en
        
        # 简单的单词替换翻译
        words = text.lower().split()
        translated_words = []
        
        for word in words:
            # 移除标点符号
            clean_word = word.strip(".,!?;:'\"")
            if clean_word in dictionary:
                translated_words.append(dictionary[clean_word])
            else:
                # 未知单词保持原样
                translated_words.append(word)
        
        translated_text = " ".join(translated_words)
        
        return TranslationResult(
            original=text,
            translated=translated_text,
            direction=direction,
            success=True
        )
