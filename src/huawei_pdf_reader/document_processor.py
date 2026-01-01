"""
华为平板PDF阅读器 - 文档处理器

实现PDF和Word文档的加载、解析和渲染功能。
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple
import tempfile
import os

import fitz  # PyMuPDF

from huawei_pdf_reader.models import DocumentInfo, PageInfo


class DocumentError(Exception):
    """文档处理错误基类"""
    pass


class FileNotFoundError(DocumentError):
    """文件不存在错误"""
    pass


class UnsupportedFormatError(DocumentError):
    """不支持的文件格式错误"""
    pass


class CorruptedFileError(DocumentError):
    """文件损坏错误"""
    pass


class IDocumentRenderer(ABC):
    """文档渲染器接口"""
    
    @abstractmethod
    def open(self, path: Path) -> DocumentInfo:
        """打开文档"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """关闭文档"""
        pass
    
    @abstractmethod
    def render_page(self, page_num: int, scale: float = 1.0) -> bytes:
        """渲染指定页面，返回图像数据"""
        pass
    
    @abstractmethod
    def get_page_info(self, page_num: int) -> PageInfo:
        """获取页面信息"""
        pass
    
    @abstractmethod
    def extract_text(self, page_num: int, rect: Optional[Tuple[float, float, float, float]] = None) -> str:
        """提取页面文本，可指定区域"""
        pass
    
    @abstractmethod
    def rotate_page(self, page_num: int, angle: int) -> None:
        """旋转页面"""
        pass
    
    @abstractmethod
    def delete_page(self, page_num: int) -> None:
        """删除页面"""
        pass
    
    @abstractmethod
    def export_page_as_image(self, page_num: int, output_path: Path) -> None:
        """导出页面为图片"""
        pass
    
    @property
    @abstractmethod
    def is_open(self) -> bool:
        """检查文档是否已打开"""
        pass
    
    @property
    @abstractmethod
    def document_info(self) -> Optional[DocumentInfo]:
        """获取当前文档信息"""
        pass


class PDFRenderer(IDocumentRenderer):
    """PDF渲染器实现"""
    
    def __init__(self):
        self._doc = None
        self._path: Optional[Path] = None
        self._document_info: Optional[DocumentInfo] = None
    
    def open(self, path: Path) -> DocumentInfo:
        """打开PDF文档"""
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")
        
        if path.suffix.lower() != '.pdf':
            raise UnsupportedFormatError(f"不支持的文件格式: {path.suffix}")
        
        try:
            self._doc = fitz.open(str(path))
        except Exception as e:
            raise CorruptedFileError(f"文件已损坏，无法打开: {e}")
        
        if self._doc.page_count == 0:
            self._doc.close()
            self._doc = None
            raise CorruptedFileError("PDF文档没有页面")
        
        self._path = path
        self._document_info = DocumentInfo(
            path=path,
            title=self._doc.metadata.get("title", "") or path.stem,
            total_pages=self._doc.page_count,
            file_type="pdf"
        )
        
        return self._document_info
    
    def close(self) -> None:
        """关闭文档"""
        if self._doc:
            self._doc.close()
            self._doc = None
        self._path = None
        self._document_info = None
    
    def render_page(self, page_num: int, scale: float = 1.0) -> bytes:
        """渲染指定页面，返回PNG图像数据"""
        if not self._doc:
            raise DocumentError("文档未打开")
        
        if page_num < 1 or page_num > self._doc.page_count:
            raise DocumentError(f"页码超出范围: {page_num}")
        
        page = self._doc[page_num - 1]  # PyMuPDF使用0索引
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat)
        return pix.tobytes("png")
    
    def get_page_info(self, page_num: int) -> PageInfo:
        """获取页面信息"""
        if not self._doc:
            raise DocumentError("文档未打开")
        
        if page_num < 1 or page_num > self._doc.page_count:
            raise DocumentError(f"页码超出范围: {page_num}")
        
        page = self._doc[page_num - 1]
        rect = page.rect
        
        return PageInfo(
            page_number=page_num,
            width=rect.width,
            height=rect.height,
            rotation=page.rotation
        )
    
    def extract_text(self, page_num: int, rect: Optional[Tuple[float, float, float, float]] = None) -> str:
        """提取页面文本"""
        if not self._doc:
            raise DocumentError("文档未打开")
        
        if page_num < 1 or page_num > self._doc.page_count:
            raise DocumentError(f"页码超出范围: {page_num}")
        
        page = self._doc[page_num - 1]
        
        if rect:
            clip = fitz.Rect(rect)
            return page.get_text("text", clip=clip)
        else:
            return page.get_text("text")
    
    def rotate_page(self, page_num: int, angle: int) -> None:
        """旋转页面（90、180、270度）"""
        if not self._doc:
            raise DocumentError("文档未打开")
        
        if page_num < 1 or page_num > self._doc.page_count:
            raise DocumentError(f"页码超出范围: {page_num}")
        
        if angle not in (90, 180, 270):
            raise DocumentError(f"无效的旋转角度: {angle}，只支持90、180、270度")
        
        page = self._doc[page_num - 1]
        current_rotation = page.rotation
        new_rotation = (current_rotation + angle) % 360
        page.set_rotation(new_rotation)
    
    def delete_page(self, page_num: int) -> None:
        """删除页面"""
        if not self._doc:
            raise DocumentError("文档未打开")
        
        if page_num < 1 or page_num > self._doc.page_count:
            raise DocumentError(f"页码超出范围: {page_num}")
        
        if self._doc.page_count <= 1:
            raise DocumentError("无法删除最后一页")
        
        self._doc.delete_page(page_num - 1)
        
        # 更新文档信息
        if self._document_info:
            self._document_info = DocumentInfo(
                path=self._document_info.path,
                title=self._document_info.title,
                total_pages=self._doc.page_count,
                file_type=self._document_info.file_type
            )
    
    def export_page_as_image(self, page_num: int, output_path: Path) -> None:
        """导出页面为图片"""
        if not self._doc:
            raise DocumentError("文档未打开")
        
        if page_num < 1 or page_num > self._doc.page_count:
            raise DocumentError(f"页码超出范围: {page_num}")
        
        page = self._doc[page_num - 1]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x缩放以获得更好的质量
        pix.save(str(output_path))
    
    def save(self, output_path: Optional[Path] = None) -> None:
        """保存文档"""
        if not self._doc:
            raise DocumentError("文档未打开")
        
        save_path = output_path or self._path
        if not save_path:
            raise DocumentError("未指定保存路径")
        
        self._doc.save(str(save_path))
    
    @property
    def is_open(self) -> bool:
        """检查文档是否已打开"""
        return self._doc is not None
    
    @property
    def document_info(self) -> Optional[DocumentInfo]:
        """获取当前文档信息"""
        return self._document_info
    
    @property
    def total_pages(self) -> int:
        """获取总页数"""
        if not self._doc:
            return 0
        return self._doc.page_count



class WordRenderer(IDocumentRenderer):
    """Word文档渲染器实现（转换为PDF后渲染）"""
    
    def __init__(self):
        self._pdf_renderer = PDFRenderer()
        self._temp_pdf_path: Optional[Path] = None
        self._original_path: Optional[Path] = None
        self._document_info: Optional[DocumentInfo] = None
    
    def open(self, path: Path) -> DocumentInfo:
        """打开Word文档（转换为PDF后渲染）"""
        from docx import Document as DocxDocument
        from docx.opc.exceptions import PackageNotFoundError
        
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")
        
        suffix = path.suffix.lower()
        if suffix not in ('.docx', '.doc'):
            raise UnsupportedFormatError(f"不支持的文件格式: {suffix}")
        
        # 尝试打开Word文档验证其有效性
        try:
            docx_doc = DocxDocument(str(path))
        except PackageNotFoundError:
            raise CorruptedFileError(f"文件已损坏，无法打开: {path}")
        except Exception as e:
            raise CorruptedFileError(f"文件已损坏，无法打开: {e}")
        
        self._original_path = path
        
        # 创建临时PDF文件
        temp_dir = tempfile.gettempdir()
        self._temp_pdf_path = Path(temp_dir) / f"{path.stem}_temp.pdf"
        
        # 将Word转换为PDF
        self._convert_docx_to_pdf(docx_doc, self._temp_pdf_path)
        
        # 使用PDF渲染器打开转换后的PDF
        pdf_info = self._pdf_renderer.open(self._temp_pdf_path)
        
        # 创建文档信息（使用原始Word文件信息）
        self._document_info = DocumentInfo(
            path=path,
            title=path.stem,
            total_pages=pdf_info.total_pages,
            file_type="docx"
        )
        
        return self._document_info
    
    def _convert_docx_to_pdf(self, docx_doc, output_path: Path) -> None:
        """将Word文档转换为PDF"""
        # 创建新的PDF文档
        pdf_doc = fitz.open()
        
        # 提取Word文档内容并创建PDF页面
        full_text = []
        for para in docx_doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)
        
        # 如果没有内容，添加一个空白页
        if not full_text:
            page = pdf_doc.new_page(width=595, height=842)  # A4尺寸
        else:
            # 将文本分页（简单实现：每页约40行）
            lines_per_page = 40
            all_lines = []
            for text in full_text:
                # 简单的换行处理
                words = text.split()
                current_line = ""
                for word in words:
                    if len(current_line) + len(word) + 1 <= 80:  # 每行约80字符
                        current_line = current_line + " " + word if current_line else word
                    else:
                        if current_line:
                            all_lines.append(current_line)
                        current_line = word
                if current_line:
                    all_lines.append(current_line)
                all_lines.append("")  # 段落间空行
            
            # 创建页面
            for i in range(0, max(1, len(all_lines)), lines_per_page):
                page = pdf_doc.new_page(width=595, height=842)  # A4尺寸
                page_lines = all_lines[i:i + lines_per_page]
                
                # 在页面上插入文本
                y_pos = 50
                for line in page_lines:
                    if line:
                        page.insert_text(
                            (50, y_pos),
                            line,
                            fontsize=11,
                            fontname="helv"
                        )
                    y_pos += 18
        
        # 保存PDF
        pdf_doc.save(str(output_path))
        pdf_doc.close()
    
    def close(self) -> None:
        """关闭文档"""
        self._pdf_renderer.close()
        
        # 删除临时PDF文件
        if self._temp_pdf_path and self._temp_pdf_path.exists():
            try:
                os.remove(self._temp_pdf_path)
            except:
                pass
        
        self._temp_pdf_path = None
        self._original_path = None
        self._document_info = None
    
    def render_page(self, page_num: int, scale: float = 1.0) -> bytes:
        """渲染指定页面"""
        return self._pdf_renderer.render_page(page_num, scale)
    
    def get_page_info(self, page_num: int) -> PageInfo:
        """获取页面信息"""
        return self._pdf_renderer.get_page_info(page_num)
    
    def extract_text(self, page_num: int, rect: Optional[Tuple[float, float, float, float]] = None) -> str:
        """提取页面文本"""
        return self._pdf_renderer.extract_text(page_num, rect)
    
    def rotate_page(self, page_num: int, angle: int) -> None:
        """旋转页面"""
        self._pdf_renderer.rotate_page(page_num, angle)
    
    def delete_page(self, page_num: int) -> None:
        """删除页面"""
        self._pdf_renderer.delete_page(page_num)
        
        # 更新文档信息
        if self._document_info:
            self._document_info = DocumentInfo(
                path=self._document_info.path,
                title=self._document_info.title,
                total_pages=self._pdf_renderer.total_pages,
                file_type=self._document_info.file_type
            )
    
    def export_page_as_image(self, page_num: int, output_path: Path) -> None:
        """导出页面为图片"""
        self._pdf_renderer.export_page_as_image(page_num, output_path)
    
    @property
    def is_open(self) -> bool:
        """检查文档是否已打开"""
        return self._pdf_renderer.is_open
    
    @property
    def document_info(self) -> Optional[DocumentInfo]:
        """获取当前文档信息"""
        return self._document_info


def create_renderer(path: Path) -> IDocumentRenderer:
    """根据文件类型创建合适的渲染器"""
    suffix = path.suffix.lower()
    
    if suffix == '.pdf':
        return PDFRenderer()
    elif suffix in ('.docx', '.doc'):
        return WordRenderer()
    else:
        raise UnsupportedFormatError(f"不支持的文件格式: {suffix}")
