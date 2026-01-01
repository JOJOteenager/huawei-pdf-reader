"""
文件管理器属性测试

Feature: huawei-pdf-reader
Property 3: 文档搜索相关性
Property 4: 文档条目完整性
Property 22: 书签添加
Validates: Requirements 2.4, 2.6, 9.6

测试文件管理器的核心功能属性。
"""

import sys
import tempfile
from datetime import datetime
from pathlib import Path
import uuid

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

import fitz  # PyMuPDF
from hypothesis import given, settings, strategies as st, assume
import pytest

from huawei_pdf_reader.database import Database
from huawei_pdf_reader.file_manager import (
    FileManager,
    FileManagerError,
    DocumentNotFoundError,
)
from huawei_pdf_reader.models import DocumentEntry, Bookmark


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


def create_document_entry(
    db: Database,
    path: Path,
    title: str,
    thumbnail: bytes = None
) -> DocumentEntry:
    """创建并保存文档条目"""
    doc = DocumentEntry(
        id=str(uuid.uuid4()),
        path=path,
        title=title,
        file_type="pdf",
        size=path.stat().st_size if path.exists() else 1000,
        folder_id=None,
        thumbnail=thumbnail,
        created_at=datetime.now(),
        modified_at=datetime.now(),
        is_deleted=False,
        tags=[]
    )
    db.add_document(doc)
    return doc


# ============== 策略定义 ==============

# 有效关键词策略（非空字符串，不含特殊SQL字符）
valid_keyword_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=('L', 'N'),
        whitelist_characters=' _-'
    ),
    min_size=1,
    max_size=30
).filter(lambda x: x.strip())

# 有效标题策略
valid_title_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=('L', 'N'),
        whitelist_characters=' _-'
    ),
    min_size=1,
    max_size=50
).filter(lambda x: x.strip())

# 有效页码策略
valid_page_num_strategy = st.integers(min_value=1, max_value=1000)

# 书签标题策略
bookmark_title_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=('L', 'N', 'P'),
        whitelist_characters=' _-'
    ),
    min_size=1,
    max_size=100
).filter(lambda x: x.strip())


# ============== Property 3: 文档搜索相关性 ==============

