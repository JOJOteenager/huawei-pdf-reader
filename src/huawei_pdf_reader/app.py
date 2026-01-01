"""
华为平板PDF阅读器 - 应用容器

实现依赖注入和模块集成。
Requirements: 整体集成
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import os
import tempfile


class ServiceContainer:
    """服务容器 - 依赖注入容器"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, bool] = {}
    
    def register(self, name: str, factory: Callable, singleton: bool = True) -> None:
        """注册服务工厂"""
        self._factories[name] = factory
        self._singletons[name] = singleton
    
    def register_instance(self, name: str, instance: Any) -> None:
        """注册服务实例"""
        self._services[name] = instance
        self._singletons[name] = True
    
    def get(self, name: str) -> Any:
        """获取服务实例"""
        if name in self._services:
            return self._services[name]
        
        if name not in self._factories:
            raise KeyError(f"Service '{name}' not registered")
        
        instance = self._factories[name](self)
        
        if self._singletons.get(name, True):
            self._services[name] = instance
        
        return instance
    
    def has(self, name: str) -> bool:
        """检查服务是否已注册"""
        return name in self._services or name in self._factories


@dataclass
class AppConfig:
    """应用配置"""
    data_dir: Path = field(default_factory=lambda: Path.home() / ".huawei_pdf_reader")
    db_name: str = "app.db"
    plugin_dir: str = "plugins"
    backup_dir: str = "backups"
    temp_dir: Optional[Path] = None
    
    def __post_init__(self):
        if self.temp_dir is None:
            self.temp_dir = Path(tempfile.gettempdir()) / "huawei_pdf_reader"
    
    @property
    def db_path(self) -> Path:
        return self.data_dir / self.db_name
    
    @property
    def plugins_path(self) -> Path:
        return self.data_dir / self.plugin_dir
    
    @property
    def backups_path(self) -> Path:
        return self.data_dir / self.backup_dir
    
    def ensure_dirs(self) -> None:
        """确保所有必要目录存在"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.plugins_path.mkdir(parents=True, exist_ok=True)
        self.backups_path.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)


class Application:
    """应用程序主类 - 集成所有模块"""
    
    _instance: Optional['Application'] = None
    
    def __init__(self, config: Optional[AppConfig] = None):
        """
        初始化应用程序
        
        Args:
            config: 应用配置，如果为None则使用默认配置
        """
        self.config = config or AppConfig()
        self.config.ensure_dirs()
        
        self._container = ServiceContainer()
        self._initialized = False
        
        # 注册核心服务
        self._register_services()
    
    @classmethod
    def get_instance(cls, config: Optional[AppConfig] = None) -> 'Application':
        """获取应用程序单例"""
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """重置应用程序单例（用于测试）"""
        cls._instance = None
    
    def _register_services(self) -> None:
        """注册所有服务"""
        # 注册配置
        self._container.register_instance('config', self.config)
        
        # 注册数据库
        self._container.register('database', self._create_database)
        
        # 注册设置
        self._container.register('settings', self._create_settings)
        
        # 注册文档处理器
        self._container.register('pdf_renderer', self._create_pdf_renderer, singleton=False)
        self._container.register('word_renderer', self._create_word_renderer, singleton=False)
        
        # 注册注释引擎
        self._container.register('annotation_engine', self._create_annotation_engine)
        
        # 注册防误触系统
        self._container.register('palm_rejection', self._create_palm_rejection)
        
        # 注册文件管理器
        self._container.register('file_manager', self._create_file_manager)
        
        # 注册繁简转换器
        self._container.register('chinese_converter', self._create_chinese_converter)
        
        # 注册翻译服务
        self._container.register('translation_service', self._create_translation_service)
        
        # 注册OCR引擎
        self._container.register('ocr_engine', self._create_ocr_engine)
        
        # 注册放大镜
        self._container.register('magnifier', self._create_magnifier)
        
        # 注册插件管理器
        self._container.register('plugin_manager', self._create_plugin_manager)
        
        # 注册备份服务
        self._container.register('backup_service', self._create_backup_service)
    
    # ============== 服务工厂方法 ==============
    
    def _create_database(self, container: ServiceContainer):
        """创建数据库实例"""
        from huawei_pdf_reader.database import Database
        return Database(self.config.db_path)
    
    def _create_settings(self, container: ServiceContainer):
        """创建设置实例"""
        db = container.get('database')
        return db.load_settings()
    
    def _create_pdf_renderer(self, container: ServiceContainer):
        """创建PDF渲染器"""
        from huawei_pdf_reader.document_processor import PDFRenderer
        return PDFRenderer()
    
    def _create_word_renderer(self, container: ServiceContainer):
        """创建Word渲染器"""
        from huawei_pdf_reader.document_processor import WordRenderer
        return WordRenderer()
    
    def _create_annotation_engine(self, container: ServiceContainer):
        """创建注释引擎"""
        from huawei_pdf_reader.annotation_engine import AnnotationEngine
        db = container.get('database')
        return AnnotationEngine(database=db)
    
    def _create_palm_rejection(self, container: ServiceContainer):
        """创建防误触系统"""
        from huawei_pdf_reader.palm_rejection import PalmRejectionSystem
        settings = container.get('settings')
        sensitivity = settings.stylus.palm_rejection_sensitivity
        return PalmRejectionSystem(sensitivity=sensitivity)
    
    def _create_file_manager(self, container: ServiceContainer):
        """创建文件管理器"""
        from huawei_pdf_reader.file_manager import FileManager
        db = container.get('database')
        return FileManager(db=db)
    
    def _create_chinese_converter(self, container: ServiceContainer):
        """创建繁简转换器"""
        from huawei_pdf_reader.chinese_converter import ChineseConverter
        return ChineseConverter()
    
    def _create_translation_service(self, container: ServiceContainer):
        """创建翻译服务"""
        from huawei_pdf_reader.translation_service import TranslationService, MockTranslationService
        settings = container.get('settings')
        # 根据配置选择翻译服务
        api_provider = settings.translation.api_provider
        if api_provider == "mock":
            return MockTranslationService()
        # 尝试使用真实翻译服务，如果依赖不可用则使用Mock
        try:
            return TranslationService()
        except ImportError:
            return MockTranslationService()
    
    def _create_ocr_engine(self, container: ServiceContainer):
        """创建OCR引擎"""
        from huawei_pdf_reader.magnifier import MockOCREngine
        # 默认使用Mock OCR引擎，实际部署时可替换为PaddleOCR
        return MockOCREngine()
    
    def _create_magnifier(self, container: ServiceContainer):
        """创建放大镜"""
        from huawei_pdf_reader.magnifier import Magnifier
        translation = container.get('translation_service')
        converter = container.get('chinese_converter')
        ocr = container.get('ocr_engine')
        return Magnifier(
            translation_service=translation,
            chinese_converter=converter,
            ocr_engine=ocr
        )
    
    def _create_plugin_manager(self, container: ServiceContainer):
        """创建插件管理器"""
        from huawei_pdf_reader.plugin_manager import PluginManager
        db = container.get('database')
        return PluginManager(
            db=db,
            plugins_dir=self.config.plugins_path
        )
    
    def _create_backup_service(self, container: ServiceContainer):
        """创建备份服务"""
        from huawei_pdf_reader.backup_service import BackupService
        db = container.get('database')
        settings = container.get('settings')
        service = BackupService(
            database=db,
            data_dir=self.config.data_dir,
            backup_dir=self.config.backups_path
        )
        service.set_config(settings.backup)
        return service
    
    # ============== 公共接口 ==============
    
    def initialize(self) -> None:
        """初始化应用程序"""
        if self._initialized:
            return
        
        # 加载已启用的插件
        plugin_manager = self.get_plugin_manager()
        plugin_manager.load_enabled_plugins()
        
        self._initialized = True
    
    def shutdown(self) -> None:
        """关闭应用程序"""
        if not self._initialized:
            return
        
        # 卸载所有插件
        plugin_manager = self.get_plugin_manager()
        plugin_manager.unload_all_plugins()
        
        # 保存设置
        self.save_settings()
        
        self._initialized = False
    
    # ============== 服务访问器 ==============
    
    @property
    def database(self):
        """获取数据库"""
        return self._container.get('database')
    
    @property
    def settings(self):
        """获取设置"""
        return self._container.get('settings')
    
    def get_database(self):
        """获取数据库"""
        return self._container.get('database')
    
    def get_settings(self):
        """获取设置"""
        return self._container.get('settings')
    
    def save_settings(self) -> None:
        """保存设置"""
        db = self.get_database()
        settings = self.get_settings()
        db.save_settings(settings)
    
    def get_pdf_renderer(self):
        """获取PDF渲染器（每次返回新实例）"""
        return self._container.get('pdf_renderer')
    
    def get_word_renderer(self):
        """获取Word渲染器（每次返回新实例）"""
        return self._container.get('word_renderer')
    
    def get_annotation_engine(self):
        """获取注释引擎"""
        return self._container.get('annotation_engine')
    
    def get_palm_rejection(self):
        """获取防误触系统"""
        return self._container.get('palm_rejection')
    
    def get_file_manager(self):
        """获取文件管理器"""
        return self._container.get('file_manager')
    
    def get_chinese_converter(self):
        """获取繁简转换器"""
        return self._container.get('chinese_converter')
    
    def get_translation_service(self):
        """获取翻译服务"""
        return self._container.get('translation_service')
    
    def get_magnifier(self):
        """获取放大镜"""
        return self._container.get('magnifier')
    
    def get_plugin_manager(self):
        """获取插件管理器"""
        return self._container.get('plugin_manager')
    
    def get_backup_service(self):
        """获取备份服务"""
        return self._container.get('backup_service')
    
    def create_renderer_for_file(self, file_path: Path):
        """根据文件类型创建渲染器"""
        from huawei_pdf_reader.document_processor import create_renderer
        return create_renderer(file_path)
    
    # ============== 便捷方法 ==============
    
    def open_document(self, file_path: Path):
        """打开文档"""
        renderer = self.create_renderer_for_file(file_path)
        doc_info = renderer.open(file_path)
        return renderer, doc_info
    
    def translate_text(self, text: str, direction: str = "en_to_zh") -> str:
        """翻译文本"""
        from huawei_pdf_reader.models import TranslationDirection
        service = self.get_translation_service()
        dir_enum = TranslationDirection(direction)
        result = service.translate(text, dir_enum)
        return result.translated if result.success else text
    
    def convert_chinese(self, text: str, direction: str = "t2s") -> str:
        """繁简转换"""
        from huawei_pdf_reader.models import ConversionDirection
        converter = self.get_chinese_converter()
        dir_enum = ConversionDirection(direction)
        return converter.convert(text, dir_enum)


# 全局应用实例访问函数
def get_app(config: Optional[AppConfig] = None) -> Application:
    """获取应用程序实例"""
    return Application.get_instance(config)
