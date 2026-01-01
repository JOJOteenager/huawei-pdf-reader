"""
注释引擎属性测试

Feature: huawei-pdf-reader
测试注释引擎的核心功能属性。

Properties:
- Property 5: 笔画设置应用
- Property 6: 橡皮擦功能
- Property 7: 注释保存往返一致性
- Property 8: 压感笔迹粗细

Validates: Requirements 3.2, 3.3, 3.4, 3.5, 3.6
"""

import sys
import tempfile
from pathlib import Path

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from hypothesis import given, settings, strategies as st, assume

from huawei_pdf_reader.models import (
    Annotation,
    PenType,
    Stroke,
    StrokePoint,
)
from huawei_pdf_reader.annotation_engine import AnnotationEngine
from huawei_pdf_reader.database import Database


# ============== 策略定义 ==============

# 笔类型策略
pen_type_strategy = st.sampled_from([
    PenType.BALLPOINT,
    PenType.FOUNTAIN,
    PenType.HIGHLIGHTER,
    PenType.PENCIL,
    PenType.MARKER,
])

# 颜色策略 (十六进制颜色)
color_strategy = st.from_regex(r"#[0-9A-Fa-f]{6}", fullmatch=True)

# 笔画宽度策略
width_strategy = st.floats(min_value=0.5, max_value=20.0, allow_nan=False, allow_infinity=False)

# 坐标策略
coordinate_strategy = st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False)

# 压力值策略
pressure_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

# 时间戳策略
timestamp_strategy = st.floats(min_value=0.0, max_value=1e10, allow_nan=False, allow_infinity=False)

# 页码策略
page_num_strategy = st.integers(min_value=1, max_value=1000)


# 笔画点策略
@st.composite
def stroke_point_strategy(draw):
    return StrokePoint(
        x=draw(coordinate_strategy),
        y=draw(coordinate_strategy),
        pressure=draw(pressure_strategy),
        timestamp=draw(timestamp_strategy),
    )


# 笔画策略
@st.composite
def stroke_strategy(draw):
    points = draw(st.lists(stroke_point_strategy(), min_size=1, max_size=50))
    return Stroke(
        id=draw(st.uuids().map(str)),
        pen_type=draw(pen_type_strategy),
        color=draw(color_strategy),
        width=draw(width_strategy),
        points=points,
    )


# 注释策略
@st.composite
def annotation_strategy(draw):
    strokes = draw(st.lists(stroke_strategy(), min_size=0, max_size=10))
    return Annotation(
        id=draw(st.uuids().map(str)),
        page_num=draw(page_num_strategy),
        strokes=strokes,
    )


# ============== 属性测试 ==============

class TestStrokeSettingsApplication:
    """
    Property 5: 笔画设置应用
    
    For any 笔类型、颜色和粗细设置，创建的笔画应使用这些设置值。
    
    Feature: huawei-pdf-reader, Property 5: 笔画设置应用
    Validates: Requirements 3.2, 3.3
    """

    @given(
        pen_type=pen_type_strategy,
        color=color_strategy,
        width=width_strategy,
    )
    @settings(max_examples=100)
    def test_stroke_settings_applied(self, pen_type: PenType, color: str, width: float):
        """
        Property 5: 笔画设置应用
        
        For any 笔类型、颜色和粗细设置，创建的笔画应使用这些设置值。
        
        Feature: huawei-pdf-reader, Property 5: 笔画设置应用
        Validates: Requirements 3.2, 3.3
        """
        engine = AnnotationEngine()
        
        # 开始笔画
        stroke_id = engine.start_stroke(pen_type, color, width)
        
        # 添加一些点
        engine.add_point(stroke_id, 10.0, 10.0, 0.5)
        engine.add_point(stroke_id, 20.0, 20.0, 0.6)
        
        # 结束笔画
        stroke = engine.end_stroke(stroke_id)
        
        # 验证笔画设置
        assert stroke.pen_type == pen_type
        assert stroke.color == color
        assert stroke.width == width


class TestEraserFunctionality:
    """
    Property 6: 橡皮擦功能
    
    For any 包含笔画的页面，在笔画位置使用橡皮擦后，该笔画应从页面注释中移除。
    
    Feature: huawei-pdf-reader, Property 6: 橡皮擦功能
    Validates: Requirements 3.4
    """

    @given(
        page_num=page_num_strategy,
        pen_type=pen_type_strategy,
        color=color_strategy,
        width=width_strategy,
        x=coordinate_strategy,
        y=coordinate_strategy,
    )
    @settings(max_examples=100)
    def test_eraser_removes_stroke(
        self, 
        page_num: int, 
        pen_type: PenType, 
        color: str, 
        width: float,
        x: float,
        y: float,
    ):
        """
        Property 6: 橡皮擦功能
        
        For any 包含笔画的页面，在笔画位置使用橡皮擦后，该笔画应从页面注释中移除。
        
        Feature: huawei-pdf-reader, Property 6: 橡皮擦功能
        Validates: Requirements 3.4
        """
        engine = AnnotationEngine()
        
        # 创建笔画
        stroke_id = engine.start_stroke(pen_type, color, width)
        engine.add_point(stroke_id, x, y, 0.5)
        engine.add_point(stroke_id, x + 10, y + 10, 0.6)
        stroke = engine.end_stroke(stroke_id)
        
        # 添加笔画到页面
        engine.add_stroke_to_page(page_num, stroke)
        
        # 验证笔画存在
        annotations_before = engine.get_annotations(page_num)
        assert len(annotations_before) > 0
        strokes_before = sum(len(a.strokes) for a in annotations_before)
        assert strokes_before == 1
        
        # 使用橡皮擦擦除
        erased_ids = engine.erase_at(page_num, x, y, radius=15.0)
        
        # 验证笔画被移除
        assert stroke.id in erased_ids
        annotations_after = engine.get_annotations(page_num)
        strokes_after = sum(len(a.strokes) for a in annotations_after)
        assert strokes_after == 0


