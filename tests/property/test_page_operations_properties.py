"""
页面操作属性测试

Feature: huawei-pdf-reader
Property 19: 页面旋转
Property 20: 页面删除
Property 21: 页面跳转
Validates: Requirements 9.3, 9.4, 9.5

测试文档页面操作的核心功能属性。
"""

import sys
import tempfile
from pathlib import Path

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

import fitz  # PyMuPDF
from hypothesis import given, settings, strategies as st, assume
import pytest

from huawei_pdf_reader.document_processor import (
    PDFRenderer,
    DocumentError,
)
from huawei_pdf_reader.models import PageInfo


# ============== 辅助函数 ==============

def create_valid_pdf(path: Path, num_pages: int = 1, title: str = "") -> None:
    """创建有效的PDF文件用于测试"""
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page(width=595, height=842)  # A4尺寸
        page.insert_text((50, 50), f"Page {i + 1}", fontsize=12)
    
    if title:
        doc.set_metadata({"title": title})
    
    doc.save(str(path))
    doc.close()


# ============== 策略定义 ==============

# 有效页数策略 (2-10页，用于删除测试需要至少2页)
multi_page_count_strategy = st.integers(min_value=2, max_value=10)

# 单页或多页策略
page_count_strategy = st.integers(min_value=1, max_value=10)

# 旋转角度策略
rotation_angle_strategy = st.sampled_from([90, 180, 270])


# ============== Property 19: 页面旋转 ==============

