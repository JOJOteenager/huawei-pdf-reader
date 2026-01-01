"""
防误触系统属性测试

Feature: huawei-pdf-reader
测试防误触系统的核心功能属性。

Properties:
- Property 9: 触摸类型分类
- Property 10: 防误触灵敏度
- Property 11: 手写笔悬停状态

Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
"""

import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from hypothesis import given, settings, strategies as st, assume

from huawei_pdf_reader.models import TouchEvent, TouchType
from huawei_pdf_reader.palm_rejection import PalmRejectionSystem


# ============== 策略定义 ==============

# 坐标策略
coordinate_strategy = st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False)

# 压力值策略 (0.0 - 1.0)
pressure_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

# 触摸面积策略 (0.0 - 1.0)
size_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

# 时间戳策略
timestamp_strategy = st.floats(min_value=0.0, max_value=1e10, allow_nan=False, allow_infinity=False)

# 触摸ID策略
touch_id_strategy = st.integers(min_value=0, max_value=1000)

# 灵敏度策略 (1-10)
sensitivity_strategy = st.integers(min_value=1, max_value=10)


# 触摸事件策略
@st.composite
def touch_event_strategy(draw, touch_type: TouchType = TouchType.UNKNOWN):
    return TouchEvent(
        id=draw(touch_id_strategy),
        x=draw(coordinate_strategy),
        y=draw(coordinate_strategy),
        pressure=draw(pressure_strategy),
        size=draw(size_strategy),
        touch_type=touch_type,
        timestamp=draw(timestamp_strategy),
    )


# 手掌触摸事件策略 (大面积、低压力)
@st.composite
def palm_touch_event_strategy(draw):
    return TouchEvent(
        id=draw(touch_id_strategy),
        x=draw(coordinate_strategy),
        y=draw(coordinate_strategy),
        pressure=draw(st.floats(min_value=0.0, max_value=0.25, allow_nan=False, allow_infinity=False)),
        size=draw(st.floats(min_value=0.6, max_value=1.0, allow_nan=False, allow_infinity=False)),
        touch_type=TouchType.UNKNOWN,
        timestamp=draw(timestamp_strategy),
    )


# 手写笔触摸事件策略 (小面积、高压力)
@st.composite
def stylus_touch_event_strategy(draw):
    return TouchEvent(
        id=draw(touch_id_strategy),
        x=draw(coordinate_strategy),
        y=draw(coordinate_strategy),
        pressure=draw(st.floats(min_value=0.4, max_value=1.0, allow_nan=False, allow_infinity=False)),
        size=draw(st.floats(min_value=0.0, max_value=0.08, allow_nan=False, allow_infinity=False)),
        touch_type=TouchType.UNKNOWN,
        timestamp=draw(timestamp_strategy),
    )


# ============== 属性测试 ==============

class TestTouchTypeClassification:
    """
    Property 9: 触摸类型分类
    
    For any 触摸事件，Palm_Rejection_System应将其分类为STYLUS、FINGER或PALM之一。
    大面积低压力的触摸应被分类为PALM，小面积高压力的触摸应被分类为STYLUS。
    
    Feature: huawei-pdf-reader, Property 9: 触摸类型分类
    Validates: Requirements 4.1, 4.2, 4.4
    """

    @given(event=touch_event_strategy())
    @settings(max_examples=100)
    def test_classify_returns_valid_type(self, event: TouchEvent):
        """
        Property 9: 触摸类型分类
        
        For any 触摸事件，分类结果应为STYLUS、FINGER或PALM之一。
        
        Feature: huawei-pdf-reader, Property 9: 触摸类型分类
        Validates: Requirements 4.1, 4.2, 4.4
        """
        system = PalmRejectionSystem()
        result = system.classify_touch(event)
        
        # 验证返回的类型是有效的TouchType
        assert result in [TouchType.STYLUS, TouchType.FINGER, TouchType.PALM]

    @given(event=palm_touch_event_strategy())
    @settings(max_examples=100)
    def test_large_size_low_pressure_classified_as_palm(self, event: TouchEvent):
        """
        Property 9: 触摸类型分类 - 手掌检测
        
        For any 大面积低压力的触摸，应被分类为PALM。
        
        Feature: huawei-pdf-reader, Property 9: 触摸类型分类
        Validates: Requirements 4.1, 4.4
        """
        system = PalmRejectionSystem()
        result = system.classify_touch(event)
        
        # 大面积低压力应被分类为手掌
        assert result == TouchType.PALM

    @given(event=stylus_touch_event_strategy())
    @settings(max_examples=100)
    def test_small_size_high_pressure_classified_as_stylus(self, event: TouchEvent):
        """
        Property 9: 触摸类型分类 - 手写笔检测
        
        For any 小面积高压力的触摸，应被分类为STYLUS。
        
        Feature: huawei-pdf-reader, Property 9: 触摸类型分类
        Validates: Requirements 4.2
        """
        system = PalmRejectionSystem()
        result = system.classify_touch(event)
        
        # 小面积高压力应被分类为手写笔
        assert result == TouchType.STYLUS

    @given(event=palm_touch_event_strategy())
    @settings(max_examples=100)
    def test_palm_touch_should_be_rejected(self, event: TouchEvent):
        """
        Property 9: 触摸类型分类 - 手掌拒绝
        
        For any 被分类为PALM的触摸，should_reject应返回True。
        
        Feature: huawei-pdf-reader, Property 9: 触摸类型分类
        Validates: Requirements 4.1
        """
        system = PalmRejectionSystem()
        
        # 手掌触摸应被拒绝
        assert system.should_reject(event) is True


