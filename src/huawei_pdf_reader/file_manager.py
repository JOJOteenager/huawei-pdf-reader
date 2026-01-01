"""
华为平板PDF阅读器 - 文件管理器

实现文档库管理、搜索、标签和缩略图功能。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import uuid
import os

import fitz  # PyMuPDF

from huawei_pdf_reader.database import Database
from huawei_pdf_reader.models import (
    Bookmark,
    DocumentEntry,
    Folder,
    Tag,
)


class FileManagerError(Exception):
    """文件管理器错误基类"""
    pass


class DocumentNotFoundError(FileManagerError):
    """文档不存在错误"""
    pass


class FolderNotFoundError(FileManagerError):
    """文件夹不存在错误"""
    pass


class TagNotFoundError(FileManagerError):
    """标签不存在错误"""
    pass


class IFileManager(ABC):
    """文件管理器接口"""
    
    @abstractmethod
    def get_documents(
        self, 
        folder_id: Optional[str] = None, 
        tag: Optional[str] = None
    ) -> List[DocumentEntry]:
        """获取文档列表"""
        pass
    
    @abstractmethod
    def search_documents(self, keyword: str) -> List[DocumentEntry]:
        """搜索文档"""
        pass
    
    @abstractmethod
    def create_folder(self, name: str, parent_id: Optional[str] = None) -> Folder:
        """创建文件夹"""
        pass
    
    @abstractmethod
    def delete_document(self, doc_id: str) -> None:
        """删除文档（移至回收站）"""
        pass
    
    @abstractmethod
    def add_tag(self, doc_id: str, tag: str) -> None:
        """添加标签"""
        pass
    
    @abstractmethod
    def remove_tag(self, doc_id: str, tag: str) -> None:
        """移除标签"""
        pass
    
    @abstractmethod
    def generate_thumbnail(self, doc_path: Path) -> bytes:
        """生成文档缩略图"""
        pass
    
    @abstractmethod
    def add_bookmark(self, doc_id: str, page_num: int, title: str) -> Bookmark:
        """添加书签"""
        pass
    
    @abstractmethod
    def get_bookmarks(self, doc_id: str) -> List[Bookmark]:
        """获取文档书签列表"""
        pass
    
    @abstractmethod
    def delete_bookmark(self, bookmark_id: str) -> None:
        """删除书签"""
        pass


class FileManager(IFileManager):
    """文件管理器实现"""
    
    # 缩略图默认尺寸
    THUMBNAIL_WIDTH = 150
    THUMBNAIL_HEIGHT = 200
    
    def __init__(self, db: Database):
        """
        初始化文件管理器
        
        Args:
            db: 数据库实例
        """
        self._db = db
    
    def get_documents(
        self, 
        folder_id: Optional[str] = None, 
        tag: Optional[str] = None
    ) -> List[DocumentEntry]:
        """
        获取文档列表
        
        Args:
            folder_id: 文件夹ID，为None时获取根目录文档
            tag: 标签名称，用于筛选带有指定标签的文档
            
        Returns:
            文档条目列表
        """
        if tag:
            # 按标签筛选
            tag_obj = self._db.get_tag_by_name(tag)
            if not tag_obj:
                return []
            docs = self._db.get_documents_by_tag(tag_obj.id)
            # 如果同时指定了folder_id，进一步筛选
            if folder_id is not None:
                docs = [d for d in docs if d.folder_id == folder_id]
            return docs
        else:
            return self._db.get_documents(folder_id=folder_id, include_deleted=False)
    
    def search_documents(self, keyword: str) -> List[DocumentEntry]:
        """
        搜索文档
        
        搜索文档标题和路径中包含关键词的文档（不区分大小写）
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的文档条目列表
        """
        if not keyword or not keyword.strip():
            return []
        return self._db.search_documents(keyword.strip())
    
    def create_folder(self, name: str, parent_id: Optional[str] = None) -> Folder:
        """
        创建文件夹
        
        Args:
            name: 文件夹名称
            parent_id: 父文件夹ID，为None时创建在根目录
            
        Returns:
            创建的文件夹对象
            
        Raises:
            FolderNotFoundError: 父文件夹不存在
        """
        if parent_id:
            parent = self._db.get_folder(parent_id)
            if not parent:
                raise FolderNotFoundError(f"父文件夹不存在: {parent_id}")
        
        folder = Folder(
            id=str(uuid.uuid4()),
            name=name,
            parent_id=parent_id,
            created_at=datetime.now()
        )
        self._db.add_folder(folder)
        return folder
    
    def delete_document(self, doc_id: str) -> None:
        """
        删除文档（移至回收站）
        
        Args:
            doc_id: 文档ID
            
        Raises:
            DocumentNotFoundError: 文档不存在
        """
        doc = self._db.get_document(doc_id)
        if not doc:
            raise DocumentNotFoundError(f"文档不存在: {doc_id}")
        
        # 软删除（移至回收站）
        self._db.delete_document(doc_id, permanent=False)
    
    def add_tag(self, doc_id: str, tag_name: str) -> None:
        """
        为文档添加标签
        
        如果标签不存在，会自动创建
        
        Args:
            doc_id: 文档ID
            tag_name: 标签名称
            
        Raises:
            DocumentNotFoundError: 文档不存在
        """
        doc = self._db.get_document(doc_id)
        if not doc:
            raise DocumentNotFoundError(f"文档不存在: {doc_id}")
        
        # 查找或创建标签
        tag = self._db.get_tag_by_name(tag_name)
        if not tag:
            tag = Tag(
                id=str(uuid.uuid4()),
                name=tag_name,
                color="#808080"
            )
            self._db.add_tag(tag)
        
        # 添加文档标签关联
        self._db.add_document_tag(doc_id, tag.id)
    
    def remove_tag(self, doc_id: str, tag_name: str) -> None:
        """
        移除文档标签
        
        Args:
            doc_id: 文档ID
            tag_name: 标签名称
            
        Raises:
            DocumentNotFoundError: 文档不存在
            TagNotFoundError: 标签不存在
        """
        doc = self._db.get_document(doc_id)
        if not doc:
            raise DocumentNotFoundError(f"文档不存在: {doc_id}")
        
        tag = self._db.get_tag_by_name(tag_name)
        if not tag:
            raise TagNotFoundError(f"标签不存在: {tag_name}")
        
        self._db.remove_document_tag(doc_id, tag.id)
    
    def generate_thumbnail(self, doc_path: Path) -> bytes:
        """
        生成文档缩略图
        
        从文档第一页生成缩略图
        
        Args:
            doc_path: 文档路径
            
        Returns:
            PNG格式的缩略图数据
            
        Raises:
            FileManagerError: 无法生成缩略图
        """
        suffix = doc_path.suffix.lower()
        
        if suffix == '.pdf':
            return self._generate_pdf_thumbnail(doc_path)
        elif suffix in ('.docx', '.doc'):
            return self._generate_word_thumbnail(doc_path)
        else:
            raise FileManagerError(f"不支持的文件格式: {suffix}")
    
    def _generate_pdf_thumbnail(self, pdf_path: Path) -> bytes:
        """生成PDF缩略图"""
        try:
            doc = fitz.open(str(pdf_path))
            if doc.page_count == 0:
                doc.close()
                raise FileManagerError("PDF文档没有页面")
            
            page = doc[0]  # 第一页
            
            # 计算缩放比例以适应缩略图尺寸
            rect = page.rect
            scale_x = self.THUMBNAIL_WIDTH / rect.width
            scale_y = self.THUMBNAIL_HEIGHT / rect.height
            scale = min(scale_x, scale_y)
            
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat)
            thumbnail_data = pix.tobytes("png")
            
            doc.close()
            return thumbnail_data
        except fitz.FileDataError as e:
            raise FileManagerError(f"无法打开PDF文件: {e}")
        except Exception as e:
            raise FileManagerError(f"生成缩略图失败: {e}")
    
    def _generate_word_thumbnail(self, word_path: Path) -> bytes:
        """生成Word文档缩略图"""
        from docx import Document as DocxDocument
        import tempfile
        
        try:
            # 打开Word文档
            docx_doc = DocxDocument(str(word_path))
            
            # 创建临时PDF
            temp_pdf = Path(tempfile.gettempdir()) / f"{word_path.stem}_thumb.pdf"
            
            # 转换为PDF（简化版本）
            pdf_doc = fitz.open()
            
            # 提取文本
            full_text = []
            for para in docx_doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text)
            
            # 创建第一页
            page = pdf_doc.new_page(width=595, height=842)
            
            if full_text:
                y_pos = 50
                for i, text in enumerate(full_text[:20]):  # 只取前20段
                    if y_pos > 750:
                        break
                    # 截断长文本
                    display_text = text[:80] + "..." if len(text) > 80 else text
                    page.insert_text(
                        (50, y_pos),
                        display_text,
                        fontsize=11,
                        fontname="helv"
                    )
                    y_pos += 18
            
            pdf_doc.save(str(temp_pdf))
            pdf_doc.close()
            
            # 从临时PDF生成缩略图
            thumbnail_data = self._generate_pdf_thumbnail(temp_pdf)
            
            # 删除临时文件
            try:
                os.remove(temp_pdf)
            except:
                pass
            
            return thumbnail_data
        except Exception as e:
            raise FileManagerError(f"生成Word缩略图失败: {e}")
    
    def add_bookmark(self, doc_id: str, page_num: int, title: str) -> Bookmark:
        """
        添加书签
        
        Args:
            doc_id: 文档ID
            page_num: 页码
            title: 书签标题
            
        Returns:
            创建的书签对象
            
        Raises:
            DocumentNotFoundError: 文档不存在
        """
        doc = self._db.get_document(doc_id)
        if not doc:
            raise DocumentNotFoundError(f"文档不存在: {doc_id}")
        
        bookmark = Bookmark(
            id=str(uuid.uuid4()),
            document_id=doc_id,
            page_num=page_num,
            title=title,
            created_at=datetime.now()
        )
        self._db.add_bookmark(bookmark)
        return bookmark
    
    def get_bookmarks(self, doc_id: str) -> List[Bookmark]:
        """
        获取文档书签列表
        
        Args:
            doc_id: 文档ID
            
        Returns:
            书签列表，按页码排序
        """
        return self._db.get_bookmarks(doc_id)
    
    def delete_bookmark(self, bookmark_id: str) -> None:
        """
        删除书签
        
        Args:
            bookmark_id: 书签ID
        """
        self._db.delete_bookmark(bookmark_id)
    
    # ============== 辅助方法 ==============
    
    def import_document(self, file_path: Path, folder_id: Optional[str] = None) -> DocumentEntry:
        """
        导入文档到文档库
        
        Args:
            file_path: 文档文件路径
            folder_id: 目标文件夹ID
            
        Returns:
            创建的文档条目
            
        Raises:
            FileManagerError: 导入失败
        """
        if not file_path.exists():
            raise FileManagerError(f"文件不存在: {file_path}")
        
        suffix = file_path.suffix.lower()
        if suffix not in ('.pdf', '.docx', '.doc'):
            raise FileManagerError(f"不支持的文件格式: {suffix}")
        
        # 生成缩略图
        try:
            thumbnail = self.generate_thumbnail(file_path)
        except:
            thumbnail = None
        
        # 确定文件类型
        file_type = "pdf" if suffix == ".pdf" else "docx"
        
        # 创建文档条目
        doc = DocumentEntry(
            id=str(uuid.uuid4()),
            path=file_path,
            title=file_path.stem,
            file_type=file_type,
            size=file_path.stat().st_size,
            folder_id=folder_id,
            thumbnail=thumbnail,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            is_deleted=False,
            tags=[]
        )
        
        self._db.add_document(doc)
        return doc
    
    def get_folders(self, parent_id: Optional[str] = None) -> List[Folder]:
        """
        获取文件夹列表
        
        Args:
            parent_id: 父文件夹ID，为None时获取根目录文件夹
            
        Returns:
            文件夹列表
        """
        return self._db.get_folders(parent_id)
    
    def delete_folder(self, folder_id: str) -> None:
        """
        删除文件夹
        
        文件夹内的文档和子文件夹会移到根目录
        
        Args:
            folder_id: 文件夹ID
            
        Raises:
            FolderNotFoundError: 文件夹不存在
        """
        folder = self._db.get_folder(folder_id)
        if not folder:
            raise FolderNotFoundError(f"文件夹不存在: {folder_id}")
        
        self._db.delete_folder(folder_id)
    
    def move_document(self, doc_id: str, folder_id: Optional[str]) -> None:
        """
        移动文档到指定文件夹
        
        Args:
            doc_id: 文档ID
            folder_id: 目标文件夹ID，为None时移到根目录
            
        Raises:
            DocumentNotFoundError: 文档不存在
            FolderNotFoundError: 目标文件夹不存在
        """
        doc = self._db.get_document(doc_id)
        if not doc:
            raise DocumentNotFoundError(f"文档不存在: {doc_id}")
        
        if folder_id:
            folder = self._db.get_folder(folder_id)
            if not folder:
                raise FolderNotFoundError(f"文件夹不存在: {folder_id}")
        
        doc.folder_id = folder_id
        self._db.update_document(doc)
    
    def rename_document(self, doc_id: str, new_title: str) -> None:
        """
        重命名文档
        
        Args:
            doc_id: 文档ID
            new_title: 新标题
            
        Raises:
            DocumentNotFoundError: 文档不存在
        """
        doc = self._db.get_document(doc_id)
        if not doc:
            raise DocumentNotFoundError(f"文档不存在: {doc_id}")
        
        doc.title = new_title
        self._db.update_document(doc)
    
    def get_deleted_documents(self) -> List[DocumentEntry]:
        """
        获取回收站中的文档
        
        Returns:
            已删除的文档列表
        """
        # 使用数据库的include_deleted参数获取所有文档，然后筛选已删除的
        all_docs = self._db.get_documents(folder_id=None, include_deleted=True)
        return [d for d in all_docs if d.is_deleted]
    
    def restore_document(self, doc_id: str) -> None:
        """
        从回收站恢复文档
        
        Args:
            doc_id: 文档ID
            
        Raises:
            DocumentNotFoundError: 文档不存在
        """
        doc = self._db.get_document(doc_id)
        if not doc:
            raise DocumentNotFoundError(f"文档不存在: {doc_id}")
        
        doc.is_deleted = False
        self._db.update_document(doc)
    
    def permanent_delete_document(self, doc_id: str) -> None:
        """
        永久删除文档
        
        Args:
            doc_id: 文档ID
            
        Raises:
            DocumentNotFoundError: 文档不存在
        """
        doc = self._db.get_document(doc_id)
        if not doc:
            raise DocumentNotFoundError(f"文档不存在: {doc_id}")
        
        self._db.delete_document(doc_id, permanent=True)
    
    def get_all_tags(self) -> List[Tag]:
        """
        获取所有标签
        
        Returns:
            标签列表
        """
        return self._db.get_all_tags()
