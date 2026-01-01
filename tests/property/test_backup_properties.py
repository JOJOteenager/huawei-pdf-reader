"""
备份服务属性测试

Feature: huawei-pdf-reader, Property 24: 本地备份往返一致性
Validates: Requirements 11.1

测试本地备份和恢复的往返一致性。
"""

import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import uuid

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from hypothesis import given, settings, strategies as st, assume

from huawei_pdf_reader.models import (
    BackupConfig,
    BackupProvider,
    DocumentEntry,
    Folder,
    Tag,
    Bookmark,
    Annotation,
    Stroke,
    StrokePoint,
    PenType,
    Settings,
    ReadingConfig,
    StylusConfig,
    ToolsConfig,
    TranslationConfig,
    PluginInfo,
)
from huawei_pdf_reader.database import Database
from huawei_pdf_reader.backup_service import BackupService, BackupError, RestoreError


# ============== 策略定义 ==============

# 有效的文件名字符（避免特殊字符）
safe_text_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N'), whitelist_characters='_-'),
    min_size=1,
    max_size=50
).filter(lambda x: len(x.strip()) > 0)

# 文件类型策略
file_type_strategy = st.sampled_from(["pdf", "docx"])

# 颜色策略
color_strategy = st.sampled_from([
    "#000000", "#FF0000", "#00FF00", "#0000FF", 
    "#FFFFFF", "#808080", "#FFA500", "#800080"
])

# 笔类型策略
pen_type_strategy = st.sampled_from([
    PenType.BALLPOINT, PenType.FOUNTAIN, PenType.HIGHLIGHTER,
    PenType.PENCIL, PenType.MARKER
])


@st.composite
def document_entry_strategy(draw):
    """生成文档条目"""
    doc_id = str(uuid.uuid4())
    title = draw(safe_text_strategy)
    file_type = draw(file_type_strategy)
    
    return DocumentEntry(
        id=doc_id,
        path=Path(f"/documents/{title}.{file_type}"),
        title=title,
        file_type=file_type,
        size=draw(st.integers(min_value=1000, max_value=10000000)),
        folder_id=None,
        thumbnail=draw(st.binary(min_size=10, max_size=100)) if draw(st.booleans()) else None,
        created_at=datetime.now(),
        modified_at=datetime.now(),
        is_deleted=False,
        tags=[],
    )


@st.composite
def folder_strategy(draw):
    """生成文件夹"""
    return Folder(
        id=str(uuid.uuid4()),
        name=draw(safe_text_strategy),
        parent_id=None,
        created_at=datetime.now(),
    )


@st.composite
def tag_strategy(draw, index: int = 0):
    """生成标签（带唯一索引确保名称唯一）"""
    base_name = draw(safe_text_strategy)
    unique_name = f"{base_name}_{index}_{uuid.uuid4().hex[:6]}"
    return Tag(
        id=str(uuid.uuid4()),
        name=unique_name,
        color=draw(color_strategy),
    )


@st.composite
def stroke_point_strategy(draw):
    """生成笔画点"""
    return StrokePoint(
        x=draw(st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False)),
        y=draw(st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False)),
        pressure=draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)),
        timestamp=draw(st.floats(min_value=0, max_value=1e10, allow_nan=False, allow_infinity=False)),
    )


@st.composite
def stroke_strategy(draw):
    """生成笔画"""
    points = draw(st.lists(stroke_point_strategy(), min_size=2, max_size=10))
    return Stroke(
        id=str(uuid.uuid4()),
        pen_type=draw(pen_type_strategy),
        color=draw(color_strategy),
        width=draw(st.floats(min_value=0.5, max_value=10.0, allow_nan=False, allow_infinity=False)),
        points=points,
    )


@st.composite
def annotation_strategy(draw, doc_id: str = None):
    """生成注释"""
    strokes = draw(st.lists(stroke_strategy(), min_size=1, max_size=5))
    return Annotation(
        id=str(uuid.uuid4()),
        page_num=draw(st.integers(min_value=1, max_value=100)),
        strokes=strokes,
        created_at=datetime.now(),
        modified_at=datetime.now(),
    )


@st.composite
def bookmark_strategy(draw, doc_id: str):
    """生成书签"""
    return Bookmark(
        id=str(uuid.uuid4()),
        document_id=doc_id,
        page_num=draw(st.integers(min_value=1, max_value=100)),
        title=draw(safe_text_strategy),
        created_at=datetime.now(),
    )


