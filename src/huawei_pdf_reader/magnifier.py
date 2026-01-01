"""
华为平板PDF阅读器 - 放大镜模块

放大镜是辅助查阅工具，帮助用户在阅读过程中查看不懂的内容。
集成了放大、区域选择、翻译（英汉/汉英）和繁简转换功能。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from .models import (
    ConversionDirection,
    MagnifierAction,
    MagnifierConfig,
    MagnifierResult,
    TranslationDirection,
)
from .chinese_converter import IChineseConverter, ChineseConverter
from .translation_service import ITranslationService, MockTranslationService


class IOCREngine(ABC):
    """OCR 引擎接口"""
    
    @abstractmethod
    def extract_text(self, image_data: bytes, region: Optional[Tuple[float, float, float, float]] = None) -> str:
        """
        从图像中提取文字
        
        Args:
            image_data: 图像数据
            region: 可选的区域坐标 (x1, y1, x2, y2)
        
        Returns:
            提取的文字
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查 OCR 引擎是否可用"""
        pass


class MockOCREngine(IOCREngine):
    """
    模拟 OCR 引擎
    
    用于测试和演示，返回预设的文本。
    """
    
    def __init__(self):
        self._available = True
        self._mock_text = ""
    
    def set_mock_text(self, text: str) -> None:
        """设置模拟返回的文本"""
        self._mock_text = text
    
    def set_available(self, available: bool) -> None:
        """设置可用性"""
        self._available = available
    
    def extract_text(self, image_data: bytes, region: Optional[Tuple[float, float, float, float]] = None) -> str:
        """返回模拟文本"""
        if not self._available:
            return ""
        return self._mock_text
    
    def is_available(self) -> bool:
        return self._available


class IMagnifier(ABC):
    """放大镜接口 - 集成放大、翻译、繁简转换功能"""
    
    @abstractmethod
    def activate(self, config: MagnifierConfig) -> None:
        """激活放大镜"""
        pass
    
    @abstractmethod
    def deactivate(self) -> None:
        """关闭放大镜"""
        pass
    
    @abstractmethod
    def move_to(self, x: float, y: float) -> None:
        """移动放大镜位置"""
        pass
    
    @abstractmethod
    def get_magnified_region(self) -> bytes:
        """获取放大区域图像"""
        pass
    
    @abstractmethod
    def select_region(self, x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float, float, float]:
        """选择区域，返回文档坐标"""
        pass
    
    @abstractmethod
    def extract_text_from_region(self, region: Tuple[float, float, float, float]) -> str:
        """从选中区域提取文字（OCR）"""
        pass
    
    @abstractmethod
    def perform_action(self, action: MagnifierAction, region: Tuple[float, float, float, float]) -> MagnifierResult:
        """
        在选中区域执行操作（翻译或繁简转换）
        
        流程:
        1. 从区域提取文字（OCR）
        2. 根据action类型调用对应服务（翻译/转换）
        3. 返回结果供UI显示
        """
        pass
    
    @abstractmethod
    def get_available_actions(self) -> List[MagnifierAction]:
        """获取当前可用的操作列表"""
        pass


class Magnifier(IMagnifier):
    """
    放大镜实现 - 整合翻译和繁简转换服务
    
    Requirements: 5.1, 5.2, 5.3, 5.6, 5.7
    - 激活/关闭放大镜
    - 移动放大镜位置
    - 选择区域并提取文字
    - 执行翻译或繁简转换操作
    """
    
    def __init__(
        self,
        translation_service: Optional[ITranslationService] = None,
        chinese_converter: Optional[IChineseConverter] = None,
        ocr_engine: Optional[IOCREngine] = None
    ):
        """
        初始化放大镜
        
        Args:
            translation_service: 翻译服务实例
            chinese_converter: 繁简转换器实例
            ocr_engine: OCR 引擎实例
        """
        self._translation = translation_service or MockTranslationService()
        self._converter = chinese_converter or ChineseConverter()
        self._ocr = ocr_engine or MockOCREngine()
        
        self._config: Optional[MagnifierConfig] = None
        self._current_position: Tuple[float, float] = (0.0, 0.0)
        self._current_region: Optional[Tuple[float, float, float, float]] = None
        self._is_active: bool = False
        
        # 用于存储当前页面的图像数据（由外部设置）
        self._page_image_data: Optional[bytes] = None
    
    @property
    def is_active(self) -> bool:
        """放大镜是否激活"""
        return self._is_active
    
    @property
    def config(self) -> Optional[MagnifierConfig]:
        """当前配置"""
        return self._config
    
    @property
    def position(self) -> Tuple[float, float]:
        """当前位置"""
        return self._current_position
    
    def set_page_image(self, image_data: bytes) -> None:
        """
        设置当前页面的图像数据
        
        Args:
            image_data: 页面图像数据
        """
        self._page_image_data = image_data
    
    def activate(self, config: MagnifierConfig) -> None:
        """
        激活放大镜
        
        Args:
            config: 放大镜配置
        
        Requirements: 5.1
        """
        self._config = config
        self._is_active = True
        self._current_region = None
    
    def deactivate(self) -> None:
        """
        关闭放大镜
        
        Requirements: 5.1
        """
        self._is_active = False
        self._current_region = None
    
    def move_to(self, x: float, y: float) -> None:
        """
        移动放大镜位置
        
        Args:
            x: X 坐标
            y: Y 坐标
        
        Requirements: 5.2
        """
        self._current_position = (x, y)
    
    def get_magnified_region(self) -> bytes:
        """
        获取放大区域图像
        
        Returns:
            放大后的图像数据
        
        Requirements: 5.2
        """
        if not self._is_active or not self._config:
            return b""
        
        # 在实际实现中，这里会根据当前位置和配置
        # 从页面图像中裁剪并放大指定区域
        # 目前返回空数据，实际渲染由 UI 层处理
        return self._page_image_data or b""
    
    def select_region(self, x1: float, y1: float, x2: float, y2: float) -> Tuple[float, float, float, float]:
        """
        选择区域
        
        Args:
            x1, y1: 起始坐标
            x2, y2: 结束坐标
        
        Returns:
            规范化后的区域坐标 (min_x, min_y, max_x, max_y)
        
        Requirements: 5.3
        """
        # 规范化坐标（确保 min < max）
        min_x = min(x1, x2)
        min_y = min(y1, y2)
        max_x = max(x1, x2)
        max_y = max(y1, y2)
        
        self._current_region = (min_x, min_y, max_x, max_y)
        return self._current_region
    
    def extract_text_from_region(self, region: Tuple[float, float, float, float]) -> str:
        """
        从选中区域提取文字（OCR）
        
        Args:
            region: 区域坐标 (x1, y1, x2, y2)
        
        Returns:
            提取的文字
        
        Requirements: 5.3
        """
        if not self._ocr.is_available():
            return ""
        
        return self._ocr.extract_text(self._page_image_data or b"", region)
    
    def perform_action(self, action: MagnifierAction, region: Tuple[float, float, float, float]) -> MagnifierResult:
        """
        在选中区域执行操作（翻译或繁简转换）
        
        Args:
            action: 操作类型
            region: 区域坐标
        
        Returns:
            操作结果
        
        Requirements: 5.6, 5.7
        """
        # 1. OCR 提取文字
        text = self.extract_text_from_region(region)
        
        if not text:
            return MagnifierResult(
                action=action,
                original_text="",
                result_text="",
                success=False,
                error_message="无法识别文字",
                region=region
            )
        
        # 2. 根据操作类型处理
        result_text = ""
        error_msg = None
        success = True
        
        try:
            if action == MagnifierAction.TRANSLATE_EN_ZH:
                # 英译汉
                result = self._translation.translate(text, TranslationDirection.EN_TO_ZH)
                result_text = result.translated
                success = result.success
                error_msg = result.error_message
                
            elif action == MagnifierAction.TRANSLATE_ZH_EN:
                # 汉译英
                result = self._translation.translate(text, TranslationDirection.ZH_TO_EN)
                result_text = result.translated
                success = result.success
                error_msg = result.error_message
                
            elif action == MagnifierAction.CONVERT_T2S:
                # 繁转简
                result_text = self._converter.convert(text, ConversionDirection.TRADITIONAL_TO_SIMPLIFIED)
                
            elif action == MagnifierAction.CONVERT_S2T:
                # 简转繁
                result_text = self._converter.convert(text, ConversionDirection.SIMPLIFIED_TO_TRADITIONAL)
                
            elif action == MagnifierAction.MAGNIFY:
                # 仅放大，返回原文
                result_text = text
                
            else:
                success = False
                error_msg = f"不支持的操作类型: {action}"
                
        except Exception as e:
            success = False
            error_msg = str(e)
        
        return MagnifierResult(
            action=action,
            original_text=text,
            result_text=result_text,
            success=success,
            error_message=error_msg,
            region=region
        )
    
    def get_available_actions(self) -> List[MagnifierAction]:
        """
        获取当前可用的操作列表
        
        Returns:
            可用操作列表
        """
        actions = [MagnifierAction.MAGNIFY]
        
        # 检查翻译服务是否可用
        if self._translation.is_available():
            actions.append(MagnifierAction.TRANSLATE_EN_ZH)
            actions.append(MagnifierAction.TRANSLATE_ZH_EN)
        
        # 繁简转换始终可用（离线功能）
        actions.append(MagnifierAction.CONVERT_T2S)
        actions.append(MagnifierAction.CONVERT_S2T)
        
        return actions
    
    def perform_action_on_text(self, action: MagnifierAction, text: str) -> MagnifierResult:
        """
        直接对文本执行操作（不需要 OCR）
        
        Args:
            action: 操作类型
            text: 要处理的文本
        
        Returns:
            操作结果
        
        Note:
            这是一个便捷方法，用于已经有文本的情况。
        """
        if not text:
            return MagnifierResult(
                action=action,
                original_text="",
                result_text="",
                success=False,
                error_message="输入文本为空",
                region=None
            )
        
        result_text = ""
        error_msg = None
        success = True
        
        try:
            if action == MagnifierAction.TRANSLATE_EN_ZH:
                result = self._translation.translate(text, TranslationDirection.EN_TO_ZH)
                result_text = result.translated
                success = result.success
                error_msg = result.error_message
                
            elif action == MagnifierAction.TRANSLATE_ZH_EN:
                result = self._translation.translate(text, TranslationDirection.ZH_TO_EN)
                result_text = result.translated
                success = result.success
                error_msg = result.error_message
                
            elif action == MagnifierAction.CONVERT_T2S:
                result_text = self._converter.convert(text, ConversionDirection.TRADITIONAL_TO_SIMPLIFIED)
                
            elif action == MagnifierAction.CONVERT_S2T:
                result_text = self._converter.convert(text, ConversionDirection.SIMPLIFIED_TO_TRADITIONAL)
                
            elif action == MagnifierAction.MAGNIFY:
                result_text = text
                
            else:
                success = False
                error_msg = f"不支持的操作类型: {action}"
                
        except Exception as e:
            success = False
            error_msg = str(e)
        
        return MagnifierResult(
            action=action,
            original_text=text,
            result_text=result_text,
            success=success,
            error_message=error_msg,
            region=None
        )
