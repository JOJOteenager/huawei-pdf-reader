#!/usr/bin/env python3
"""
华为平板PDF阅读器 - Android 打包脚本

用于构建 Android APK 文件。

使用方法:
    python build_android.py [debug|release]

前置条件:
    1. 安装 Buildozer: pip install buildozer
    2. 安装 Android SDK 和 NDK (Buildozer 会自动下载)
    3. 在 Linux 或 WSL 环境下运行 (Windows 不直接支持)

华为平板优化:
    - 支持 arm64-v8a 和 armeabi-v7a 架构
    - 针对大屏幕平板优化布局
    - 支持华为手写笔输入
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_environment():
    """检查构建环境"""
    print("检查构建环境...")
    
    # 检查操作系统
    if sys.platform == "win32":
        print("警告: Windows 不直接支持 Buildozer")
        print("建议使用 WSL (Windows Subsystem for Linux) 或 Linux 虚拟机")
        print("或者使用 GitHub Actions 进行云端构建")
        return False
    
    # 检查 Python 版本
    if sys.version_info < (3, 10):
        print(f"错误: 需要 Python 3.10+, 当前版本: {sys.version}")
        return False
    
    # 检查 Buildozer
    try:
        result = subprocess.run(
            ["buildozer", "--version"],
            capture_output=True,
            text=True
        )
        print(f"Buildozer 版本: {result.stdout.strip()}")
    except FileNotFoundError:
        print("错误: 未找到 Buildozer")
        print("请安装: pip install buildozer")
        return False
    
    # 检查 Java
    try:
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True
        )
        print(f"Java: {result.stderr.split(chr(10))[0]}")
    except FileNotFoundError:
        print("警告: 未找到 Java, Buildozer 会尝试自动安装")
    
    print("环境检查完成")
    return True


def clean_build():
    """清理构建目录"""
    print("清理构建目录...")
    
    dirs_to_clean = [
        ".buildozer",
        "bin",
        "__pycache__",
    ]
    
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"  删除: {dir_path}")
            shutil.rmtree(dir_path)
    
    # 清理 .pyc 文件
    for pyc_file in Path(".").rglob("*.pyc"):
        pyc_file.unlink()
    
    print("清理完成")


def build_apk(build_type: str = "debug"):
    """
    构建 APK
    
    Args:
        build_type: 构建类型 (debug 或 release)
    """
    print(f"开始构建 {build_type} APK...")
    
    # 确保在正确的目录
    spec_file = Path("buildozer.spec")
    if not spec_file.exists():
        print("错误: 未找到 buildozer.spec 文件")
        print("请在项目根目录运行此脚本")
        return False
    
    # 构建命令
    cmd = ["buildozer", "-v", "android", build_type]
    
    print(f"执行命令: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=True)
        print("-" * 50)
        print(f"构建成功!")
        
        # 查找生成的 APK
        bin_dir = Path("bin")
        if bin_dir.exists():
            apk_files = list(bin_dir.glob("*.apk"))
            if apk_files:
                print(f"APK 文件: {apk_files[0]}")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        return False


def deploy_to_device():
    """部署到设备"""
    print("部署到设备...")
    
    cmd = ["buildozer", "android", "deploy", "run", "logcat"]
    
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"部署失败: {e}")
        return False


def print_usage():
    """打印使用说明"""
    print("""
华为平板PDF阅读器 - Android 打包脚本

使用方法:
    python build_android.py [命令]

命令:
    check       检查构建环境
    clean       清理构建目录
    debug       构建 debug APK
    release     构建 release APK
    deploy      部署到设备并运行
    help        显示此帮助信息

示例:
    python build_android.py check    # 检查环境
    python build_android.py debug    # 构建 debug 版本
    python build_android.py release  # 构建 release 版本

注意:
    - 首次构建需要下载 Android SDK/NDK, 可能需要较长时间
    - 建议在 Linux 或 WSL 环境下运行
    - 华为平板需要开启开发者模式和 USB 调试
""")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print_usage()
        return 0
    
    command = sys.argv[1].lower()
    
    if command == "help":
        print_usage()
        return 0
    
    elif command == "check":
        success = check_environment()
        return 0 if success else 1
    
    elif command == "clean":
        clean_build()
        return 0
    
    elif command == "debug":
        if not check_environment():
            return 1
        success = build_apk("debug")
        return 0 if success else 1
    
    elif command == "release":
        if not check_environment():
            return 1
        success = build_apk("release")
        return 0 if success else 1
    
    elif command == "deploy":
        success = deploy_to_device()
        return 0 if success else 1
    
    else:
        print(f"未知命令: {command}")
        print_usage()
        return 1


if __name__ == "__main__":
    sys.exit(main())
