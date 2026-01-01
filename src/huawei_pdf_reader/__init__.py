"""
PDF阅读器

支持PDF/Word文档阅读、华为手写笔注释、防误触、区域翻译和繁简转换功能。
"""

__version__ = "0.1.0"
__author__ = "Developer"

# Android 环境检测
def _is_android():
    """检测是否在 Android 环境运行"""
    try:
        import android
        return True
    except ImportError:
        pass
    try:
        from jnius import autoclass
        return True
    except ImportError:
        pass
    return False

_ANDROID = _is_android()

# 在 Android 上只导出基本信息，避免导入依赖外部库的模块
if _ANDROID:
    # Android 环境 - 最小化导入
    __all__ = [
        "__version__",
        "__author__",
    ]
else:
    # 桌面环境 - 完整导入
    try:
        from huawei_pdf_reader.models import (
            Annotation,
            BackupConfig,
            BackupProvider,
            Bookmark,
            ConversionDirection,
            DocumentEntry,
            DocumentInfo,
            Folder,
            MagnifierAction,
            MagnifierConfig,
            MagnifierResult,
            PageInfo,
            PenType,
            PluginInfo,
            ReadingConfig,
            Settings,
            Stroke,
            StrokePoint,
            StylusConfig,
            Tag,
            ToolsConfig,
            TouchEvent,
            TouchType,
            TranslationConfig,
            TranslationDirection,
            TranslationResult,
        )
        from huawei_pdf_reader.database import Database
        from huawei_pdf_reader.document_processor import (
            IDocumentRenderer,
            PDFRenderer,
            WordRenderer,
            DocumentError,
            FileNotFoundError,
            UnsupportedFormatError,
            CorruptedFileError,
            create_renderer,
        )
        from huawei_pdf_reader.annotation_engine import (
            IAnnotationEngine,
            AnnotationEngine,
        )
        from huawei_pdf_reader.palm_rejection import (
            IPalmRejectionSystem,
            PalmRejectionSystem,
        )
        from huawei_pdf_reader.file_manager import (
            IFileManager,
            FileManager,
            FileManagerError,
            DocumentNotFoundError,
            FolderNotFoundError,
            TagNotFoundError,
        )
        from huawei_pdf_reader.chinese_converter import (
            IChineseConverter,
            ChineseConverter,
        )
        from huawei_pdf_reader.translation_service import (
            ITranslationService,
            TranslationService,
            MockTranslationService,
        )
        from huawei_pdf_reader.magnifier import (
            IOCREngine,
            MockOCREngine,
            IMagnifier,
            Magnifier,
        )
        from huawei_pdf_reader.plugin_manager import (
            PluginAPI,
            IPlugin,
            PluginSandbox,
            PluginManager,
            PermissionDeniedError,
            PluginError,
            PluginLoadError,
            PluginExecutionError,
        )
        from huawei_pdf_reader.backup_service import (
            ICloudProvider,
            BaiduPanProvider,
            OneDriveProvider,
            BackupService,
            BackupError,
            RestoreError,
            CloudProviderError,
        )
        from huawei_pdf_reader.app import (
            Application,
            AppConfig,
            ServiceContainer,
            get_app,
        )

        # UI模块 - 延迟导入以避免Kivy初始化问题
        def get_ui_module():
            """获取UI模块（延迟导入）"""
            from huawei_pdf_reader import ui
            return ui

        __all__ = [
            # Version info
            "__version__",
            "__author__",
            # Application
            "Application",
            "AppConfig",
            "ServiceContainer",
            "get_app",
            # Data models
            "PageInfo",
            "DocumentInfo",
            "DocumentEntry",
            "Folder",
            "Tag",
            "Bookmark",
            "StrokePoint",
            "Stroke",
            "Annotation",
            "TouchType",
            "TouchEvent",
            "PenType",
            "MagnifierAction",
            "MagnifierConfig",
            "MagnifierResult",
            "TranslationDirection",
            "TranslationResult",
            "TranslationConfig",
            "ConversionDirection",
            "PluginInfo",
            "BackupProvider",
            "BackupConfig",
            "ReadingConfig",
            "StylusConfig",
            "ToolsConfig",
            "Settings",
            # Database
            "Database",
            # Document Processor
            "IDocumentRenderer",
            "PDFRenderer",
            "WordRenderer",
            "DocumentError",
            "FileNotFoundError",
            "UnsupportedFormatError",
            "CorruptedFileError",
            "create_renderer",
            # Annotation Engine
            "IAnnotationEngine",
            "AnnotationEngine",
            # Palm Rejection System
            "IPalmRejectionSystem",
            "PalmRejectionSystem",
            # File Manager
            "IFileManager",
            "FileManager",
            "FileManagerError",
            "DocumentNotFoundError",
            "FolderNotFoundError",
            "TagNotFoundError",
            # Chinese Converter
            "IChineseConverter",
            "ChineseConverter",
            # Translation Service
            "ITranslationService",
            "TranslationService",
            "MockTranslationService",
            # Magnifier
            "IOCREngine",
            "MockOCREngine",
            "IMagnifier",
            "Magnifier",
            # Plugin Manager
            "PluginAPI",
            "IPlugin",
            "PluginSandbox",
            "PluginManager",
            "PermissionDeniedError",
            "PluginError",
            "PluginLoadError",
            "PluginExecutionError",
            # Backup Service
            "ICloudProvider",
            "BaiduPanProvider",
            "OneDriveProvider",
            "BackupService",
            "BackupError",
            "RestoreError",
            "CloudProviderError",
            # UI module accessor
            "get_ui_module",
        ]
    except ImportError:
        # 如果导入失败，使用最小化导出
        __all__ = [
            "__version__",
            "__author__",
        ]
