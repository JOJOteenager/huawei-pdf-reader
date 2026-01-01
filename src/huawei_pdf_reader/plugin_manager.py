"""
华为平板PDF阅读器 - 插件管理器

负责插件的验证、安装、启用、禁用和卸载。
实现插件沙箱和错误隔离机制。
"""

import importlib.util
import json
import os
import shutil
import sys
import traceback
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import uuid

from huawei_pdf_reader.models import PluginInfo
from huawei_pdf_reader.database import Database


# ============== 权限错误 ==============

class PermissionDeniedError(Exception):
    """权限被拒绝错误"""
    pass


class PluginError(Exception):
    """插件错误基类"""
    pass


class PluginLoadError(PluginError):
    """插件加载错误"""
    pass


class PluginExecutionError(PluginError):
    """插件执行错误"""
    pass


# ============== 插件API接口 ==============

class PluginAPI:
    """
    插件API接口
    
    提供给插件调用的核心功能接口。
    通过此接口，插件可以安全地访问应用的部分功能。
    
    权限列表:
    - events: 事件监听和触发
    - document_read: 读取文档信息
    - document_write: 修改文档
    - annotation_read: 读取注释
    - annotation_write: 修改注释
    - settings_read: 读取设置
    - settings_write: 修改设置
    - network: 网络访问
    - storage: 本地存储
    """
    
    def __init__(self, plugin_id: str, permissions: List[str]):
        """
        初始化插件API
        
        Args:
            plugin_id: 插件ID
            permissions: 插件拥有的权限列表
        """
        self._plugin_id = plugin_id
        self._permissions = set(permissions)
        self._callbacks: Dict[str, List[Callable]] = {}
        self._storage: Dict[str, Any] = {}
        self._logs: List[Dict[str, Any]] = []
    
    def _check_permission(self, permission: str) -> bool:
        """检查是否有指定权限"""
        return permission in self._permissions
    
    def _require_permission(self, permission: str) -> None:
        """要求指定权限，无权限则抛出异常"""
        if not self._check_permission(permission):
            raise PermissionDeniedError(
                f"插件 {self._plugin_id} 没有 {permission} 权限"
            )
    
    # ============== 事件系统 ==============
    
    def register_callback(self, event: str, callback: Callable) -> bool:
        """
        注册事件回调
        
        Args:
            event: 事件名称
            callback: 回调函数
            
        Returns:
            是否注册成功
        """
        if not self._check_permission("events"):
            return False
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)
        return True
    
    def unregister_callback(self, event: str, callback: Callable) -> bool:
        """
        取消注册事件回调
        
        Args:
            event: 事件名称
            callback: 回调函数
            
        Returns:
            是否取消成功
        """
        if event in self._callbacks and callback in self._callbacks[event]:
            self._callbacks[event].remove(callback)
            return True
        return False
    
    def get_callbacks(self, event: str) -> List[Callable]:
        """获取指定事件的所有回调"""
        return self._callbacks.get(event, []).copy()
    
    def clear_callbacks(self) -> None:
        """清除所有回调"""
        self._callbacks.clear()
    
    # ============== 日志系统 ==============
    
    def log(self, message: str, level: str = "info") -> None:
        """
        记录日志
        
        Args:
            message: 日志消息
            level: 日志级别 (debug, info, warning, error)
        """
        log_entry = {
            "plugin_id": self._plugin_id,
            "level": level.upper(),
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        self._logs.append(log_entry)
        print(f"[Plugin:{self._plugin_id}][{level.upper()}] {message}")
    
    def get_logs(self) -> List[Dict[str, Any]]:
        """获取日志记录"""
        return self._logs.copy()
    
    def clear_logs(self) -> None:
        """清除日志"""
        self._logs.clear()
    
    # ============== 存储系统 ==============
    
    def store_data(self, key: str, value: Any) -> bool:
        """
        存储数据
        
        Args:
            key: 数据键
            value: 数据值
            
        Returns:
            是否存储成功
        """
        if not self._check_permission("storage"):
            return False
        self._storage[key] = value
        return True
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """
        获取存储的数据
        
        Args:
            key: 数据键
            default: 默认值
            
        Returns:
            存储的数据或默认值
        """
        if not self._check_permission("storage"):
            return default
        return self._storage.get(key, default)
    
    def delete_data(self, key: str) -> bool:
        """
        删除存储的数据
        
        Args:
            key: 数据键
            
        Returns:
            是否删除成功
        """
        if not self._check_permission("storage"):
            return False
        if key in self._storage:
            del self._storage[key]
            return True
        return False
    
    def get_all_data(self) -> Dict[str, Any]:
        """获取所有存储的数据"""
        if not self._check_permission("storage"):
            return {}
        return self._storage.copy()
    
    # ============== 信息查询 ==============
    
    def get_plugin_id(self) -> str:
        """获取插件ID"""
        return self._plugin_id
    
    def get_permissions(self) -> List[str]:
        """获取插件权限列表"""
        return list(self._permissions)
    
    def has_permission(self, permission: str) -> bool:
        """检查是否有指定权限"""
        return self._check_permission(permission)
    
    # ============== 清理 ==============
    
    def cleanup(self) -> None:
        """清理所有资源"""
        self.clear_callbacks()
        self.clear_logs()
        self._storage.clear()


# ============== 插件基类 ==============

class IPlugin(ABC):
    """插件基类接口"""
    
    @abstractmethod
    def on_load(self, api: PluginAPI) -> None:
        """
        插件加载时调用
        
        Args:
            api: 插件API接口
        """
        pass
    
    @abstractmethod
    def on_unload(self) -> None:
        """插件卸载时调用"""
        pass
    
    @property
    @abstractmethod
    def info(self) -> PluginInfo:
        """获取插件信息"""
        pass


# ============== 插件沙箱 ==============

@dataclass
class PluginSandbox:
    """
    插件沙箱
    
    用于隔离插件执行环境，捕获插件错误。
    提供错误计数和自动禁用机制。
    """
    plugin_id: str
    plugin_instance: Optional[IPlugin] = None
    api: Optional[PluginAPI] = None
    is_loaded: bool = False
    last_error: Optional[str] = None
    error_count: int = 0
    max_errors: int = 5  # 最大错误次数，超过后自动禁用
    
    def execute_safely(self, func: Callable, *args, **kwargs) -> Tuple[bool, Any, Optional[str]]:
        """
        安全执行函数
        
        在沙箱环境中执行函数，捕获所有异常。
        
        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            (是否成功, 返回值, 错误信息)
        """
        try:
            result = func(*args, **kwargs)
            return True, result, None
        except Exception as e:
            self.error_count += 1
            self.last_error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            return False, None, self.last_error
    
    def should_disable(self) -> bool:
        """
        检查是否应该禁用插件
        
        当错误次数超过阈值时返回True
        
        Returns:
            是否应该禁用
        """
        return self.error_count >= self.max_errors
    
    def reset_error_count(self) -> None:
        """重置错误计数"""
        self.error_count = 0
        self.last_error = None
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        获取错误摘要
        
        Returns:
            包含错误信息的字典
        """
        return {
            "plugin_id": self.plugin_id,
            "is_loaded": self.is_loaded,
            "error_count": self.error_count,
            "max_errors": self.max_errors,
            "last_error": self.last_error,
            "should_disable": self.should_disable(),
        }


# ============== 插件管理器 ==============

class PluginManager:
    """
    插件管理器
    
    负责插件的完整生命周期管理：
    - 验证插件格式和安全性
    - 安装和卸载插件
    - 启用和禁用插件
    - 错误隔离和恢复
    """
    
    # 插件清单文件名
    MANIFEST_FILE = "plugin.json"
    
    # 必需的清单字段
    REQUIRED_MANIFEST_FIELDS = ["id", "name", "version", "entry_point"]
    
    # 允许的权限列表
    ALLOWED_PERMISSIONS = [
        "events",           # 事件监听
        "document_read",    # 读取文档
        "document_write",   # 修改文档
        "annotation_read",  # 读取注释
        "annotation_write", # 修改注释
        "settings_read",    # 读取设置
        "settings_write",   # 修改设置
        "network",          # 网络访问
        "storage",          # 本地存储
    ]
    
    def __init__(self, db: Database, plugins_dir: Path):
        """
        初始化插件管理器
        
        Args:
            db: 数据库实例
            plugins_dir: 插件安装目录
        """
        self._db = db
        self._plugins_dir = plugins_dir
        self._sandboxes: Dict[str, PluginSandbox] = {}
        self._loaded_modules: Dict[str, Any] = {}
        
        # 确保插件目录存在
        self._plugins_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_plugin(self, plugin_path: Path) -> Tuple[bool, str]:
        """
        验证插件
        
        验证插件文件格式和清单内容的有效性。
        
        Args:
            plugin_path: 插件文件路径（.zip文件或目录）
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            # 检查路径是否存在
            if not plugin_path.exists():
                return False, f"插件路径不存在: {plugin_path}"
            
            # 如果是zip文件，解压到临时目录验证
            if plugin_path.suffix == ".zip":
                return self._validate_zip_plugin(plugin_path)
            elif plugin_path.is_dir():
                return self._validate_dir_plugin(plugin_path)
            else:
                return False, "不支持的插件格式，请使用.zip文件或目录"
                
        except Exception as e:
            return False, f"验证插件时发生错误: {str(e)}"
    
    def _validate_zip_plugin(self, zip_path: Path) -> Tuple[bool, str]:
        """验证zip格式的插件"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # 检查是否包含清单文件
                names = zf.namelist()
                manifest_path = None
                
                for name in names:
                    if name.endswith(self.MANIFEST_FILE):
                        manifest_path = name
                        break
                
                if not manifest_path:
                    return False, f"插件缺少清单文件: {self.MANIFEST_FILE}"
                
                # 读取并验证清单
                manifest_data = zf.read(manifest_path).decode('utf-8')
                return self._validate_manifest(manifest_data)
                
        except zipfile.BadZipFile:
            return False, "无效的zip文件"
        except Exception as e:
            return False, f"读取zip文件失败: {str(e)}"
    
    def _validate_dir_plugin(self, dir_path: Path) -> Tuple[bool, str]:
        """验证目录格式的插件"""
        manifest_path = dir_path / self.MANIFEST_FILE
        
        if not manifest_path.exists():
            return False, f"插件缺少清单文件: {self.MANIFEST_FILE}"
        
        try:
            manifest_data = manifest_path.read_text(encoding='utf-8')
            return self._validate_manifest(manifest_data)
        except Exception as e:
            return False, f"读取清单文件失败: {str(e)}"
    
    def _validate_manifest(self, manifest_data: str) -> Tuple[bool, str]:
        """验证清单内容"""
        try:
            manifest = json.loads(manifest_data)
        except json.JSONDecodeError as e:
            return False, f"清单文件JSON格式错误: {str(e)}"
        
        # 检查必需字段
        for field in self.REQUIRED_MANIFEST_FIELDS:
            if field not in manifest:
                return False, f"清单缺少必需字段: {field}"
            if not manifest[field]:
                return False, f"清单字段不能为空: {field}"
        
        # 验证权限
        permissions = manifest.get("permissions", [])
        if not isinstance(permissions, list):
            return False, "permissions字段必须是数组"
        
        for perm in permissions:
            if perm not in self.ALLOWED_PERMISSIONS:
                return False, f"未知的权限: {perm}"
        
        # 验证入口点格式
        entry_point = manifest["entry_point"]
        if not entry_point.endswith(".py"):
            return False, "入口点必须是.py文件"
        
        return True, ""
    
    def install_plugin(self, plugin_path: Path) -> PluginInfo:
        """
        安装插件
        
        Args:
            plugin_path: 插件文件路径
            
        Returns:
            安装后的插件信息
            
        Raises:
            ValueError: 插件验证失败
            FileExistsError: 插件已存在
        """
        # 先验证插件
        is_valid, error = self.validate_plugin(plugin_path)
        if not is_valid:
            raise ValueError(f"插件验证失败: {error}")
        
        # 读取清单获取插件信息
        manifest = self._read_manifest(plugin_path)
        plugin_id = manifest["id"]
        
        # 检查是否已安装
        existing = self._db.get_plugin(plugin_id)
        if existing:
            raise FileExistsError(f"插件已安装: {plugin_id}")
        
        # 安装插件文件
        install_dir = self._plugins_dir / plugin_id
        self._install_plugin_files(plugin_path, install_dir)
        
        # 创建插件信息
        plugin_info = PluginInfo(
            id=plugin_id,
            name=manifest["name"],
            version=manifest["version"],
            author=manifest.get("author", ""),
            description=manifest.get("description", ""),
            entry_point=manifest["entry_point"],
            permissions=manifest.get("permissions", []),
            enabled=False,
            installed_at=datetime.now(),
        )
        
        # 保存到数据库
        self._db.add_plugin(plugin_info)
        
        return plugin_info
    
    def _read_manifest(self, plugin_path: Path) -> dict:
        """读取插件清单"""
        if plugin_path.suffix == ".zip":
            with zipfile.ZipFile(plugin_path, 'r') as zf:
                for name in zf.namelist():
                    if name.endswith(self.MANIFEST_FILE):
                        return json.loads(zf.read(name).decode('utf-8'))
        else:
            manifest_path = plugin_path / self.MANIFEST_FILE
            return json.loads(manifest_path.read_text(encoding='utf-8'))
        raise ValueError("无法读取插件清单")
    
    def _install_plugin_files(self, source: Path, dest: Path) -> None:
        """安装插件文件到目标目录"""
        # 如果目标目录存在，先删除
        if dest.exists():
            shutil.rmtree(dest)
        
        if source.suffix == ".zip":
            # 解压zip文件
            with zipfile.ZipFile(source, 'r') as zf:
                zf.extractall(dest)
        else:
            # 复制目录
            shutil.copytree(source, dest)
    
    def uninstall_plugin(self, plugin_id: str) -> None:
        """
        卸载插件
        
        Args:
            plugin_id: 插件ID
            
        Raises:
            ValueError: 插件不存在
        """
        plugin = self._db.get_plugin(plugin_id)
        if not plugin:
            raise ValueError(f"插件不存在: {plugin_id}")
        
        # 如果插件已启用，先禁用
        if plugin.enabled:
            self.disable_plugin(plugin_id)
        
        # 删除插件文件
        install_dir = self._plugins_dir / plugin_id
        if install_dir.exists():
            shutil.rmtree(install_dir)
        
        # 从数据库删除
        self._db.delete_plugin(plugin_id)
        
        # 清理沙箱
        if plugin_id in self._sandboxes:
            del self._sandboxes[plugin_id]
    
    def enable_plugin(self, plugin_id: str) -> None:
        """
        启用插件
        
        Args:
            plugin_id: 插件ID
            
        Raises:
            ValueError: 插件不存在或加载失败
        """
        plugin = self._db.get_plugin(plugin_id)
        if not plugin:
            raise ValueError(f"插件不存在: {plugin_id}")
        
        if plugin.enabled:
            return  # 已经启用
        
        # 加载插件
        self._load_plugin(plugin)
        
        # 更新数据库状态
        self._db.update_plugin_status(plugin_id, True)
    
    def disable_plugin(self, plugin_id: str) -> None:
        """
        禁用插件
        
        Args:
            plugin_id: 插件ID
            
        Raises:
            ValueError: 插件不存在
        """
        plugin = self._db.get_plugin(plugin_id)
        if not plugin:
            raise ValueError(f"插件不存在: {plugin_id}")
        
        if not plugin.enabled:
            return  # 已经禁用
        
        # 卸载插件
        self._unload_plugin(plugin_id)
        
        # 更新数据库状态
        self._db.update_plugin_status(plugin_id, False)
    
    def _load_plugin(self, plugin: PluginInfo) -> None:
        """加载插件"""
        install_dir = self._plugins_dir / plugin.id
        entry_point = install_dir / plugin.entry_point
        
        if not entry_point.exists():
            raise ValueError(f"插件入口点不存在: {entry_point}")
        
        # 创建沙箱
        sandbox = PluginSandbox(plugin_id=plugin.id)
        
        try:
            # 动态加载模块
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin.id}",
                entry_point
            )
            if spec is None or spec.loader is None:
                raise ValueError("无法加载插件模块")
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"plugin_{plugin.id}"] = module
            spec.loader.exec_module(module)
            
            # 查找插件类
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, IPlugin) and 
                    attr is not IPlugin):
                    plugin_class = attr
                    break
            
            if plugin_class is None:
                raise ValueError("插件模块中未找到IPlugin实现类")
            
            # 创建插件实例
            plugin_instance = plugin_class()
            
            # 创建API
            api = PluginAPI(plugin.id, plugin.permissions)
            
            # 调用on_load
            success, _, error = sandbox.execute_safely(
                plugin_instance.on_load, api
            )
            
            if not success:
                raise ValueError(f"插件加载失败: {error}")
            
            # 保存到沙箱
            sandbox.plugin_instance = plugin_instance
            sandbox.api = api
            sandbox.is_loaded = True
            
            self._sandboxes[plugin.id] = sandbox
            self._loaded_modules[plugin.id] = module
            
        except Exception as e:
            sandbox.last_error = str(e)
            self._sandboxes[plugin.id] = sandbox
            raise ValueError(f"加载插件失败: {str(e)}")
    
    def _unload_plugin(self, plugin_id: str) -> None:
        """卸载插件"""
        sandbox = self._sandboxes.get(plugin_id)
        
        if sandbox and sandbox.plugin_instance:
            # 安全调用on_unload
            sandbox.execute_safely(sandbox.plugin_instance.on_unload)
            sandbox.is_loaded = False
            sandbox.plugin_instance = None
            sandbox.api = None
        
        # 从sys.modules移除
        module_name = f"plugin_{plugin_id}"
        if module_name in sys.modules:
            del sys.modules[module_name]
        
        if plugin_id in self._loaded_modules:
            del self._loaded_modules[plugin_id]
    
    def get_installed_plugins(self) -> List[PluginInfo]:
        """
        获取已安装的插件列表
        
        Returns:
            插件信息列表
        """
        return self._db.get_all_plugins()
    
    def get_enabled_plugins(self) -> List[PluginInfo]:
        """
        获取已启用的插件列表
        
        Returns:
            已启用的插件信息列表
        """
        return self._db.get_enabled_plugins()
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginInfo]:
        """
        获取插件信息
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            插件信息，不存在则返回None
        """
        return self._db.get_plugin(plugin_id)
    
    def is_plugin_loaded(self, plugin_id: str) -> bool:
        """
        检查插件是否已加载
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            是否已加载
        """
        sandbox = self._sandboxes.get(plugin_id)
        return sandbox is not None and sandbox.is_loaded
    
    def get_plugin_error(self, plugin_id: str) -> Optional[str]:
        """
        获取插件最后的错误信息
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            错误信息，无错误则返回None
        """
        sandbox = self._sandboxes.get(plugin_id)
        return sandbox.last_error if sandbox else None
    
    def execute_plugin_safely(
        self, 
        plugin_id: str, 
        method_name: str, 
        *args, 
        **kwargs
    ) -> Tuple[bool, Any, Optional[str]]:
        """
        安全执行插件方法
        
        Args:
            plugin_id: 插件ID
            method_name: 方法名
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            (是否成功, 返回值, 错误信息)
        """
        sandbox = self._sandboxes.get(plugin_id)
        
        if not sandbox or not sandbox.is_loaded or not sandbox.plugin_instance:
            return False, None, "插件未加载"
        
        method = getattr(sandbox.plugin_instance, method_name, None)
        if method is None:
            return False, None, f"方法不存在: {method_name}"
        
        return sandbox.execute_safely(method, *args, **kwargs)
    
    def load_enabled_plugins(self) -> Dict[str, Optional[str]]:
        """
        加载所有已启用的插件
        
        应用启动时调用此方法自动加载插件。
        
        Returns:
            字典，键为插件ID，值为错误信息（成功则为None）
        """
        results = {}
        enabled_plugins = self._db.get_enabled_plugins()
        
        for plugin in enabled_plugins:
            try:
                self._load_plugin(plugin)
                results[plugin.id] = None
            except Exception as e:
                results[plugin.id] = str(e)
                # 加载失败时禁用插件
                self._db.update_plugin_status(plugin.id, False)
        
        return results
    
    def get_sandbox(self, plugin_id: str) -> Optional[PluginSandbox]:
        """
        获取插件沙箱
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            插件沙箱，不存在则返回None
        """
        return self._sandboxes.get(plugin_id)
    
    def unload_all_plugins(self) -> None:
        """
        卸载所有已加载的插件
        
        应用关闭时调用此方法清理插件。
        """
        # 获取所有已加载的插件ID
        loaded_plugin_ids = list(self._sandboxes.keys())
        
        for plugin_id in loaded_plugin_ids:
            try:
                self._unload_plugin(plugin_id)
            except Exception:
                pass  # 忽略卸载错误
        
        # 清理所有沙箱
        self._sandboxes.clear()
        self._loaded_modules.clear()