class TestAnnotationRoundTrip:
    """
    Property 7: 注释保存往返一致性
    
    For any 有效的注释数据，保存后再加载应产生等效的注释数据。
    
    Feature: huawei-pdf-reader, Property 7: 注释保存往返一致性
    Validates: Requirements 3.5
    """

    @given(annotation=annotation_strategy())
    @settings(max_examples=100)
    def test_annotation_round_trip(self, annotation: Annotation):
        """
        Property 7: 注释保存往返一致性
        
        For any 有效的注释数据，保存后再加载应产生等效的注释数据。
        
        Feature: huawei-pdf-reader, Property 7: 注释保存往返一致性
        Validates: Requirements 3.5
        """
        # 使用临时数据库
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path)
            
            doc_id = "test_doc_123"
            
            # 保存注释
            db.save_annotation(doc_id, annotation)
            
            # 加载注释
            loaded_annotations = db.load_annotations(doc_id)
            
            # 验证加载的注释
            assert len(loaded_annotations) == 1
            loaded = loaded_annotations[0]
            
            # 验证基本属性
            assert loaded.id == annotation.id
            assert loaded.page_num == annotation.page_num
            assert len(loaded.strokes) == len(annotation.strokes)
            
            # 验证每个笔画
            for orig_stroke, loaded_stroke in zip(annotation.strokes, loaded.strokes):
                assert loaded_stroke.id == orig_stroke.id
                assert loaded_stroke.pen_type == orig_stroke.pen_type
                assert loaded_stroke.color == orig_stroke.color
                assert loaded_stroke.width == orig_stroke.width
                assert len(loaded_stroke.points) == len(orig_stroke.points)
                
                # 验证每个点
                for orig_point, loaded_point in zip(orig_stroke.points, loaded_stroke.points):
                    assert abs(loaded_point.x - orig_point.x) < 1e-6
                    assert abs(loaded_point.y - orig_point.y) < 1e-6
                    assert abs(loaded_point.pressure - orig_point.pressure) < 1e-6
                    assert abs(loaded_point.timestamp - orig_point.timestamp) < 1e-6


class TestPressureSensitivity:
    """
    Property 8: 压感笔迹粗细
    
    For any 两个不同压力值的笔画点（在相同笔设置下），压力值较大的点应产生较粗的笔迹。
    
    Feature: huawei-pdf-reader, Property 8: 压感笔迹粗细
    Validates: Requirements 3.6
    """

    @given(
        base_width=width_strategy,
        pressure1=st.floats(min_value=0.0, max_value=0.49, allow_nan=False, allow_infinity=False),
        pressure2=st.floats(min_value=0.51, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_pressure_affects_width(
        self, 
        base_width: float, 
        pressure1: float, 
        pressure2: float,
    ):
        """
        Property 8: 压感笔迹粗细
        
        For any 两个不同压力值的笔画点（在相同笔设置下），压力值较大的点应产生较粗的笔迹。
        
        Feature: huawei-pdf-reader, Property 8: 压感笔迹粗细
        Validates: Requirements 3.6
        """
        # 确保 pressure2 > pressure1
        assume(pressure2 > pressure1)
        
        engine = AnnotationEngine()
        engine.set_pressure_sensitivity(True)
        
        # 计算两个压力值对应的宽度
        width1 = engine.calculate_stroke_width(base_width, pressure1)
        width2 = engine.calculate_stroke_width(base_width, pressure2)
        
        # 验证压力值较大的点产生较粗的笔迹
        assert width2 > width1

    @given(
        base_width=width_strategy,
        pressure=pressure_strategy,
    )
    @settings(max_examples=100)
    def test_pressure_sensitivity_disabled(
        self, 
        base_width: float, 
        pressure: float,
    ):
        """
        当压感禁用时，笔迹宽度应等于基础宽度
        
        Feature: huawei-pdf-reader, Property 8: 压感笔迹粗细
        Validates: Requirements 3.6
        """
        engine = AnnotationEngine()
        engine.set_pressure_sensitivity(False)
        
        # 计算宽度
        calculated_width = engine.calculate_stroke_width(base_width, pressure)
        
        # 验证宽度等于基础宽度
        assert calculated_width == base_width
