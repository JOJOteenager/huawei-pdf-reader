"""
华为平板PDF阅读器 - 数据模型

定义所有数据类和枚举类型。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple
import json


# ============== 枚举类型 ==============

class PenType(Enum):
    """笔类型"""
    BALLPOINT = "ballpoint"      # 圆珠笔
    FOUNTAIN = "fountain"        # 钢笔
    HIGHLIGHTER = "highlighter"  # 荧光笔
    PENCIL = "pencil"           # 铅笔
    MARKER = "marker"           # 马克笔


class TouchType(Enum):
    """触摸类型"""
    STYLUS = "stylus"      # 手写笔
    FINGER = "finger"      # 手指
    PALM = "palm"          # 手掌
    UNKNOWN = "unknown"


class MagnifierAction(Enum):
    """放大镜操作类型"""
    MAGNIFY = "magnify"                  # 仅放大
    TRANSLATE_EN_ZH = "translate_en_zh"  # 英译汉
    TRANSLATE_ZH_EN = "translate_zh_en"  # 汉译英
    CONVERT_T2S = "convert_t2s"          # 繁转简
    CONVERT_S2T = "convert_s2t"          # 简转繁


class TranslationDirection(Enum):
    """翻译方向"""
    EN_TO_ZH = "en_to_zh"  # 英译汉
    ZH_TO_EN = "zh_to_en"  # 汉译英


class ConversionDirection(Enum):
    """转换方向"""
    TRADITIONAL_TO_SIMPLIFIED = "t2s"  # 繁转简
    SIMPLIFIED_TO_TRADITIONAL = "s2t"  # 简转繁


class BackupProvider(Enum):
    """备份提供商"""
    LOCAL = "local"
    BAIDU_PAN = "baidu_pan"
    ONEDRIVE = "onedrive"


# ============== 文档相关数据类 ==============

@dataclass
class PageInfo:
    """页面信息"""
    page_number: int
    width: float
    height: float
    rotation: int = 0

    def to_dict(self) -> dict:
        return {
            "page_number": self.page_number,
            "width": self.width,
            "height": self.height,
            "rotation": self.rotation,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PageInfo":
        return cls(
            page_number=data["page_number"],
            width=data["width"],
            height=data["height"],
            rotation=data.get("rotation", 0),
        )


@dataclass
class DocumentInfo:
    """文档信息"""
    path: Path
    title: str
    total_pages: int
    file_type: str  # 'pdf' or 'docx'

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "title": self.title,
            "total_pages": self.total_pages,
            "file_type": self.file_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentInfo":
        return cls(
            path=Path(data["path"]),
            title=data["title"],
            total_pages=data["total_pages"],
            file_type=data["file_type"],
        )


@dataclass
class DocumentEntry:
    """文档条目"""
    id: str
    path: Path
    title: str
    file_type: str
    size: int
    folder_id: Optional[str] = None
    thumbnail: Optional[bytes] = None
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    is_deleted: bool = False
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "path": str(self.path),
            "title": self.title,
            "file_type": self.file_type,
            "size": self.size,
            "folder_id": self.folder_id,
            "thumbnail": self.thumbnail.hex() if self.thumbnail else None,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "is_deleted": self.is_deleted,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentEntry":
        return cls(
            id=data["id"],
            path=Path(data["path"]),
            title=data["title"],
            file_type=data["file_type"],
            size=data["size"],
            folder_id=data.get("folder_id"),
            thumbnail=bytes.fromhex(data["thumbnail"]) if data.get("thumbnail") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            modified_at=datetime.fromisoformat(data["modified_at"]),
            is_deleted=data.get("is_deleted", False),
            tags=data.get("tags", []),
        )


@dataclass
class Folder:
    """文件夹"""
    id: str
    name: str
    parent_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Folder":
        return cls(
            id=data["id"],
            name=data["name"],
            parent_id=data.get("parent_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
        )


@dataclass
class Tag:
    """标签"""
    id: str
    name: str
    color: str = "#808080"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Tag":
        return cls(
            id=data["id"],
            name=data["name"],
            color=data.get("color", "#808080"),
        )


@dataclass
class Bookmark:
    """书签"""
    id: str
    document_id: str
    page_num: int
    title: str
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "page_num": self.page_num,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Bookmark":
        return cls(
            id=data["id"],
            document_id=data["document_id"],
            page_num=data["page_num"],
            title=data["title"],
            created_at=datetime.fromisoformat(data["created_at"]),
        )


# ============== 注释相关数据类 ==============

@dataclass
class StrokePoint:
    """笔画点"""
    x: float
    y: float
    pressure: float  # 0.0 - 1.0
    timestamp: float

    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "pressure": self.pressure,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StrokePoint":
        return cls(
            x=data["x"],
            y=data["y"],
            pressure=data["pressure"],
            timestamp=data["timestamp"],
        )


@dataclass
class Stroke:
    """笔画"""
    id: str
    pen_type: PenType
    color: str  # hex color
    width: float
    points: List[StrokePoint] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pen_type": self.pen_type.value,
            "color": self.color,
            "width": self.width,
            "points": [p.to_dict() for p in self.points],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Stroke":
        return cls(
            id=data["id"],
            pen_type=PenType(data["pen_type"]),
            color=data["color"],
            width=data["width"],
            points=[StrokePoint.from_dict(p) for p in data.get("points", [])],
        )


@dataclass
class Annotation:
    """注释"""
    id: str
    page_num: int
    strokes: List[Stroke] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "page_num": self.page_num,
            "strokes": [s.to_dict() for s in self.strokes],
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Annotation":
        return cls(
            id=data["id"],
            page_num=data["page_num"],
            strokes=[Stroke.from_dict(s) for s in data.get("strokes", [])],
            created_at=datetime.fromisoformat(data["created_at"]),
            modified_at=datetime.fromisoformat(data["modified_at"]),
        )


# ============== 触摸事件数据类 ==============

@dataclass
class TouchEvent:
    """触摸事件"""
    id: int
    x: float
    y: float
    pressure: float
    size: float  # 触摸面积
    touch_type: TouchType
    timestamp: float

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "pressure": self.pressure,
            "size": self.size,
            "touch_type": self.touch_type.value,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TouchEvent":
        return cls(
            id=data["id"],
            x=data["x"],
            y=data["y"],
            pressure=data["pressure"],
            size=data["size"],
            touch_type=TouchType(data["touch_type"]),
            timestamp=data["timestamp"],
        )


# ============== 放大镜相关数据类 ==============

@dataclass
class MagnifierConfig:
    """放大镜配置"""
    size: Tuple[int, int] = (200, 200)  # 放大镜尺寸
    zoom_level: float = 2.0              # 放大倍数
    shape: str = "circle"                # 形状: circle/rectangle

    def to_dict(self) -> dict:
        return {
            "size": list(self.size),
            "zoom_level": self.zoom_level,
            "shape": self.shape,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MagnifierConfig":
        return cls(
            size=tuple(data.get("size", [200, 200])),
            zoom_level=data.get("zoom_level", 2.0),
            shape=data.get("shape", "circle"),
        )


@dataclass
class MagnifierResult:
    """放大镜操作结果"""
    action: MagnifierAction
    original_text: str
    result_text: str
    success: bool
    error_message: Optional[str] = None
    region: Optional[Tuple[float, float, float, float]] = None

    def to_dict(self) -> dict:
        return {
            "action": self.action.value,
            "original_text": self.original_text,
            "result_text": self.result_text,
            "success": self.success,
            "error_message": self.error_message,
            "region": list(self.region) if self.region else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MagnifierResult":
        return cls(
            action=MagnifierAction(data["action"]),
            original_text=data["original_text"],
            result_text=data["result_text"],
            success=data["success"],
            error_message=data.get("error_message"),
            region=tuple(data["region"]) if data.get("region") else None,
        )


# ============== 翻译相关数据类 ==============

@dataclass
class TranslationResult:
    """翻译结果"""
    original: str
    translated: str
    direction: TranslationDirection
    success: bool
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "original": self.original,
            "translated": self.translated,
            "direction": self.direction.value,
            "success": self.success,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TranslationResult":
        return cls(
            original=data["original"],
            translated=data["translated"],
            direction=TranslationDirection(data["direction"]),
            success=data["success"],
            error_message=data.get("error_message"),
        )


# ============== 插件相关数据类 ==============

@dataclass
class PluginInfo:
    """插件信息"""
    id: str
    name: str
    version: str
    author: str
    description: str
    entry_point: str
    permissions: List[str] = field(default_factory=list)
    enabled: bool = False
    installed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "entry_point": self.entry_point,
            "permissions": self.permissions,
            "enabled": self.enabled,
            "installed_at": self.installed_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PluginInfo":
        return cls(
            id=data["id"],
            name=data["name"],
            version=data["version"],
            author=data["author"],
            description=data["description"],
            entry_point=data["entry_point"],
            permissions=data.get("permissions", []),
            enabled=data.get("enabled", False),
            installed_at=datetime.fromisoformat(data["installed_at"]) if data.get("installed_at") else datetime.now(),
        )


# ============== 配置相关数据类 ==============

@dataclass
class ReadingConfig:
    """阅读设置"""
    page_direction: str = "vertical"  # vertical/horizontal
    dual_page: bool = False
    continuous_scroll: bool = True
    toolbar_position: str = "top"  # top/bottom/left/right
    eye_protection: bool = False
    keep_screen_on: bool = True

    def to_dict(self) -> dict:
        return {
            "page_direction": self.page_direction,
            "dual_page": self.dual_page,
            "continuous_scroll": self.continuous_scroll,
            "toolbar_position": self.toolbar_position,
            "eye_protection": self.eye_protection,
            "keep_screen_on": self.keep_screen_on,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReadingConfig":
        return cls(
            page_direction=data.get("page_direction", "vertical"),
            dual_page=data.get("dual_page", False),
            continuous_scroll=data.get("continuous_scroll", True),
            toolbar_position=data.get("toolbar_position", "top"),
            eye_protection=data.get("eye_protection", False),
            keep_screen_on=data.get("keep_screen_on", True),
        )


@dataclass
class StylusConfig:
    """手写笔设置"""
    double_tap: str = "eraser"
    long_press: str = "select_text"
    primary_click: str = "none"
    secondary_click: str = "undo"
    pinch: str = "none"
    swipe_up: str = "none"
    swipe_down: str = "none"
    palm_rejection_sensitivity: int = 7  # 1-10

    def to_dict(self) -> dict:
        return {
            "double_tap": self.double_tap,
            "long_press": self.long_press,
            "primary_click": self.primary_click,
            "secondary_click": self.secondary_click,
            "pinch": self.pinch,
            "swipe_up": self.swipe_up,
            "swipe_down": self.swipe_down,
            "palm_rejection_sensitivity": self.palm_rejection_sensitivity,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StylusConfig":
        return cls(
            double_tap=data.get("double_tap", "eraser"),
            long_press=data.get("long_press", "select_text"),
            primary_click=data.get("primary_click", "none"),
            secondary_click=data.get("secondary_click", "undo"),
            pinch=data.get("pinch", "none"),
            swipe_up=data.get("swipe_up", "none"),
            swipe_down=data.get("swipe_down", "none"),
            palm_rejection_sensitivity=data.get("palm_rejection_sensitivity", 7),
        )


@dataclass
class ToolsConfig:
    """工具设置"""
    shape_recognition: bool = True
    pressure_sensitivity: bool = True
    shape_fill: bool = False
    long_press_select_text: bool = True
    long_press_create_menu: bool = True

    def to_dict(self) -> dict:
        return {
            "shape_recognition": self.shape_recognition,
            "pressure_sensitivity": self.pressure_sensitivity,
            "shape_fill": self.shape_fill,
            "long_press_select_text": self.long_press_select_text,
            "long_press_create_menu": self.long_press_create_menu,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ToolsConfig":
        return cls(
            shape_recognition=data.get("shape_recognition", True),
            pressure_sensitivity=data.get("pressure_sensitivity", True),
            shape_fill=data.get("shape_fill", False),
            long_press_select_text=data.get("long_press_select_text", True),
            long_press_create_menu=data.get("long_press_create_menu", True),
        )


@dataclass
class BackupConfig:
    """备份配置"""
    provider: BackupProvider = BackupProvider.LOCAL
    auto_backup: bool = False
    wifi_only: bool = True
    backup_path: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "provider": self.provider.value,
            "auto_backup": self.auto_backup,
            "wifi_only": self.wifi_only,
            "backup_path": self.backup_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BackupConfig":
        return cls(
            provider=BackupProvider(data.get("provider", "local")),
            auto_backup=data.get("auto_backup", False),
            wifi_only=data.get("wifi_only", True),
            backup_path=data.get("backup_path"),
        )


@dataclass
class TranslationConfig:
    """翻译设置"""
    default_direction: str = "en_to_zh"
    api_provider: str = "baidu"

    def to_dict(self) -> dict:
        return {
            "default_direction": self.default_direction,
            "api_provider": self.api_provider,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TranslationConfig":
        return cls(
            default_direction=data.get("default_direction", "en_to_zh"),
            api_provider=data.get("api_provider", "baidu"),
        )


@dataclass
class Settings:
    """应用设置"""
    theme: str = "dark_green"
    language: str = "zh_CN"
    reading: ReadingConfig = field(default_factory=ReadingConfig)
    stylus: StylusConfig = field(default_factory=StylusConfig)
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    backup: BackupConfig = field(default_factory=BackupConfig)
    translation: TranslationConfig = field(default_factory=TranslationConfig)

    def to_dict(self) -> dict:
        return {
            "theme": self.theme,
            "language": self.language,
            "reading": self.reading.to_dict(),
            "stylus": self.stylus.to_dict(),
            "tools": self.tools.to_dict(),
            "backup": self.backup.to_dict(),
            "translation": self.translation.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        return cls(
            theme=data.get("theme", "dark_green"),
            language=data.get("language", "zh_CN"),
            reading=ReadingConfig.from_dict(data.get("reading", {})),
            stylus=StylusConfig.from_dict(data.get("stylus", {})),
            tools=ToolsConfig.from_dict(data.get("tools", {})),
            backup=BackupConfig.from_dict(data.get("backup", {})),
            translation=TranslationConfig.from_dict(data.get("translation", {})),
        )

    def to_json(self) -> str:
        """序列化为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Settings":
        """从JSON字符串反序列化"""
        data = json.loads(json_str)
        return cls.from_dict(data)
