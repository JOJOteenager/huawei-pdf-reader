"""
华为平板PDF阅读器 - 注释引擎

处理手写笔输入和注释管理。
"""

import math
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .models import Annotation, PenType, Stroke, StrokePoint


class IAnnotationEngine(ABC):
    """注释引擎接口"""

    @abstractmethod
    def start_stroke(self, pen_type: PenType, color: str, width: float) -> str:
        """开始新笔画，返回笔画ID"""
        pass

    @abstractmethod
    def add_point(self, stroke_id: str, x: float, y: float, pressure: float) -> None:
        """添加笔画点"""
        pass

    @abstractmethod
    def end_stroke(self, stroke_id: str) -> Stroke:
        """结束笔画"""
        pass

    @abstractmethod
    def erase_at(self, page_num: int, x: float, y: float, radius: float) -> List[str]:
        """擦除指定位置的笔画，返回被删除的笔画ID列表"""
        pass

    @abstractmethod
    def get_annotations(self, page_num: int) -> List[Annotation]:
        """获取页面注释"""
        pass

    @abstractmethod
    def save_annotations(self, doc_id: str) -> None:
        """保存注释"""
        pass

    @abstractmethod
    def load_annotations(self, doc_id: str) -> None:
        """加载注释"""
        pass

    @abstractmethod
    def shape_recognition(self, stroke: Stroke) -> Optional[Stroke]:
        """一笔成型：识别并转换为标准图形"""
        pass