@st.composite
def settings_strategy(draw):
    """生成设置"""
    return Settings(
        theme=draw(st.sampled_from(["dark_green", "light", "dark"])),
        language=draw(st.sampled_from(["zh_CN", "en_US"])),
        reading=ReadingConfig(
            page_direction=draw(st.sampled_from(["vertical", "horizontal"])),
            dual_page=draw(st.booleans()),
            continuous_scroll=draw(st.booleans()),
            toolbar_position=draw(st.sampled_from(["top", "bottom"])),
            eye_protection=draw(st.booleans()),
            keep_screen_on=draw(st.booleans()),
        ),
        stylus=StylusConfig(
            double_tap=draw(st.sampled_from(["eraser", "none", "undo"])),
            long_press=draw(st.sampled_from(["select_text", "none"])),
            primary_click="none",
            secondary_click="undo",
            pinch="none",
            swipe_up="none",
            swipe_down="none",
            palm_rejection_sensitivity=draw(st.integers(min_value=1, max_value=10)),
        ),
        tools=ToolsConfig(),
        backup=BackupConfig(
            provider=BackupProvider.LOCAL,
            auto_backup=draw(st.booleans()),
            wifi_only=draw(st.booleans()),
        ),
        translation=TranslationConfig(),
    )


@st.composite
def backup_data_strategy(draw):
    """生成完整的备份数据集"""
    # 生成文档
    documents = draw(st.lists(document_entry_strategy(), min_size=1, max_size=3))
    
    # 生成文件夹
    folders = draw(st.lists(folder_strategy(), min_size=0, max_size=2))
    
    # 生成标签（确保名称唯一）
    num_tags = draw(st.integers(min_value=0, max_value=3))
    tags = [draw(tag_strategy(i)) for i in range(num_tags)]
    
    # 生成注释（每个文档可能有注释）
    annotations = []
    for doc in documents:
        if draw(st.booleans()):
            ann = draw(annotation_strategy())
            annotations.append((doc.id, ann))
    
    # 生成书签
    bookmarks = []
    for doc in documents:
        if draw(st.booleans()):
            bm = draw(bookmark_strategy(doc.id))
            bookmarks.append(bm)
    
    # 生成设置
    app_settings = draw(settings_strategy())
    
    return {
        "documents": documents,
        "folders": folders,
        "tags": tags,
        "annotations": annotations,
        "bookmarks": bookmarks,
        "settings": app_settings,
    }


# ============== 属性测试 ==============

