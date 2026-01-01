"""
华为平板PDF阅读器 - 数据库层

SQLite数据库操作类，负责数据持久化。
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, List, Optional
import uuid

from huawei_pdf_reader.models import (
    Annotation,
    Bookmark,
    DocumentEntry,
    Folder,
    PluginInfo,
    Settings,
    Tag,
)


# SQLite数据库Schema
SCHEMA = """
-- 文档表
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    title TEXT NOT NULL,
    file_type TEXT NOT NULL,
    size INTEGER NOT NULL,
    folder_id TEXT,
    thumbnail BLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted INTEGER DEFAULT 0,
    FOREIGN KEY (folder_id) REFERENCES folders(id)
);

-- 文件夹表
CREATE TABLE IF NOT EXISTS folders (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    parent_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES folders(id)
);

-- 标签表
CREATE TABLE IF NOT EXISTS tags (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    color TEXT DEFAULT '#808080'
);

-- 文档标签关联表
CREATE TABLE IF NOT EXISTS document_tags (
    document_id TEXT NOT NULL,
    tag_id TEXT NOT NULL,
    PRIMARY KEY (document_id, tag_id),
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (tag_id) REFERENCES tags(id)
);

-- 注释表
CREATE TABLE IF NOT EXISTS annotations (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    page_num INTEGER NOT NULL,
    data BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- 书签表
CREATE TABLE IF NOT EXISTS bookmarks (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    page_num INTEGER NOT NULL,
    title TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- 插件表
CREATE TABLE IF NOT EXISTS plugins (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    author TEXT,
    description TEXT,
    entry_point TEXT NOT NULL,
    permissions TEXT,
    enabled INTEGER DEFAULT 0,
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 设置表
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_documents_folder ON documents(folder_id);
CREATE INDEX IF NOT EXISTS idx_documents_deleted ON documents(is_deleted);
CREATE INDEX IF NOT EXISTS idx_annotations_document ON annotations(document_id);
CREATE INDEX IF NOT EXISTS idx_bookmarks_document ON bookmarks(document_id);
"""


class Database:
    """数据库操作类"""

    def __init__(self, db_path: Path):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self) -> None:
        """确保数据库和表存在"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_connection() as conn:
            conn.executescript(SCHEMA)
            conn.commit()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()


    # ============== 文档操作 ==============

    def add_document(self, doc: DocumentEntry) -> str:
        """添加文档"""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO documents (id, path, title, file_type, size, folder_id, 
                                       thumbnail, created_at, modified_at, is_deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc.id,
                    str(doc.path),
                    doc.title,
                    doc.file_type,
                    doc.size,
                    doc.folder_id,
                    doc.thumbnail,
                    doc.created_at.isoformat(),
                    doc.modified_at.isoformat(),
                    1 if doc.is_deleted else 0,
                ),
            )
            conn.commit()
        return doc.id

    def get_document(self, doc_id: str) -> Optional[DocumentEntry]:
        """获取文档"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE id = ?", (doc_id,)
            ).fetchone()
            if row:
                return self._row_to_document(row)
        return None

    def get_documents(
        self,
        folder_id: Optional[str] = None,
        include_deleted: bool = False,
    ) -> List[DocumentEntry]:
        """获取文档列表"""
        with self._get_connection() as conn:
            if folder_id:
                query = "SELECT * FROM documents WHERE folder_id = ?"
                params = [folder_id]
            else:
                query = "SELECT * FROM documents WHERE folder_id IS NULL"
                params = []

            if not include_deleted:
                query += " AND is_deleted = 0"

            rows = conn.execute(query, params).fetchall()
            docs = [self._row_to_document(row) for row in rows]

            # 加载标签
            for doc in docs:
                doc.tags = self._get_document_tags(conn, doc.id)

            return docs

    def search_documents(self, keyword: str) -> List[DocumentEntry]:
        """搜索文档"""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM documents 
                WHERE (title LIKE ? OR path LIKE ?) AND is_deleted = 0
                """,
                (f"%{keyword}%", f"%{keyword}%"),
            ).fetchall()
            docs = [self._row_to_document(row) for row in rows]

            for doc in docs:
                doc.tags = self._get_document_tags(conn, doc.id)

            return docs

    def update_document(self, doc: DocumentEntry) -> None:
        """更新文档"""
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE documents 
                SET path = ?, title = ?, file_type = ?, size = ?, folder_id = ?,
                    thumbnail = ?, modified_at = ?, is_deleted = ?
                WHERE id = ?
                """,
                (
                    str(doc.path),
                    doc.title,
                    doc.file_type,
                    doc.size,
                    doc.folder_id,
                    doc.thumbnail,
                    datetime.now().isoformat(),
                    1 if doc.is_deleted else 0,
                    doc.id,
                ),
            )
            conn.commit()

    def delete_document(self, doc_id: str, permanent: bool = False) -> None:
        """删除文档"""
        with self._get_connection() as conn:
            if permanent:
                conn.execute("DELETE FROM document_tags WHERE document_id = ?", (doc_id,))
                conn.execute("DELETE FROM annotations WHERE document_id = ?", (doc_id,))
                conn.execute("DELETE FROM bookmarks WHERE document_id = ?", (doc_id,))
                conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            else:
                conn.execute(
                    "UPDATE documents SET is_deleted = 1, modified_at = ? WHERE id = ?",
                    (datetime.now().isoformat(), doc_id),
                )
            conn.commit()

    def _row_to_document(self, row: sqlite3.Row) -> DocumentEntry:
        """将数据库行转换为DocumentEntry"""
        return DocumentEntry(
            id=row["id"],
            path=Path(row["path"]),
            title=row["title"],
            file_type=row["file_type"],
            size=row["size"],
            folder_id=row["folder_id"],
            thumbnail=row["thumbnail"],
            created_at=datetime.fromisoformat(row["created_at"]),
            modified_at=datetime.fromisoformat(row["modified_at"]),
            is_deleted=bool(row["is_deleted"]),
        )

    def _get_document_tags(self, conn: sqlite3.Connection, doc_id: str) -> List[str]:
        """获取文档的标签名称列表"""
        rows = conn.execute(
            """
            SELECT t.name FROM tags t
            JOIN document_tags dt ON t.id = dt.tag_id
            WHERE dt.document_id = ?
            """,
            (doc_id,),
        ).fetchall()
        return [row["name"] for row in rows]


    # ============== 文件夹操作 ==============

    def add_folder(self, folder: Folder) -> str:
        """添加文件夹"""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO folders (id, name, parent_id, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (folder.id, folder.name, folder.parent_id, folder.created_at.isoformat()),
            )
            conn.commit()
        return folder.id

    def get_folder(self, folder_id: str) -> Optional[Folder]:
        """获取文件夹"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM folders WHERE id = ?", (folder_id,)
            ).fetchone()
            if row:
                return Folder(
                    id=row["id"],
                    name=row["name"],
                    parent_id=row["parent_id"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
        return None

    def get_folders(self, parent_id: Optional[str] = None) -> List[Folder]:
        """获取文件夹列表"""
        with self._get_connection() as conn:
            if parent_id:
                rows = conn.execute(
                    "SELECT * FROM folders WHERE parent_id = ?", (parent_id,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM folders WHERE parent_id IS NULL"
                ).fetchall()
            return [
                Folder(
                    id=row["id"],
                    name=row["name"],
                    parent_id=row["parent_id"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                for row in rows
            ]

    def delete_folder(self, folder_id: str) -> None:
        """删除文件夹"""
        with self._get_connection() as conn:
            # 将文件夹内的文档移到根目录
            conn.execute(
                "UPDATE documents SET folder_id = NULL WHERE folder_id = ?",
                (folder_id,),
            )
            # 将子文件夹移到根目录
            conn.execute(
                "UPDATE folders SET parent_id = NULL WHERE parent_id = ?",
                (folder_id,),
            )
            # 删除文件夹
            conn.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
            conn.commit()

    # ============== 标签操作 ==============

    def add_tag(self, tag: Tag) -> str:
        """添加标签"""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO tags (id, name, color) VALUES (?, ?, ?)",
                (tag.id, tag.name, tag.color),
            )
            conn.commit()
        return tag.id

    def get_tag(self, tag_id: str) -> Optional[Tag]:
        """获取标签"""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM tags WHERE id = ?", (tag_id,)).fetchone()
            if row:
                return Tag(id=row["id"], name=row["name"], color=row["color"])
        return None

    def get_tag_by_name(self, name: str) -> Optional[Tag]:
        """根据名称获取标签"""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM tags WHERE name = ?", (name,)).fetchone()
            if row:
                return Tag(id=row["id"], name=row["name"], color=row["color"])
        return None

    def get_all_tags(self) -> List[Tag]:
        """获取所有标签"""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM tags").fetchall()
            return [Tag(id=row["id"], name=row["name"], color=row["color"]) for row in rows]

    def add_document_tag(self, doc_id: str, tag_id: str) -> None:
        """为文档添加标签"""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO document_tags (document_id, tag_id) VALUES (?, ?)",
                (doc_id, tag_id),
            )
            conn.commit()

    def remove_document_tag(self, doc_id: str, tag_id: str) -> None:
        """移除文档标签"""
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM document_tags WHERE document_id = ? AND tag_id = ?",
                (doc_id, tag_id),
            )
            conn.commit()

    def get_documents_by_tag(self, tag_id: str) -> List[DocumentEntry]:
        """获取带有指定标签的文档"""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT d.* FROM documents d
                JOIN document_tags dt ON d.id = dt.document_id
                WHERE dt.tag_id = ? AND d.is_deleted = 0
                """,
                (tag_id,),
            ).fetchall()
            docs = [self._row_to_document(row) for row in rows]
            for doc in docs:
                doc.tags = self._get_document_tags(conn, doc.id)
            return docs


    # ============== 注释操作 ==============

    def save_annotation(self, doc_id: str, annotation: Annotation) -> str:
        """保存注释"""
        data = json.dumps(annotation.to_dict(), ensure_ascii=False)
        with self._get_connection() as conn:
            # 检查是否已存在
            existing = conn.execute(
                "SELECT id FROM annotations WHERE id = ?", (annotation.id,)
            ).fetchone()

            if existing:
                conn.execute(
                    """
                    UPDATE annotations 
                    SET data = ?, modified_at = ?
                    WHERE id = ?
                    """,
                    (data, datetime.now().isoformat(), annotation.id),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO annotations (id, document_id, page_num, data, created_at, modified_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        annotation.id,
                        doc_id,
                        annotation.page_num,
                        data,
                        annotation.created_at.isoformat(),
                        annotation.modified_at.isoformat(),
                    ),
                )
            conn.commit()
        return annotation.id

    def get_annotations(self, doc_id: str, page_num: Optional[int] = None) -> List[Annotation]:
        """获取注释"""
        with self._get_connection() as conn:
            if page_num is not None:
                rows = conn.execute(
                    "SELECT data FROM annotations WHERE document_id = ? AND page_num = ?",
                    (doc_id, page_num),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT data FROM annotations WHERE document_id = ?",
                    (doc_id,),
                ).fetchall()
            return [Annotation.from_dict(json.loads(row["data"])) for row in rows]

    def load_annotations(self, doc_id: str) -> List[Annotation]:
        """加载文档的所有注释（别名方法，用于注释引擎）"""
        return self.get_annotations(doc_id)

    def delete_annotation(self, annotation_id: str) -> None:
        """删除注释"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM annotations WHERE id = ?", (annotation_id,))
            conn.commit()

    # ============== 书签操作 ==============

    def add_bookmark(self, bookmark: Bookmark) -> str:
        """添加书签"""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO bookmarks (id, document_id, page_num, title, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    bookmark.id,
                    bookmark.document_id,
                    bookmark.page_num,
                    bookmark.title,
                    bookmark.created_at.isoformat(),
                ),
            )
            conn.commit()
        return bookmark.id

    def get_bookmarks(self, doc_id: str) -> List[Bookmark]:
        """获取文档的书签"""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM bookmarks WHERE document_id = ? ORDER BY page_num",
                (doc_id,),
            ).fetchall()
            return [
                Bookmark(
                    id=row["id"],
                    document_id=row["document_id"],
                    page_num=row["page_num"],
                    title=row["title"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                for row in rows
            ]

    def delete_bookmark(self, bookmark_id: str) -> None:
        """删除书签"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
            conn.commit()

    # ============== 插件操作 ==============

    def add_plugin(self, plugin: PluginInfo) -> str:
        """添加插件"""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO plugins (id, name, version, author, description, 
                                     entry_point, permissions, enabled, installed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plugin.id,
                    plugin.name,
                    plugin.version,
                    plugin.author,
                    plugin.description,
                    plugin.entry_point,
                    json.dumps(plugin.permissions),
                    1 if plugin.enabled else 0,
                    plugin.installed_at.isoformat(),
                ),
            )
            conn.commit()
        return plugin.id

    def get_plugin(self, plugin_id: str) -> Optional[PluginInfo]:
        """获取插件"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM plugins WHERE id = ?", (plugin_id,)
            ).fetchone()
            if row:
                return self._row_to_plugin(row)
        return None

    def get_all_plugins(self) -> List[PluginInfo]:
        """获取所有插件"""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM plugins").fetchall()
            return [self._row_to_plugin(row) for row in rows]

    def get_enabled_plugins(self) -> List[PluginInfo]:
        """获取已启用的插件"""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM plugins WHERE enabled = 1").fetchall()
            return [self._row_to_plugin(row) for row in rows]

    def update_plugin_status(self, plugin_id: str, enabled: bool) -> None:
        """更新插件状态"""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE plugins SET enabled = ? WHERE id = ?",
                (1 if enabled else 0, plugin_id),
            )
            conn.commit()

    def delete_plugin(self, plugin_id: str) -> None:
        """删除插件"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM plugins WHERE id = ?", (plugin_id,))
            conn.commit()

    def _row_to_plugin(self, row: sqlite3.Row) -> PluginInfo:
        """将数据库行转换为PluginInfo"""
        return PluginInfo(
            id=row["id"],
            name=row["name"],
            version=row["version"],
            author=row["author"] or "",
            description=row["description"] or "",
            entry_point=row["entry_point"],
            permissions=json.loads(row["permissions"]) if row["permissions"] else [],
            enabled=bool(row["enabled"]),
            installed_at=datetime.fromisoformat(row["installed_at"]),
        )


    # ============== 设置操作 ==============

    def save_settings(self, settings: Settings) -> None:
        """保存设置"""
        json_str = settings.to_json()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO settings (key, value)
                VALUES ('app_settings', ?)
                """,
                (json_str,),
            )
            conn.commit()

    def load_settings(self) -> Settings:
        """加载设置"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = 'app_settings'"
            ).fetchone()
            if row:
                return Settings.from_json(row["value"])
        return Settings()

    def save_setting(self, key: str, value: str) -> None:
        """保存单个设置项"""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )
            conn.commit()

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取单个设置项"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
            if row:
                return row["value"]
        return default

    # ============== 工具方法 ==============

    def generate_id(self) -> str:
        """生成唯一ID"""
        return str(uuid.uuid4())

    def vacuum(self) -> None:
        """压缩数据库"""
        with self._get_connection() as conn:
            conn.execute("VACUUM")

    def get_stats(self) -> dict:
        """获取数据库统计信息"""
        with self._get_connection() as conn:
            doc_count = conn.execute(
                "SELECT COUNT(*) FROM documents WHERE is_deleted = 0"
            ).fetchone()[0]
            folder_count = conn.execute("SELECT COUNT(*) FROM folders").fetchone()[0]
            tag_count = conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
            annotation_count = conn.execute("SELECT COUNT(*) FROM annotations").fetchone()[0]
            bookmark_count = conn.execute("SELECT COUNT(*) FROM bookmarks").fetchone()[0]
            plugin_count = conn.execute("SELECT COUNT(*) FROM plugins").fetchone()[0]

            return {
                "documents": doc_count,
                "folders": folder_count,
                "tags": tag_count,
                "annotations": annotation_count,
                "bookmarks": bookmark_count,
                "plugins": plugin_count,
            }
