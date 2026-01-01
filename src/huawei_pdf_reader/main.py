"""
华为平板PDF阅读器 - 主入口

应用程序的主入口点，集成所有模块。
Requirements: 整体集成
"""

import sys
import argparse
from pathlib import Path
from typing import Optional


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="华为平板PDF阅读器 - 支持PDF/Word阅读、手写笔注释、翻译和繁简转换"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="数据目录路径"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="无头模式运行（用于测试）"
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="显示版本信息"
    )
    parser.add_argument(
        "file",
        nargs="?",
        type=Path,
        default=None,
        help="要打开的文档路径"
    )
    return parser.parse_args()


def main() -> int:
    """应用程序主入口"""
    args = parse_args()
    
    # 显示版本信息
    if args.version:
        from huawei_pdf_reader import __version__
        print(f"华为平板PDF阅读器 v{__version__}")
        return 0
    
    print("华为平板PDF阅读器 v0.1.0")
    print("正在初始化...")
    
    try:
        from huawei_pdf_reader.app import Application, AppConfig, get_app
        
        # 创建配置
        config = AppConfig()
        if args.data_dir:
            config.data_dir = args.data_dir
        
        # 获取应用实例
        app = get_app(config)
        
        # 初始化应用
        app.initialize()
        
        if args.headless:
            # 无头模式
            print("无头模式运行")
            return run_headless(app, args.file)
        
        # 运行GUI
        return run_gui(app, args.file)
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保已安装所有依赖: pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"运行错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


def run_gui(app, file_path: Optional[Path] = None) -> int:
    """运行GUI模式"""
    try:
        from huawei_pdf_reader.ui.main_window import PDFReaderApp
        
        # 获取设置
        settings = app.get_settings()
        
        # 创建并运行Kivy应用
        kivy_app = PDFReaderApp(settings=settings, application=app)
        
        # 如果指定了文件，在启动后打开
        if file_path and file_path.exists():
            kivy_app.initial_file = file_path
        
        kivy_app.run()
        
        # 关闭应用
        app.shutdown()
        
        return 0
    except Exception as e:
        print(f"GUI运行错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


def run_headless(app, file_path: Optional[Path] = None) -> int:
    """无头模式运行（用于测试）"""
    print("华为平板PDF阅读器 v0.1.0 (无头模式)")
    
    # 显示已加载的服务
    print("\n已加载的服务:")
    print(f"  - 数据库: {app.get_database()}")
    print(f"  - 文件管理器: {app.get_file_manager()}")
    print(f"  - 注释引擎: {app.get_annotation_engine()}")
    print(f"  - 防误触系统: {app.get_palm_rejection()}")
    print(f"  - 繁简转换器: {app.get_chinese_converter()}")
    print(f"  - 翻译服务: {app.get_translation_service()}")
    print(f"  - 放大镜: {app.get_magnifier()}")
    print(f"  - 插件管理器: {app.get_plugin_manager()}")
    print(f"  - 备份服务: {app.get_backup_service()}")
    
    # 如果指定了文件，尝试打开
    if file_path:
        if file_path.exists():
            print(f"\n打开文档: {file_path}")
            try:
                renderer, doc_info = app.open_document(file_path)
                print(f"  标题: {doc_info.title}")
                print(f"  页数: {doc_info.total_pages}")
                print(f"  类型: {doc_info.file_type}")
                renderer.close()
            except Exception as e:
                print(f"  打开失败: {e}")
        else:
            print(f"\n文件不存在: {file_path}")
    
    # 关闭应用
    app.shutdown()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