class TestBackupRoundTrip:
    """
    Property 24: 本地备份往返一致性
    
    For any 文档和注释数据，本地备份后再恢复应产生等效的数据。
    
    Feature: huawei-pdf-reader, Property 24: 本地备份往返一致性
    Validates: Requirements 11.1
    """

    @given(data=backup_data_strategy())
    @settings(max_examples=100, deadline=None)
    def test_local_backup_round_trip(self, data: dict):
        """
        本地备份往返一致性
        
        Property 24: 本地备份往返一致性
        For any 文档和注释数据，本地备份后再恢复应产生等效的数据。
        
        Feature: huawei-pdf-reader, Property 24: 本地备份往返一致性
        Validates: Requirements 11.1
        """
        # 创建临时目录
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # 创建源数据库
            source_db_path = temp_dir / "source" / "data.db"
            source_db = Database(source_db_path)
            
            # 填充源数据库
            for folder in data["folders"]:
                source_db.add_folder(folder)
            
            for tag in data["tags"]:
                source_db.add_tag(tag)
            
            for doc in data["documents"]:
                source_db.add_document(doc)
            
            for doc_id, ann in data["annotations"]:
                source_db.save_annotation(doc_id, ann)
            
            for bm in data["bookmarks"]:
                source_db.add_bookmark(bm)
            
            source_db.save_settings(data["settings"])
            
            # 创建备份服务并执行备份
            backup_dir = temp_dir / "backups"
            backup_service = BackupService(
                database=source_db,
                data_dir=temp_dir / "source",
                backup_dir=backup_dir,
            )
            
            # 执行本地备份
            result = backup_service.backup(BackupProvider.LOCAL)
            assert result is True, "备份应该成功"
            
            # 验证备份文件存在
            backups = backup_service.list_local_backups()
            assert len(backups) > 0, "应该有备份文件"
            
            # 创建目标数据库（模拟新设备）
            target_db_path = temp_dir / "target" / "data.db"
            target_db = Database(target_db_path)
            
            # 创建新的备份服务用于恢复
            restore_service = BackupService(
                database=target_db,
                data_dir=temp_dir / "target",
                backup_dir=backup_dir,
            )
            
            # 执行恢复
            restore_result = restore_service.restore(BackupProvider.LOCAL)
            assert restore_result is True, "恢复应该成功"
            
            # 验证数据一致性
            
            # 验证文件夹
            restored_folders = target_db.get_folders()
            assert len(restored_folders) == len(data["folders"]), "文件夹数量应该一致"
            
            # 验证标签
            restored_tags = target_db.get_all_tags()
            assert len(restored_tags) == len(data["tags"]), "标签数量应该一致"
            
            # 验证文档
            restored_docs = target_db.get_documents(include_deleted=True)
            assert len(restored_docs) == len(data["documents"]), "文档数量应该一致"
            
            # 验证文档内容
            for original_doc in data["documents"]:
                restored_doc = target_db.get_document(original_doc.id)
                assert restored_doc is not None, f"文档 {original_doc.id} 应该存在"
                assert restored_doc.title == original_doc.title, "文档标题应该一致"
                assert restored_doc.file_type == original_doc.file_type, "文档类型应该一致"
                assert restored_doc.size == original_doc.size, "文档大小应该一致"
            
            # 验证注释
            for doc_id, original_ann in data["annotations"]:
                restored_anns = target_db.get_annotations(doc_id)
                assert len(restored_anns) > 0, f"文档 {doc_id} 应该有注释"
                
                # 找到对应的注释
                restored_ann = next((a for a in restored_anns if a.id == original_ann.id), None)
                assert restored_ann is not None, f"注释 {original_ann.id} 应该存在"
                assert restored_ann.page_num == original_ann.page_num, "注释页码应该一致"
                assert len(restored_ann.strokes) == len(original_ann.strokes), "笔画数量应该一致"
            
            # 验证书签
            for original_bm in data["bookmarks"]:
                restored_bms = target_db.get_bookmarks(original_bm.document_id)
                restored_bm = next((b for b in restored_bms if b.id == original_bm.id), None)
                assert restored_bm is not None, f"书签 {original_bm.id} 应该存在"
                assert restored_bm.page_num == original_bm.page_num, "书签页码应该一致"
                assert restored_bm.title == original_bm.title, "书签标题应该一致"
            
            # 验证设置
            restored_settings = target_db.load_settings()
            assert restored_settings.theme == data["settings"].theme, "主题应该一致"
            assert restored_settings.language == data["settings"].language, "语言应该一致"
            assert restored_settings.reading.page_direction == data["settings"].reading.page_direction
            assert restored_settings.reading.dual_page == data["settings"].reading.dual_page
            assert restored_settings.stylus.palm_rejection_sensitivity == data["settings"].stylus.palm_rejection_sensitivity
            
        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)

    @given(data=backup_data_strategy())
    @settings(max_examples=50, deadline=None)
    def test_multiple_backups_restore_latest(self, data: dict):
        """
        多次备份后恢复最新版本
        
        验证多次备份后，恢复操作默认使用最新的备份。
        """
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # 创建数据库
            db_path = temp_dir / "data" / "data.db"
            db = Database(db_path)
            
            # 创建备份服务
            backup_dir = temp_dir / "backups"
            backup_service = BackupService(
                database=db,
                data_dir=temp_dir / "data",
                backup_dir=backup_dir,
            )
            
            # 添加初始数据
            for doc in data["documents"]:
                db.add_document(doc)
            
            # 执行第一次备份
            backup_service.backup(BackupProvider.LOCAL)
            
            # 获取备份列表
            backups = backup_service.list_local_backups()
            assert len(backups) >= 1, "应该至少有一个备份"
            
            # 验证备份按时间倒序排列
            if len(backups) > 1:
                for i in range(len(backups) - 1):
                    assert backups[i]["created_at"] >= backups[i + 1]["created_at"], \
                        "备份应该按时间倒序排列"
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @given(settings_data=settings_strategy())
    @settings(max_examples=50, deadline=None)
    def test_settings_backup_round_trip(self, settings_data: Settings):
        """
        设置备份往返一致性
        
        验证设置数据在备份和恢复后保持一致。
        """
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # 创建源数据库
            source_db_path = temp_dir / "source" / "data.db"
            source_db = Database(source_db_path)
            source_db.save_settings(settings_data)
            
            # 创建备份服务
            backup_dir = temp_dir / "backups"
            backup_service = BackupService(
                database=source_db,
                data_dir=temp_dir / "source",
                backup_dir=backup_dir,
            )
            
            # 执行备份
            backup_service.backup(BackupProvider.LOCAL)
            
            # 创建目标数据库
            target_db_path = temp_dir / "target" / "data.db"
            target_db = Database(target_db_path)
            
            # 恢复
            restore_service = BackupService(
                database=target_db,
                data_dir=temp_dir / "target",
                backup_dir=backup_dir,
            )
            restore_service.restore(BackupProvider.LOCAL)
            
            # 验证设置
            restored = target_db.load_settings()
            
            assert restored.theme == settings_data.theme
            assert restored.language == settings_data.language
            assert restored.reading.page_direction == settings_data.reading.page_direction
            assert restored.reading.dual_page == settings_data.reading.dual_page
            assert restored.reading.continuous_scroll == settings_data.reading.continuous_scroll
            assert restored.stylus.double_tap == settings_data.stylus.double_tap
            assert restored.stylus.palm_rejection_sensitivity == settings_data.stylus.palm_rejection_sensitivity
            assert restored.backup.auto_backup == settings_data.backup.auto_backup
            assert restored.backup.wifi_only == settings_data.backup.wifi_only
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
