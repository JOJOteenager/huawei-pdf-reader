"""
华为平板PDF阅读器 - 防误触系统

实现手掌拒绝功能，区分手写笔、手指和手掌触摸。
"""

from abc import ABC, abstractmethod
from typing import List

from .models import TouchEvent, TouchType


class IPalmRejectionSystem(ABC):
    """防误触系统接口"""
    
    @abstractmethod
    def classify_touch(self, event: TouchEvent) -> TouchType:
        """分类触摸类型"""
        pass
    
    @abstractmethod
    def should_reject(self, event: TouchEvent) -> bool:
        """判断是否应该拒绝该触摸"""
        pass
    
    @abstractmethod
    def set_sensitivity(self, level: int) -> None:
        """设置灵敏度 (1-10)"""
        pass
    
    @abstractmethod
    def on_stylus_hover(self, is_hovering: bool) -> None:
        """手写笔悬停状态变化"""
        pass


class PalmRejectionSystem(IPalmRejectionSystem):
    """
    防误触系统实现
    
    基于触摸面积和压力来分类触摸类型：
    - 手写笔(STYLUS): 小面积、高压力
    - 手指(FINGER): 中等面积、中等压力
    - 手掌(PALM): 大面积、低压力
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    
    # 默认阈值常量
    DEFAULT_PALM_SIZE_THRESHOLD = 0.5  # 大于此值视为手掌
    DEFAULT_STYLUS_SIZE_THRESHOLD = 0.1  # 小于此值视为手写笔
    DEFAULT_STYLUS_PRESSURE_THRESHOLD = 0.3  # 高于此值且面积小视为手写笔
    
    def __init__(self, sensitivity: int = 7):
        """
        初始化防误触系统
        
        Args:
            sensitivity: 灵敏度级别 (1-10)，默认为7
        """
        self._sensitivity = self._clamp_sensitivity(sensitivity)
        self._stylus_hovering = False
        self._palm_rejection_enabled = True
        self._update_thresholds()
    
    def _clamp_sensitivity(self, level: int) -> int:
        """将灵敏度限制在1-10范围内"""
        return max(1, min(10, level))
    
    def _update_thresholds(self) -> None:
        """根据灵敏度更新阈值"""
        # 灵敏度越高，手掌检测阈值越低（更容易将触摸判定为手掌）
        # 灵敏度范围: 1-10
        # 灵敏度为1时，palm_size_threshold = 0.7 (不太敏感)
        # 灵敏度为10时，palm_size_threshold = 0.25 (非常敏感)
        sensitivity_factor = (self._sensitivity - 1) / 9.0  # 0.0 to 1.0
        
        self._palm_size_threshold = 0.7 - (sensitivity_factor * 0.45)
        self._stylus_size_threshold = 0.15 - (sensitivity_factor * 0.05)
        self._stylus_pressure_threshold = 0.4 - (sensitivity_factor * 0.15)
    
    @property
    def sensitivity(self) -> int:
        """获取当前灵敏度"""
        return self._sensitivity
    
    @property
    def is_stylus_hovering(self) -> bool:
        """获取手写笔悬停状态"""
        return self._stylus_hovering
    
    @property
    def palm_rejection_enabled(self) -> bool:
        """获取防误触是否启用"""
        return self._palm_rejection_enabled
    
    def classify_touch(self, event: TouchEvent) -> TouchType:
        """
        分类触摸类型
        
        基于触摸面积和压力进行分类：
        - 大面积低压力 -> PALM
        - 小面积高压力 -> STYLUS
        - 其他情况 -> FINGER
        
        Args:
            event: 触摸事件
            
        Returns:
            TouchType: 分类后的触摸类型
        """
        # 如果事件已经有明确的类型（如来自硬件的手写笔事件），直接返回
        if event.touch_type == TouchType.STYLUS:
            return TouchType.STYLUS
        
        size = event.size
        pressure = event.pressure
        
        # 大面积低压力 -> 手掌
        if size >= self._palm_size_threshold and pressure < 0.3:
            return TouchType.PALM
        
        # 小面积高压力 -> 手写笔
        if size <= self._stylus_size_threshold and pressure >= self._stylus_pressure_threshold:
            return TouchType.STYLUS
        
        # 中等情况 -> 手指
        return TouchType.FINGER
    
    def should_reject(self, event: TouchEvent) -> bool:
        """
        判断是否应该拒绝该触摸
        
        在以下情况下拒绝触摸：
        1. 防误触功能启用且触摸被分类为手掌
        2. 手写笔悬停时，拒绝所有非手写笔触摸
        
        Args:
            event: 触摸事件
            
        Returns:
            bool: True表示应该拒绝，False表示应该接受
        """
        if not self._palm_rejection_enabled:
            return False
        
        touch_type = self.classify_touch(event)
        
        # 手掌触摸总是被拒绝
        if touch_type == TouchType.PALM:
            return True
        
        # 手写笔悬停时，拒绝非手写笔触摸
        if self._stylus_hovering and touch_type != TouchType.STYLUS:
            return True
        
        return False
    
    def set_sensitivity(self, level: int) -> None:
        """
        设置防误触灵敏度
        
        灵敏度越高，越容易将触摸判定为手掌。
        
        Args:
            level: 灵敏度级别 (1-10)
        """
        self._sensitivity = self._clamp_sensitivity(level)
        self._update_thresholds()
    
    def on_stylus_hover(self, is_hovering: bool) -> None:
        """
        手写笔悬停状态变化
        
        当手写笔悬停在屏幕上方时，自动启用防误触模式。
        
        Args:
            is_hovering: True表示手写笔正在悬停
        """
        self._stylus_hovering = is_hovering
        
        # 手写笔悬停时自动启用防误触
        if is_hovering:
            self._palm_rejection_enabled = True
    
    def enable_palm_rejection(self, enabled: bool = True) -> None:
        """
        启用或禁用防误触功能
        
        Args:
            enabled: True启用，False禁用
        """
        self._palm_rejection_enabled = enabled
    
    def get_thresholds(self) -> dict:
        """
        获取当前阈值（用于调试）
        
        Returns:
            dict: 包含当前阈值的字典
        """
        return {
            "palm_size_threshold": self._palm_size_threshold,
            "stylus_size_threshold": self._stylus_size_threshold,
            "stylus_pressure_threshold": self._stylus_pressure_threshold,
        }