class TestDocumentSearchRelevance:
    """
    Property 3: 文档搜索相关性
    
    For any 文档集合和搜索关键词，搜索结果中的每个文档的标题或路径
    应包含该关键词（不区分大小写）。
    
    Feature: huawei-pdf-reader, Property 3: 文档搜索相关性
    Validates: Requirements 2.4
    """

    @given(
        keyword=valid_keyword_strategy,
        num_matching=st.integers(min_value=1, max_value=5),
        num_non_matching=st.integers(min_value=0, max_value=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_search_results_contain_keyword(
        self, 
        keyword: str, 
        num_matching: int, 
        num_non_matching: int
    ):
        """
        Property 3: 搜索结果包含关键词
        
        For any 搜索关键词，搜索结果中的每个文档的标题或路径
        应包含该关键词（不区分大小写）。
        
        Feature: huawei-pdf-reader, Property 3: 文档搜索相关性
        Validates: Requirements 2.4
        """
        keyword = keyword.strip()
        assume(len(keyword) >= 1)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = temp_path / "test.db"
            db = Database(db_path)
            file_manager = FileManager(db)
            
            # 创建包含关键词的文档
            matching_docs = []
            for i in range(num_matching):
                pdf_path = temp_path / f"doc_{keyword}_{i}.pdf"
                create_valid_pdf(pdf_path)
                doc = create_document_entry(
                    db, pdf_path, 
                    title=f"Document with {keyword} number {i}"
                )
                matching_docs.append(doc)
            
            # 创建不包含关键词的文档
            for i in range(num_non_matching):
                pdf_path = temp_path / f"other_file_{i}.pdf"
                create_valid_pdf(pdf_path)
                create_document_entry(
                    db, pdf_path,
                    title=f"Unrelated document {i}"
                )
            
            # 执行搜索
            results = file_manager.search_documents(keyword)
            
            # 验证：所有搜索结果都应包含关键词
            keyword_lower = keyword.lower()
            for doc in results:
                title_contains = keyword_lower in doc.title.lower()
                path_contains = keyword_lower in str(doc.path).lower()
                
                assert title_contains or path_contains, \
                    f"Document '{doc.title}' (path: {doc.path}) does not contain keyword '{keyword}'"
            
            # 验证：所有匹配的文档都应在结果中
            result_ids = {doc.id for doc in results}
            for matching_doc in matching_docs:
                assert matching_doc.id in result_ids, \
                    f"Matching document '{matching_doc.title}' not found in search results"

    @given(keyword=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_search_case_insensitive(self, keyword: str):
        """
        Property 3: 搜索不区分大小写
        
        For any 关键词，使用大写、小写或混合大小写搜索应返回相同的结果。
        
        Feature: huawei-pdf-reader, Property 3: 文档搜索相关性
        Validates: Requirements 2.4
        """
        keyword = keyword.strip()
        assume(len(keyword) >= 1)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = temp_path / "test.db"
            db = Database(db_path)
            file_manager = FileManager(db)
            
            # 创建包含关键词的文档
            pdf_path = temp_path / f"doc_{keyword.lower()}.pdf"
            create_valid_pdf(pdf_path)
            create_document_entry(db, pdf_path, title=f"Document {keyword.lower()}")
            
            # 使用不同大小写搜索
            results_lower = file_manager.search_documents(keyword.lower())
            results_upper = file_manager.search_documents(keyword.upper())
            results_mixed = file_manager.search_documents(keyword.title())
            
            # 验证结果数量相同
            assert len(results_lower) == len(results_upper) == len(results_mixed), \
                "Search should be case-insensitive"

    def test_empty_keyword_returns_empty(self):
        """
        Property 3: 空关键词返回空结果
        
        搜索空字符串或只有空白的字符串应返回空列表。
        
        Feature: huawei-pdf-reader, Property 3: 文档搜索相关性
        Validates: Requirements 2.4
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = temp_path / "test.db"
            db = Database(db_path)
            file_manager = FileManager(db)
            
            # 创建一些文档
            pdf_path = temp_path / "test.pdf"
            create_valid_pdf(pdf_path)
            create_document_entry(db, pdf_path, title="Test Document")
            
            # 搜索空字符串
            assert file_manager.search_documents("") == []
            assert file_manager.search_documents("   ") == []


# ============== Property 4: 文档条目完整性 ==============

class TestDocumentEntryCompleteness:
    """
    Property 4: 文档条目完整性
    
    For any 文档条目，应包含非空的缩略图数据和有效的修改日期。
    
    Feature: huawei-pdf-reader, Property 4: 文档条目完整性
    Validates: Requirements 2.6
    """

    @given(
        title=valid_title_strategy,
        num_pages=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=None)
    def test_imported_document_has_thumbnail(self, title: str, num_pages: int):
        """
        Property 4: 导入的文档有缩略图
        
        For any 通过import_document导入的文档，应包含非空的缩略图数据。
        
        Feature: huawei-pdf-reader, Property 4: 文档条目完整性
        Validates: Requirements 2.6
        """
        title = title.strip()
        assume(len(title) >= 1)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = temp_path / "test.db"
            db = Database(db_path)
            file_manager = FileManager(db)
            
            # 创建PDF文件
            pdf_path = temp_path / f"{title}.pdf"
            create_valid_pdf(pdf_path, num_pages=num_pages)
            
            # 导入文档
            doc = file_manager.import_document(pdf_path)
            
            # 验证缩略图非空
            assert doc.thumbnail is not None, \
                "Imported document should have thumbnail"
            assert len(doc.thumbnail) > 0, \
                "Thumbnail should not be empty"
            
            # 验证缩略图是有效的PNG数据（PNG文件头）
            assert doc.thumbnail[:8] == b'\x89PNG\r\n\x1a\n', \
                "Thumbnail should be valid PNG data"

    @given(title=valid_title_strategy)
    @settings(max_examples=100, deadline=None)
    def test_document_has_valid_modified_date(self, title: str):
        """
        Property 4: 文档有有效的修改日期
        
        For any 文档条目，修改日期应是有效的datetime对象，
        且不早于创建日期。
        
        Feature: huawei-pdf-reader, Property 4: 文档条目完整性
        Validates: Requirements 2.6
        """
        title = title.strip()
        assume(len(title) >= 1)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = temp_path / "test.db"
            db = Database(db_path)
            file_manager = FileManager(db)
            
            # 创建并导入文档
            pdf_path = temp_path / f"{title}.pdf"
            create_valid_pdf(pdf_path)
            doc = file_manager.import_document(pdf_path)
            
            # 验证修改日期是有效的datetime
            assert isinstance(doc.modified_at, datetime), \
                "modified_at should be a datetime object"
            
            # 验证修改日期不早于创建日期
            assert doc.modified_at >= doc.created_at, \
                "modified_at should not be earlier than created_at"

    @given(title=valid_title_strategy)
    @settings(max_examples=100, deadline=None)
    def test_generated_thumbnail_is_valid(self, title: str):
        """
        Property 4: 生成的缩略图有效
        
        For any 有效的PDF文档，generate_thumbnail应返回有效的PNG图像数据。
        
        Feature: huawei-pdf-reader, Property 4: 文档条目完整性
        Validates: Requirements 2.6
        """
        title = title.strip()
        assume(len(title) >= 1)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = temp_path / "test.db"
            db = Database(db_path)
            file_manager = FileManager(db)
            
            # 创建PDF文件
            pdf_path = temp_path / f"{title}.pdf"
            create_valid_pdf(pdf_path)
            
            # 生成缩略图
            thumbnail = file_manager.generate_thumbnail(pdf_path)
            
            # 验证缩略图非空
            assert thumbnail is not None, \
                "Thumbnail should not be None"
            assert len(thumbnail) > 0, \
                "Thumbnail should not be empty"
            
            # 验证是有效的PNG数据
            assert thumbnail[:8] == b'\x89PNG\r\n\x1a\n', \
                "Thumbnail should be valid PNG data"


# ============== Property 22: 书签添加 ==============

class TestBookmarkAddition:
    """
    Property 22: 书签添加
    
    For any 页面位置和书签标题，添加书签后该书签应出现在文档的书签列表中。
    
    Feature: huawei-pdf-reader, Property 22: 书签添加
    Validates: Requirements 9.6
    """

    @given(
        page_num=valid_page_num_strategy,
        bookmark_title=bookmark_title_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_added_bookmark_appears_in_list(self, page_num: int, bookmark_title: str):
        """
        Property 22: 添加的书签出现在列表中
        
        For any 页码和书签标题，添加书签后该书签应出现在文档的书签列表中。
        
        Feature: huawei-pdf-reader, Property 22: 书签添加
        Validates: Requirements 9.6
        """
        bookmark_title = bookmark_title.strip()
        assume(len(bookmark_title) >= 1)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = temp_path / "test.db"
            db = Database(db_path)
            file_manager = FileManager(db)
            
            # 创建并导入文档
            pdf_path = temp_path / "test.pdf"
            create_valid_pdf(pdf_path)
            doc = file_manager.import_document(pdf_path)
            
            # 添加书签
            bookmark = file_manager.add_bookmark(doc.id, page_num, bookmark_title)
            
            # 验证书签属性
            assert bookmark.document_id == doc.id, \
                "Bookmark should be associated with the document"
            assert bookmark.page_num == page_num, \
                f"Bookmark page_num should be {page_num}"
            assert bookmark.title == bookmark_title, \
                f"Bookmark title should be '{bookmark_title}'"
            
            # 获取书签列表并验证
            bookmarks = file_manager.get_bookmarks(doc.id)
            bookmark_ids = [b.id for b in bookmarks]
            
            assert bookmark.id in bookmark_ids, \
                "Added bookmark should appear in bookmark list"

    @given(
        num_bookmarks=st.integers(min_value=1, max_value=10),
        page_nums=st.lists(
            st.integers(min_value=1, max_value=100),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_multiple_bookmarks_all_appear(self, num_bookmarks: int, page_nums: list):
        """
        Property 22: 多个书签都出现在列表中
        
        For any 多个书签，添加后所有书签都应出现在文档的书签列表中。
        
        Feature: huawei-pdf-reader, Property 22: 书签添加
        Validates: Requirements 9.6
        """
        # 确保有足够的页码
        page_nums = page_nums[:num_bookmarks]
        if len(page_nums) < num_bookmarks:
            page_nums.extend([1] * (num_bookmarks - len(page_nums)))
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = temp_path / "test.db"
            db = Database(db_path)
            file_manager = FileManager(db)
            
            # 创建并导入文档
            pdf_path = temp_path / "test.pdf"
            create_valid_pdf(pdf_path)
            doc = file_manager.import_document(pdf_path)
            
            # 添加多个书签
            added_bookmarks = []
            for i, page_num in enumerate(page_nums[:num_bookmarks]):
                bookmark = file_manager.add_bookmark(
                    doc.id, page_num, f"Bookmark {i}"
                )
                added_bookmarks.append(bookmark)
            
            # 获取书签列表
            bookmarks = file_manager.get_bookmarks(doc.id)
            bookmark_ids = {b.id for b in bookmarks}
            
            # 验证所有添加的书签都在列表中
            for added in added_bookmarks:
                assert added.id in bookmark_ids, \
                    f"Bookmark '{added.title}' should appear in bookmark list"

    @given(
        page_num=valid_page_num_strategy,
        bookmark_title=bookmark_title_strategy
    )
    @settings(max_examples=100, deadline=None)
    def test_bookmark_has_valid_created_at(self, page_num: int, bookmark_title: str):
        """
        Property 22: 书签有有效的创建时间
        
        For any 添加的书签，应有有效的创建时间。
        
        Feature: huawei-pdf-reader, Property 22: 书签添加
        Validates: Requirements 9.6
        """
        bookmark_title = bookmark_title.strip()
        assume(len(bookmark_title) >= 1)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = temp_path / "test.db"
            db = Database(db_path)
            file_manager = FileManager(db)
            
            # 创建并导入文档
            pdf_path = temp_path / "test.pdf"
            create_valid_pdf(pdf_path)
            doc = file_manager.import_document(pdf_path)
            
            # 记录添加前的时间
            before_add = datetime.now()
            
            # 添加书签
            bookmark = file_manager.add_bookmark(doc.id, page_num, bookmark_title)
            
            # 记录添加后的时间
            after_add = datetime.now()
            
            # 验证创建时间在合理范围内
            assert isinstance(bookmark.created_at, datetime), \
                "created_at should be a datetime object"
            assert before_add <= bookmark.created_at <= after_add, \
                "created_at should be within the expected time range"

    def test_bookmark_for_nonexistent_document_raises_error(self):
        """
        Property 22: 为不存在的文档添加书签应报错
        
        尝试为不存在的文档添加书签应抛出DocumentNotFoundError。
        
        Feature: huawei-pdf-reader, Property 22: 书签添加
        Validates: Requirements 9.6
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = temp_path / "test.db"
            db = Database(db_path)
            file_manager = FileManager(db)
            
            # 尝试为不存在的文档添加书签
            with pytest.raises(DocumentNotFoundError):
                file_manager.add_bookmark(
                    "nonexistent-doc-id",
                    1,
                    "Test Bookmark"
                )