class TestPageRotation:
    """
    Property 19: 页面旋转
    
    For any 页面和旋转角度（90、180、270），旋转后页面的rotation属性应更新为新角度。
    
    Feature: huawei-pdf-reader, Property 19: 页面旋转
    Validates: Requirements 9.3
    """

    @given(
        num_pages=page_count_strategy,
        angle=rotation_angle_strategy
    )
    @settings(max_examples=100)
    def test_page_rotation_updates_rotation(self, num_pages: int, angle: int):
        """
        Property 19: 页面旋转更新rotation属性
        
        For any 页面和旋转角度（90、180、270），旋转后页面的rotation属性
        应更新为新角度（累加到当前旋转角度）。
        
        Feature: huawei-pdf-reader, Property 19: 页面旋转
        Validates: Requirements 9.3
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "test.pdf"
            create_valid_pdf(pdf_path, num_pages=num_pages)
            
            renderer = PDFRenderer()
            try:
                renderer.open(pdf_path)
                
                # 选择一个有效的页码
                page_num = 1
                
                # 获取旋转前的rotation
                page_info_before = renderer.get_page_info(page_num)
                rotation_before = page_info_before.rotation
                
                # 执行旋转
                renderer.rotate_page(page_num, angle)
                
                # 获取旋转后的rotation
                page_info_after = renderer.get_page_info(page_num)
                rotation_after = page_info_after.rotation
                
                # 验证旋转后的角度正确（累加并取模360）
                expected_rotation = (rotation_before + angle) % 360
                assert rotation_after == expected_rotation, \
                    f"Expected rotation {expected_rotation}, got {rotation_after}"
                
            finally:
                renderer.close()

    @given(
        num_pages=page_count_strategy,
        page_idx=st.integers(min_value=0, max_value=9)
    )
    @settings(max_examples=100)
    def test_page_rotation_on_specific_page(self, num_pages: int, page_idx: int):
        """
        Property 19: 特定页面旋转
        
        For any 多页文档中的特定页面，旋转该页面不应影响其他页面的rotation。
        
        Feature: huawei-pdf-reader, Property 19: 页面旋转
        Validates: Requirements 9.3
        """
        # 确保页码在有效范围内
        assume(page_idx < num_pages)
        page_num = page_idx + 1  # 转换为1索引
        
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "test.pdf"
            create_valid_pdf(pdf_path, num_pages=num_pages)
            
            renderer = PDFRenderer()
            try:
                renderer.open(pdf_path)
                
                # 记录所有页面的初始rotation
                initial_rotations = {}
                for i in range(1, num_pages + 1):
                    initial_rotations[i] = renderer.get_page_info(i).rotation
                
                # 旋转指定页面
                renderer.rotate_page(page_num, 90)
                
                # 验证只有指定页面的rotation改变
                for i in range(1, num_pages + 1):
                    current_rotation = renderer.get_page_info(i).rotation
                    if i == page_num:
                        expected = (initial_rotations[i] + 90) % 360
                        assert current_rotation == expected, \
                            f"Page {i} rotation should be {expected}, got {current_rotation}"
                    else:
                        assert current_rotation == initial_rotations[i], \
                            f"Page {i} rotation should not change, was {initial_rotations[i]}, now {current_rotation}"
                
            finally:
                renderer.close()


# ============== Property 20: 页面删除 ==============

class TestPageDeletion:
    """
    Property 20: 页面删除
    
    For any 多页文档，删除一页后文档总页数应减少1。
    
    Feature: huawei-pdf-reader, Property 20: 页面删除
    Validates: Requirements 9.4
    """

    @given(
        num_pages=multi_page_count_strategy,
        page_idx=st.integers(min_value=0, max_value=9)
    )
    @settings(max_examples=100)
    def test_page_deletion_reduces_count(self, num_pages: int, page_idx: int):
        """
        Property 20: 删除页面减少总页数
        
        For any 多页文档，删除一页后文档总页数应减少1。
        
        Feature: huawei-pdf-reader, Property 20: 页面删除
        Validates: Requirements 9.4
        """
        # 确保页码在有效范围内
        assume(page_idx < num_pages)
        page_num = page_idx + 1  # 转换为1索引
        
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "test.pdf"
            create_valid_pdf(pdf_path, num_pages=num_pages)
            
            renderer = PDFRenderer()
            try:
                doc_info = renderer.open(pdf_path)
                initial_pages = doc_info.total_pages
                
                # 删除页面
                renderer.delete_page(page_num)
                
                # 验证总页数减少1
                assert renderer.total_pages == initial_pages - 1, \
                    f"Expected {initial_pages - 1} pages, got {renderer.total_pages}"
                
                # 验证document_info也更新了
                assert renderer.document_info.total_pages == initial_pages - 1, \
                    f"document_info.total_pages should be {initial_pages - 1}"
                
            finally:
                renderer.close()

    def test_cannot_delete_last_page(self):
        """
        Property 20: 无法删除最后一页
        
        For any 单页文档，尝试删除唯一的页面应抛出错误。
        
        Feature: huawei-pdf-reader, Property 20: 页面删除
        Validates: Requirements 9.4
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "test.pdf"
            create_valid_pdf(pdf_path, num_pages=1)
            
            renderer = PDFRenderer()
            try:
                renderer.open(pdf_path)
                
                # 尝试删除唯一的页面应该失败
                with pytest.raises(DocumentError):
                    renderer.delete_page(1)
                
            finally:
                renderer.close()

    @given(num_pages=multi_page_count_strategy)
    @settings(max_examples=100)
    def test_delete_all_but_one_page(self, num_pages: int):
        """
        Property 20: 连续删除页面直到只剩一页
        
        For any 多页文档，可以连续删除页面直到只剩一页。
        
        Feature: huawei-pdf-reader, Property 20: 页面删除
        Validates: Requirements 9.4
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "test.pdf"
            create_valid_pdf(pdf_path, num_pages=num_pages)
            
            renderer = PDFRenderer()
            try:
                renderer.open(pdf_path)
                
                # 删除页面直到只剩一页
                while renderer.total_pages > 1:
                    current_pages = renderer.total_pages
                    renderer.delete_page(1)  # 总是删除第一页
                    assert renderer.total_pages == current_pages - 1
                
                # 验证最终只剩一页
                assert renderer.total_pages == 1
                
            finally:
                renderer.close()


# ============== Property 21: 页面跳转 ==============

class TestPageNavigation:
    """
    Property 21: 页面跳转
    
    For any 有效的页码（1到总页数），跳转后当前页码应等于目标页码。
    
    Feature: huawei-pdf-reader, Property 21: 页面跳转
    Validates: Requirements 9.5
    """

    @given(
        num_pages=page_count_strategy,
        target_page_idx=st.integers(min_value=0, max_value=9)
    )
    @settings(max_examples=100)
    def test_page_info_for_valid_page(self, num_pages: int, target_page_idx: int):
        """
        Property 21: 获取有效页面信息
        
        For any 有效的页码（1到总页数），get_page_info应返回正确的页面信息，
        包含正确的页码。
        
        Feature: huawei-pdf-reader, Property 21: 页面跳转
        Validates: Requirements 9.5
        """
        # 确保目标页码在有效范围内
        assume(target_page_idx < num_pages)
        target_page = target_page_idx + 1  # 转换为1索引
        
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "test.pdf"
            create_valid_pdf(pdf_path, num_pages=num_pages)
            
            renderer = PDFRenderer()
            try:
                renderer.open(pdf_path)
                
                # 获取目标页面信息
                page_info = renderer.get_page_info(target_page)
                
                # 验证页码正确
                assert page_info.page_number == target_page, \
                    f"Expected page_number {target_page}, got {page_info.page_number}"
                
                # 验证页面尺寸有效
                assert page_info.width > 0, "Page width should be positive"
                assert page_info.height > 0, "Page height should be positive"
                
            finally:
                renderer.close()

    @given(
        num_pages=page_count_strategy,
        invalid_offset=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=100)
    def test_invalid_page_number_error(self, num_pages: int, invalid_offset: int):
        """
        Property 21: 无效页码错误处理
        
        For any 超出范围的页码，get_page_info应抛出错误。
        
        Feature: huawei-pdf-reader, Property 21: 页面跳转
        Validates: Requirements 9.5
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "test.pdf"
            create_valid_pdf(pdf_path, num_pages=num_pages)
            
            renderer = PDFRenderer()
            try:
                renderer.open(pdf_path)
                
                # 尝试访问超出范围的页码
                invalid_page = num_pages + invalid_offset
                
                with pytest.raises(DocumentError):
                    renderer.get_page_info(invalid_page)
                
            finally:
                renderer.close()

    @given(num_pages=page_count_strategy)
    @settings(max_examples=100)
    def test_zero_page_number_error(self, num_pages: int):
        """
        Property 21: 页码0错误处理
        
        For any 文档，页码0应该是无效的。
        
        Feature: huawei-pdf-reader, Property 21: 页面跳转
        Validates: Requirements 9.5
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "test.pdf"
            create_valid_pdf(pdf_path, num_pages=num_pages)
            
            renderer = PDFRenderer()
            try:
                renderer.open(pdf_path)
                
                # 页码0应该无效
                with pytest.raises(DocumentError):
                    renderer.get_page_info(0)
                
            finally:
                renderer.close()

    @given(num_pages=page_count_strategy)
    @settings(max_examples=100)
    def test_render_all_pages(self, num_pages: int):
        """
        Property 21: 渲染所有页面
        
        For any 文档，应该能够渲染从1到总页数的所有页面。
        
        Feature: huawei-pdf-reader, Property 21: 页面跳转
        Validates: Requirements 9.5
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "test.pdf"
            create_valid_pdf(pdf_path, num_pages=num_pages)
            
            renderer = PDFRenderer()
            try:
                renderer.open(pdf_path)
                
                # 渲染所有页面
                for page_num in range(1, num_pages + 1):
                    image_data = renderer.render_page(page_num)
                    
                    # 验证返回的是有效的图像数据
                    assert isinstance(image_data, bytes), \
                        f"Expected bytes, got {type(image_data)}"
                    assert len(image_data) > 0, \
                        f"Page {page_num} rendered empty image"
                    
                    # 验证是PNG格式（PNG文件头）
                    assert image_data[:8] == b'\x89PNG\r\n\x1a\n', \
                        f"Page {page_num} is not valid PNG"
                
            finally:
                renderer.close()