class AnnotationEngine(IAnnotationEngine):
    """注释引擎实现"""

    # 压感笔迹粗细系数
    MIN_PRESSURE_MULTIPLIER = 0.5
    MAX_PRESSURE_MULTIPLIER = 1.5

    def __init__(self, database=None):
        """
        初始化注释引擎
        
        Args:
            database: 数据库实例，用于持久化注释
        """
        self._database = database
        # 当前正在绘制的笔画 {stroke_id: Stroke}
        self._active_strokes: Dict[str, Stroke] = {}
        # 页面注释 {page_num: {annotation_id: Annotation}}
        self._annotations: Dict[int, Dict[str, Annotation]] = {}
        # 当前文档ID
        self._current_doc_id: Optional[str] = None
        # 压感启用状态
        self._pressure_sensitivity_enabled: bool = True

    def set_pressure_sensitivity(self, enabled: bool) -> None:
        """设置是否启用压感"""
        self._pressure_sensitivity_enabled = enabled

    def start_stroke(self, pen_type: PenType, color: str, width: float) -> str:
        """
        开始新笔画
        
        Args:
            pen_type: 笔类型
            color: 颜色（十六进制）
            width: 基础宽度
            
        Returns:
            笔画ID
        """
        stroke_id = str(uuid.uuid4())
        stroke = Stroke(
            id=stroke_id,
            pen_type=pen_type,
            color=color,
            width=width,
            points=[]
        )
        self._active_strokes[stroke_id] = stroke
        return stroke_id

    def add_point(self, stroke_id: str, x: float, y: float, pressure: float) -> None:
        """
        添加笔画点
        
        Args:
            stroke_id: 笔画ID
            x: X坐标
            y: Y坐标
            pressure: 压力值 (0.0 - 1.0)
        """
        if stroke_id not in self._active_strokes:
            raise ValueError(f"Stroke {stroke_id} not found")
        
        # 确保压力值在有效范围内
        pressure = max(0.0, min(1.0, pressure))
        
        point = StrokePoint(
            x=x,
            y=y,
            pressure=pressure,
            timestamp=time.time()
        )
        self._active_strokes[stroke_id].points.append(point)

    def end_stroke(self, stroke_id: str) -> Stroke:
        """
        结束笔画
        
        Args:
            stroke_id: 笔画ID
            
        Returns:
            完成的笔画对象
        """
        if stroke_id not in self._active_strokes:
            raise ValueError(f"Stroke {stroke_id} not found")
        
        stroke = self._active_strokes.pop(stroke_id)
        return stroke

    def add_stroke_to_page(self, page_num: int, stroke: Stroke) -> str:
        """
        将笔画添加到页面注释
        
        Args:
            page_num: 页码
            stroke: 笔画对象
            
        Returns:
            注释ID
        """
        if page_num not in self._annotations:
            self._annotations[page_num] = {}
        
        # 创建或获取页面的默认注释
        annotation_id = f"annotation_{page_num}"
        if annotation_id not in self._annotations[page_num]:
            self._annotations[page_num][annotation_id] = Annotation(
                id=annotation_id,
                page_num=page_num,
                strokes=[],
                created_at=datetime.now(),
                modified_at=datetime.now()
            )
        
        annotation = self._annotations[page_num][annotation_id]
        annotation.strokes.append(stroke)
        annotation.modified_at = datetime.now()
        
        return annotation_id

    def erase_at(self, page_num: int, x: float, y: float, radius: float) -> List[str]:
        """
        擦除指定位置的笔画
        
        Args:
            page_num: 页码
            x: X坐标
            y: Y坐标
            radius: 擦除半径
            
        Returns:
            被删除的笔画ID列表
        """
        erased_stroke_ids = []
        
        if page_num not in self._annotations:
            return erased_stroke_ids
        
        for annotation in self._annotations[page_num].values():
            strokes_to_remove = []
            
            for stroke in annotation.strokes:
                # 检查笔画是否与擦除区域相交
                if self._stroke_intersects_circle(stroke, x, y, radius):
                    strokes_to_remove.append(stroke)
                    erased_stroke_ids.append(stroke.id)
            
            # 移除相交的笔画
            for stroke in strokes_to_remove:
                annotation.strokes.remove(stroke)
            
            if strokes_to_remove:
                annotation.modified_at = datetime.now()
        
        return erased_stroke_ids

    def _stroke_intersects_circle(self, stroke: Stroke, cx: float, cy: float, radius: float) -> bool:
        """
        检查笔画是否与圆形区域相交
        
        Args:
            stroke: 笔画
            cx: 圆心X坐标
            cy: 圆心Y坐标
            radius: 半径
            
        Returns:
            是否相交
        """
        for point in stroke.points:
            distance = math.sqrt((point.x - cx) ** 2 + (point.y - cy) ** 2)
            if distance <= radius:
                return True
        return False

    def get_annotations(self, page_num: int) -> List[Annotation]:
        """
        获取页面注释
        
        Args:
            page_num: 页码
            
        Returns:
            注释列表
        """
        if page_num not in self._annotations:
            return []
        return list(self._annotations[page_num].values())

    def get_all_annotations(self) -> Dict[int, List[Annotation]]:
        """
        获取所有页面的注释
        
        Returns:
            {page_num: [Annotation, ...]}
        """
        return {
            page_num: list(annotations.values())
            for page_num, annotations in self._annotations.items()
        }

    def clear_annotations(self, page_num: Optional[int] = None) -> None:
        """
        清除注释
        
        Args:
            page_num: 页码，如果为None则清除所有页面
        """
        if page_num is None:
            self._annotations.clear()
        elif page_num in self._annotations:
            del self._annotations[page_num]


    def calculate_stroke_width(self, base_width: float, pressure: float) -> float:
        """
        根据压力值计算笔迹粗细
        
        Args:
            base_width: 基础宽度
            pressure: 压力值 (0.0 - 1.0)
            
        Returns:
            计算后的宽度
        """
        if not self._pressure_sensitivity_enabled:
            return base_width
        
        # 压力值映射到 [MIN_PRESSURE_MULTIPLIER, MAX_PRESSURE_MULTIPLIER]
        multiplier = self.MIN_PRESSURE_MULTIPLIER + \
            pressure * (self.MAX_PRESSURE_MULTIPLIER - self.MIN_PRESSURE_MULTIPLIER)
        
        return base_width * multiplier

    def save_annotations(self, doc_id: str) -> None:
        """
        保存注释到数据库
        
        Args:
            doc_id: 文档ID
        """
        self._current_doc_id = doc_id
        
        if self._database is None:
            return
        
        # 将所有注释保存到数据库
        for page_num, annotations in self._annotations.items():
            for annotation in annotations.values():
                self._database.save_annotation(doc_id, annotation)

    def load_annotations(self, doc_id: str) -> None:
        """
        从数据库加载注释
        
        Args:
            doc_id: 文档ID
        """
        self._current_doc_id = doc_id
        self._annotations.clear()
        
        if self._database is None:
            return
        
        # 从数据库加载注释
        annotations = self._database.load_annotations(doc_id)
        for annotation in annotations:
            page_num = annotation.page_num
            if page_num not in self._annotations:
                self._annotations[page_num] = {}
            self._annotations[page_num][annotation.id] = annotation

    def shape_recognition(self, stroke: Stroke) -> Optional[Stroke]:
        """
        一笔成型：识别并转换为标准图形
        
        支持识别：直线、矩形、圆形、三角形
        
        Args:
            stroke: 原始笔画
            
        Returns:
            转换后的标准图形笔画，如果无法识别则返回None
        """
        if len(stroke.points) < 3:
            return None
        
        # 获取笔画的边界框
        points = stroke.points
        xs = [p.x for p in points]
        ys = [p.y for p in points]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        width = max_x - min_x
        height = max_y - min_y
        
        # 检查是否为直线
        if self._is_line(points):
            return self._create_line_stroke(stroke, points[0], points[-1])
        
        # 检查是否为闭合图形
        start = points[0]
        end = points[-1]
        distance = math.sqrt((end.x - start.x) ** 2 + (end.y - start.y) ** 2)
        diagonal = math.sqrt(width ** 2 + height ** 2)
        
        # 如果起点和终点足够接近，认为是闭合图形
        if diagonal > 0 and distance / diagonal < 0.15:
            # 检查是否为圆形
            if self._is_circle(points, min_x, min_y, width, height):
                return self._create_circle_stroke(stroke, min_x, min_y, width, height)
            
            # 检查是否为矩形
            if self._is_rectangle(points, min_x, min_y, width, height):
                return self._create_rectangle_stroke(stroke, min_x, min_y, width, height)
            
            # 检查是否为三角形
            if self._is_triangle(points):
                return self._create_triangle_stroke(stroke, points)
        
        return None

    def _is_line(self, points: List[StrokePoint]) -> bool:
        """检查点集是否构成直线"""
        if len(points) < 2:
            return False
        
        start = points[0]
        end = points[-1]
        
        # 计算直线长度
        line_length = math.sqrt((end.x - start.x) ** 2 + (end.y - start.y) ** 2)
        if line_length < 10:  # 太短不算直线
            return False
        
        # 计算所有点到直线的最大距离
        max_deviation = 0
        for point in points[1:-1]:
            deviation = self._point_to_line_distance(point, start, end)
            max_deviation = max(max_deviation, deviation)
        
        # 如果最大偏差小于线长的10%，认为是直线
        return max_deviation / line_length < 0.1

    def _point_to_line_distance(self, point: StrokePoint, 
                                 line_start: StrokePoint, 
                                 line_end: StrokePoint) -> float:
        """计算点到直线的距离"""
        # 使用向量叉积计算点到直线距离
        dx = line_end.x - line_start.x
        dy = line_end.y - line_start.y
        
        line_length = math.sqrt(dx ** 2 + dy ** 2)
        if line_length == 0:
            return math.sqrt((point.x - line_start.x) ** 2 + (point.y - line_start.y) ** 2)
        
        # 叉积 / 线长 = 点到直线距离
        cross = abs((point.x - line_start.x) * dy - (point.y - line_start.y) * dx)
        return cross / line_length

    def _is_circle(self, points: List[StrokePoint], 
                   min_x: float, min_y: float, 
                   width: float, height: float) -> bool:
        """检查点集是否构成圆形"""
        if width == 0 or height == 0:
            return False
        
        # 宽高比接近1
        aspect_ratio = width / height if height > 0 else 0
        if not (0.7 < aspect_ratio < 1.4):
            return False
        
        # 计算中心和半径
        center_x = min_x + width / 2
        center_y = min_y + height / 2
        radius = (width + height) / 4
        
        # 检查所有点到中心的距离是否接近半径
        deviations = []
        for point in points:
            dist = math.sqrt((point.x - center_x) ** 2 + (point.y - center_y) ** 2)
            deviations.append(abs(dist - radius))
        
        avg_deviation = sum(deviations) / len(deviations)
        return avg_deviation / radius < 0.2

    def _is_rectangle(self, points: List[StrokePoint],
                      min_x: float, min_y: float,
                      width: float, height: float) -> bool:
        """检查点集是否构成矩形"""
        if width < 10 or height < 10:
            return False
        
        # 检查点是否主要分布在边界框的边上
        edge_points = 0
        threshold = min(width, height) * 0.15
        
        for point in points:
            # 检查是否在四条边附近
            near_left = abs(point.x - min_x) < threshold
            near_right = abs(point.x - (min_x + width)) < threshold
            near_top = abs(point.y - min_y) < threshold
            near_bottom = abs(point.y - (min_y + height)) < threshold
            
            if near_left or near_right or near_top or near_bottom:
                edge_points += 1
        
        return edge_points / len(points) > 0.7

    def _is_triangle(self, points: List[StrokePoint]) -> bool:
        """检查点集是否构成三角形"""
        if len(points) < 10:
            return False
        
        # 找到三个角点（方向变化最大的点）
        corners = self._find_corners(points, 3)
        
        if len(corners) != 3:
            return False
        
        # 检查三个角点是否形成有效三角形
        # 计算三角形面积，如果面积太小则不是有效三角形
        area = self._triangle_area(corners[0], corners[1], corners[2])
        
        # 计算边界框面积
        xs = [p.x for p in points]
        ys = [p.y for p in points]
        bbox_area = (max(xs) - min(xs)) * (max(ys) - min(ys))
        
        # 三角形面积应该接近边界框面积的一半
        if bbox_area > 0:
            return 0.3 < area / bbox_area < 0.7
        
        return False

    def _find_corners(self, points: List[StrokePoint], num_corners: int) -> List[StrokePoint]:
        """找到笔画中的角点"""
        if len(points) < num_corners:
            return []
        
        # 计算每个点的方向变化
        angles = []
        for i in range(1, len(points) - 1):
            prev = points[i - 1]
            curr = points[i]
            next_p = points[i + 1]
            
            # 计算两个向量的夹角
            v1 = (curr.x - prev.x, curr.y - prev.y)
            v2 = (next_p.x - curr.x, next_p.y - curr.y)
            
            angle = self._angle_between_vectors(v1, v2)
            angles.append((i, angle))
        
        # 按角度变化排序，取最大的几个
        angles.sort(key=lambda x: x[1], reverse=True)
        
        corner_indices = [a[0] for a in angles[:num_corners]]
        corner_indices.sort()
        
        return [points[i] for i in corner_indices]

    def _angle_between_vectors(self, v1: Tuple[float, float], v2: Tuple[float, float]) -> float:
        """计算两个向量之间的夹角"""
        len1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
        len2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)
        
        if len1 == 0 or len2 == 0:
            return 0
        
        dot = v1[0] * v2[0] + v1[1] * v2[1]
        cos_angle = dot / (len1 * len2)
        cos_angle = max(-1, min(1, cos_angle))  # 防止浮点误差
        
        return math.acos(cos_angle)

    def _triangle_area(self, p1: StrokePoint, p2: StrokePoint, p3: StrokePoint) -> float:
        """计算三角形面积"""
        return abs((p2.x - p1.x) * (p3.y - p1.y) - (p3.x - p1.x) * (p2.y - p1.y)) / 2

    def _create_line_stroke(self, original: Stroke, 
                            start: StrokePoint, 
                            end: StrokePoint) -> Stroke:
        """创建直线笔画"""
        avg_pressure = (start.pressure + end.pressure) / 2
        
        new_points = [
            StrokePoint(x=start.x, y=start.y, pressure=avg_pressure, timestamp=time.time()),
            StrokePoint(x=end.x, y=end.y, pressure=avg_pressure, timestamp=time.time())
        ]
        
        return Stroke(
            id=str(uuid.uuid4()),
            pen_type=original.pen_type,
            color=original.color,
            width=original.width,
            points=new_points
        )

    def _create_circle_stroke(self, original: Stroke,
                              min_x: float, min_y: float,
                              width: float, height: float) -> Stroke:
        """创建圆形笔画"""
        center_x = min_x + width / 2
        center_y = min_y + height / 2
        radius = (width + height) / 4
        
        # 生成圆形点
        num_points = 36
        new_points = []
        avg_pressure = sum(p.pressure for p in original.points) / len(original.points)
        
        for i in range(num_points + 1):
            angle = 2 * math.pi * i / num_points
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            new_points.append(StrokePoint(x=x, y=y, pressure=avg_pressure, timestamp=time.time()))
        
        return Stroke(
            id=str(uuid.uuid4()),
            pen_type=original.pen_type,
            color=original.color,
            width=original.width,
            points=new_points
        )

    def _create_rectangle_stroke(self, original: Stroke,
                                  min_x: float, min_y: float,
                                  width: float, height: float) -> Stroke:
        """创建矩形笔画"""
        avg_pressure = sum(p.pressure for p in original.points) / len(original.points)
        
        # 四个角点
        corners = [
            (min_x, min_y),
            (min_x + width, min_y),
            (min_x + width, min_y + height),
            (min_x, min_y + height),
            (min_x, min_y)  # 闭合
        ]
        
        new_points = [
            StrokePoint(x=x, y=y, pressure=avg_pressure, timestamp=time.time())
            for x, y in corners
        ]
        
        return Stroke(
            id=str(uuid.uuid4()),
            pen_type=original.pen_type,
            color=original.color,
            width=original.width,
            points=new_points
        )

    def _create_triangle_stroke(self, original: Stroke, 
                                 points: List[StrokePoint]) -> Stroke:
        """创建三角形笔画"""
        corners = self._find_corners(points, 3)
        if len(corners) != 3:
            return None
        
        avg_pressure = sum(p.pressure for p in original.points) / len(original.points)
        
        # 三个角点加闭合点
        new_points = [
            StrokePoint(x=corners[0].x, y=corners[0].y, pressure=avg_pressure, timestamp=time.time()),
            StrokePoint(x=corners[1].x, y=corners[1].y, pressure=avg_pressure, timestamp=time.time()),
            StrokePoint(x=corners[2].x, y=corners[2].y, pressure=avg_pressure, timestamp=time.time()),
            StrokePoint(x=corners[0].x, y=corners[0].y, pressure=avg_pressure, timestamp=time.time())  # 闭合
        ]
        
        return Stroke(
            id=str(uuid.uuid4()),
            pen_type=original.pen_type,
            color=original.color,
            width=original.width,
            points=new_points
        )