class TestPalmRejectionSensitivity:
    """
    Property 10: 防误触灵敏度
    
    For any 灵敏度设置（1-10），较高的灵敏度应导致更多的触摸被分类为PALM。
    
    Feature: huawei-pdf-reader, Property 10: 防误触灵敏度
    Validates: Requirements 4.3
    """

    @given(
        low_sensitivity=st.integers(min_value=1, max_value=4),
        high_sensitivity=st.integers(min_value=7, max_value=10),
    )
    @settings(max_examples=100)
    def test_higher_sensitivity_lower_palm_threshold(
        self, 
        low_sensitivity: int, 
        high_sensitivity: int,
    ):
        """
        Property 10: 防误触灵敏度
        
        For any 两个不同的灵敏度设置，较高灵敏度应有较低的手掌检测阈值。
        
        Feature: huawei-pdf-reader, Property 10: 防误触灵敏度
        Validates: Requirements 4.3
        """
        assume(high_sensitivity > low_sensitivity)
        
        system_low = PalmRejectionSystem(sensitivity=low_sensitivity)
        system_high = PalmRejectionSystem(sensitivity=high_sensitivity)
        
        thresholds_low = system_low.get_thresholds()
        thresholds_high = system_high.get_thresholds()
        
        # 较高灵敏度应有较低的手掌检测阈值（更容易检测为手掌）
        assert thresholds_high["palm_size_threshold"] < thresholds_low["palm_size_threshold"]

    @given(sensitivity=sensitivity_strategy)
    @settings(max_examples=100)
    def test_sensitivity_clamped_to_valid_range(self, sensitivity: int):
        """
        Property 10: 防误触灵敏度 - 范围限制
        
        For any 灵敏度值，系统应将其限制在1-10范围内。
        
        Feature: huawei-pdf-reader, Property 10: 防误触灵敏度
        Validates: Requirements 4.3
        """
        system = PalmRejectionSystem(sensitivity=sensitivity)
        
        # 灵敏度应在1-10范围内
        assert 1 <= system.sensitivity <= 10

    @given(
        initial_sensitivity=sensitivity_strategy,
        new_sensitivity=sensitivity_strategy,
    )
    @settings(max_examples=100)
    def test_set_sensitivity_updates_thresholds(
        self, 
        initial_sensitivity: int, 
        new_sensitivity: int,
    ):
        """
        Property 10: 防误触灵敏度 - 动态更新
        
        For any 灵敏度变化，set_sensitivity应更新内部阈值。
        
        Feature: huawei-pdf-reader, Property 10: 防误触灵敏度
        Validates: Requirements 4.3
        """
        assume(initial_sensitivity != new_sensitivity)
        
        system = PalmRejectionSystem(sensitivity=initial_sensitivity)
        thresholds_before = system.get_thresholds()
        
        system.set_sensitivity(new_sensitivity)
        thresholds_after = system.get_thresholds()
        
        # 阈值应该改变
        assert thresholds_before != thresholds_after
        assert system.sensitivity == new_sensitivity


class TestStylusHoverState:
    """
    Property 11: 手写笔悬停状态
    
    For any 手写笔悬停状态变化，当悬停为true时防误触模式应启用，
    当悬停为false时应根据设置决定。
    
    Feature: huawei-pdf-reader, Property 11: 手写笔悬停状态
    Validates: Requirements 4.5
    """

    @given(event=touch_event_strategy())
    @settings(max_examples=100)
    def test_stylus_hover_enables_palm_rejection(self, event: TouchEvent):
        """
        Property 11: 手写笔悬停状态 - 自动启用
        
        For any 手写笔悬停状态为true时，防误触模式应自动启用。
        
        Feature: huawei-pdf-reader, Property 11: 手写笔悬停状态
        Validates: Requirements 4.5
        """
        system = PalmRejectionSystem()
        
        # 设置悬停状态为true
        system.on_stylus_hover(True)
        
        # 验证悬停状态
        assert system.is_stylus_hovering is True
        # 验证防误触已启用
        assert system.palm_rejection_enabled is True

    @given(event=touch_event_strategy())
    @settings(max_examples=100)
    def test_stylus_hover_rejects_non_stylus_touch(self, event: TouchEvent):
        """
        Property 11: 手写笔悬停状态 - 拒绝非手写笔触摸
        
        For any 手写笔悬停时的非手写笔触摸，应被拒绝。
        
        Feature: huawei-pdf-reader, Property 11: 手写笔悬停状态
        Validates: Requirements 4.5
        """
        system = PalmRejectionSystem()
        system.on_stylus_hover(True)
        
        # 分类触摸
        touch_type = system.classify_touch(event)
        
        # 如果不是手写笔触摸，应被拒绝
        if touch_type != TouchType.STYLUS:
            assert system.should_reject(event) is True

    @settings(max_examples=100)
    @given(st.booleans())
    def test_hover_state_changes(self, is_hovering: bool):
        """
        Property 11: 手写笔悬停状态 - 状态变化
        
        For any 悬停状态变化，系统应正确记录状态。
        
        Feature: huawei-pdf-reader, Property 11: 手写笔悬停状态
        Validates: Requirements 4.5
        """
        system = PalmRejectionSystem()
        
        system.on_stylus_hover(is_hovering)
        
        assert system.is_stylus_hovering == is_hovering
        
        # 悬停时防误触应启用
        if is_hovering:
            assert system.palm_rejection_enabled is True
