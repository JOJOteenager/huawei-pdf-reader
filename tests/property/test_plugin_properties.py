"""
插件系统属性测试

Feature: huawei-pdf-reader
测试插件系统的验证、生命周期、错误隔离和自动加载功能。

Properties:
- Property 15: 插件验证
- Property 16: 插件生命周期
- Property 17: 插件错误隔离
- Property 18: 插件自动加载

Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.6, 7.7
"""

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pytest
from hypothesis import given, settings, strategies as st, assume

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from huawei_pdf_reader.models import PluginInfo
from huawei_pdf_reader.database import Database
from huawei_pdf_reader.plugin_manager import (
    PluginManager,
    PluginAPI,
    IPlugin,
    PluginSandbox,
)


# ============== 策略定义 ==============

# 有效的插件ID策略（字母数字和下划线）
valid_plugin_id_strategy = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyz0123456789_"),
    min_size=3,
    max_size=30,
).filter(lambda x: x[0].isalpha() if x else False)

# 有效的插件名称策略（只允许安全字符）
valid_plugin_name_strategy = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-"),
    min_size=1,
    max_size=50,
).filter(lambda x: x.strip() != "")

# 版本号策略
version_strategy = st.from_regex(r"[0-9]+\.[0-9]+\.[0-9]+", fullmatch=True)

# 权限策略
permission_strategy = st.lists(
    st.sampled_from([
        "events",
        "document_read",
        "document_write",
        "annotation_read",
        "annotation_write",
        "settings_read",
        "settings_write",
        "network",
        "storage",
    ]),
    unique=True,
    max_size=5,
)

# 无效权限策略
invalid_permission_strategy = st.text(min_size=1, max_size=20).filter(
    lambda x: x not in [
        "events", "document_read", "document_write",
        "annotation_read", "annotation_write",
        "settings_read", "settings_write",
        "network", "storage",
    ]
)


# 有效的插件清单策略
@st.composite
def valid_manifest_strategy(draw):
    """生成有效的插件清单"""
    # 使用安全的字符串策略，避免特殊字符破坏生成的Python代码
    safe_text = st.text(
        alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-"),
        max_size=50,
    )
    return {
        "id": draw(valid_plugin_id_strategy),
        "name": draw(valid_plugin_name_strategy),
        "version": draw(version_strategy),
        "author": draw(safe_text),
        "description": draw(safe_text),
        "entry_point": "main.py",
        "permissions": draw(permission_strategy),
    }


# 无效的插件清单策略（缺少必需字段）
@st.composite
def invalid_manifest_missing_field_strategy(draw):
    """生成缺少必需字段的插件清单"""
    manifest = draw(valid_manifest_strategy())
    # 随机移除一个必需字段
    required_fields = ["id", "name", "version", "entry_point"]
    field_to_remove = draw(st.sampled_from(required_fields))
    del manifest[field_to_remove]
    return manifest, field_to_remove


# 插件信息策略
@st.composite
def plugin_info_strategy(draw):
    """生成插件信息"""
    return PluginInfo(
        id=draw(valid_plugin_id_strategy),
        name=draw(valid_plugin_name_strategy),
        version=draw(version_strategy),
        author=draw(st.text(max_size=50)),
        description=draw(st.text(max_size=200)),
        entry_point="main.py",
        permissions=draw(permission_strategy),
        enabled=draw(st.booleans()),
        installed_at=datetime.now(),
    )


# ============== 辅助函数 ==============

def create_test_plugin_dir(base_dir: Path, manifest: dict) -> Path:
    """创建测试插件目录"""
    plugin_dir = base_dir / manifest["id"]
    plugin_dir.mkdir(parents=True, exist_ok=True)
    
    # 写入清单文件
    manifest_path = plugin_dir / "plugin.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    
    # 写入入口点文件
    entry_point = plugin_dir / manifest["entry_point"]
    entry_point.write_text(f'''
"""测试插件"""
from huawei_pdf_reader.plugin_manager import IPlugin, PluginAPI
from huawei_pdf_reader.models import PluginInfo
from datetime import datetime

class TestPlugin(IPlugin):
    def __init__(self):
        self._api = None
        self._info = PluginInfo(
            id="{manifest["id"]}",
            name="{manifest["name"]}",
            version="{manifest["version"]}",
            author="{manifest.get("author", "")}",
            description="{manifest.get("description", "")}",
            entry_point="{manifest["entry_point"]}",
            permissions={manifest.get("permissions", [])},
            enabled=False,
            installed_at=datetime.now(),
        )
    
    def on_load(self, api: PluginAPI) -> None:
        self._api = api
        api.log("Plugin loaded")
    
    def on_unload(self) -> None:
        if self._api:
            self._api.log("Plugin unloaded")
    
    @property
    def info(self) -> PluginInfo:
        return self._info
''', encoding="utf-8")
    
    return plugin_dir


def create_error_plugin_dir(base_dir: Path, manifest: dict) -> Path:
    """创建会抛出错误的测试插件目录"""
    plugin_dir = base_dir / manifest["id"]
    plugin_dir.mkdir(parents=True, exist_ok=True)
    
    # 写入清单文件
    manifest_path = plugin_dir / "plugin.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    
    # 写入会抛出错误的入口点文件
    entry_point = plugin_dir / manifest["entry_point"]
    entry_point.write_text(f'''
"""会抛出错误的测试插件"""
from huawei_pdf_reader.plugin_manager import IPlugin, PluginAPI
from huawei_pdf_reader.models import PluginInfo
from datetime import datetime

class ErrorPlugin(IPlugin):
    def __init__(self):
        self._info = PluginInfo(
            id="{manifest["id"]}",
            name="{manifest["name"]}",
            version="{manifest["version"]}",
            author="",
            description="",
            entry_point="{manifest["entry_point"]}",
            permissions=[],
            enabled=False,
            installed_at=datetime.now(),
        )
    
    def on_load(self, api: PluginAPI) -> None:
        raise RuntimeError("Plugin load error for testing")
    
    def on_unload(self) -> None:
        pass
    
    @property
    def info(self) -> PluginInfo:
        return self._info
''', encoding="utf-8")
    
    return plugin_dir


# ============== Property 15: 插件验证 ==============

class TestPluginValidation:
    """
    Property 15: 插件验证
    
    For any 插件文件，验证函数应返回(bool, str)元组，
    其中bool表示是否有效，str为错误信息（有效时为空）。
    
    Feature: huawei-pdf-reader, Property 15: 插件验证
    Validates: Requirements 7.1
    """

    @given(manifest=valid_manifest_strategy())
    @settings(max_examples=100)
    def test_valid_plugin_validation_returns_tuple(self, manifest: dict):
        """
        Property 15: 插件验证
        
        验证有效插件时应返回(True, "")元组。
        
        Feature: huawei-pdf-reader, Property 15: 插件验证
        Validates: Requirements 7.1
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            db_path = tmpdir_path / "test.db"
            plugins_dir = tmpdir_path / "plugins"
            plugins_dir.mkdir()
            
            # 创建测试插件目录
            plugin_dir = create_test_plugin_dir(tmpdir_path / "source", manifest)
            
            # 创建插件管理器
            db = Database(db_path)
            manager = PluginManager(db, plugins_dir)
            
            # 验证插件
            is_valid, error = manager.validate_plugin(plugin_dir)
            
            # 验证返回值类型
            assert isinstance(is_valid, bool)
            assert isinstance(error, str)
            
            # 有效插件应返回True和空错误信息
            assert is_valid is True
            assert error == ""

    @given(data=invalid_manifest_missing_field_strategy())
    @settings(max_examples=100)
    def test_invalid_plugin_missing_field_returns_error(self, data):
        """
        Property 15: 插件验证
        
        缺少必需字段的插件应返回(False, 非空错误信息)。
        
        Feature: huawei-pdf-reader, Property 15: 插件验证
        Validates: Requirements 7.1
        """
        manifest, missing_field = data
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            db_path = tmpdir_path / "test.db"
            plugins_dir = tmpdir_path / "plugins"
            plugins_dir.mkdir()
            
            # 创建插件目录（使用临时ID）
            plugin_dir = tmpdir_path / "source" / "test_plugin"
            plugin_dir.mkdir(parents=True)
            
            # 写入不完整的清单
            manifest_path = plugin_dir / "plugin.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            
            # 写入入口点文件
            entry_point = plugin_dir / "main.py"
            entry_point.write_text("# empty plugin", encoding="utf-8")
            
            # 创建插件管理器
            db = Database(db_path)
            manager = PluginManager(db, plugins_dir)
            
            # 验证插件
            is_valid, error = manager.validate_plugin(plugin_dir)
            
            # 验证返回值类型
            assert isinstance(is_valid, bool)
            assert isinstance(error, str)
            
            # 无效插件应返回False和非空错误信息
            assert is_valid is False
            assert error != ""
            assert missing_field in error

    def test_nonexistent_plugin_returns_error(self):
        """
        Property 15: 插件验证
        
        不存在的插件路径应返回(False, 非空错误信息)。
        
        Feature: huawei-pdf-reader, Property 15: 插件验证
        Validates: Requirements 7.1
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            db_path = tmpdir_path / "test.db"
            plugins_dir = tmpdir_path / "plugins"
            plugins_dir.mkdir()
            
            # 创建插件管理器
            db = Database(db_path)
            manager = PluginManager(db, plugins_dir)
            
            # 验证不存在的路径
            nonexistent_path = tmpdir_path / "nonexistent"
            is_valid, error = manager.validate_plugin(nonexistent_path)
            
            # 验证返回值
            assert is_valid is False
            assert error != ""


# ============== Property 16: 插件生命周期 ==============

class TestPluginLifecycle:
    """
    Property 16: 插件生命周期
    
    For any 有效的插件，安装→启用→禁用→卸载的生命周期应正确更新插件状态，
    且每个状态转换后get_installed_plugins应反映正确的状态。
    
    Feature: huawei-pdf-reader, Property 16: 插件生命周期
    Validates: Requirements 7.2, 7.3, 7.4
    """

    @given(manifest=valid_manifest_strategy())
    @settings(max_examples=100)
    def test_plugin_lifecycle_state_transitions(self, manifest: dict):
        """
        Property 16: 插件生命周期
        
        插件生命周期状态转换应正确反映在get_installed_plugins中。
        
        Feature: huawei-pdf-reader, Property 16: 插件生命周期
        Validates: Requirements 7.2, 7.3, 7.4
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            db_path = tmpdir_path / "test.db"
            plugins_dir = tmpdir_path / "plugins"
            plugins_dir.mkdir()
            
            # 创建测试插件
            plugin_dir = create_test_plugin_dir(tmpdir_path / "source", manifest)
            
            # 创建插件管理器
            db = Database(db_path)
            manager = PluginManager(db, plugins_dir)
            
            # 1. 安装插件
            plugin_info = manager.install_plugin(plugin_dir)
            assert plugin_info.id == manifest["id"]
            assert plugin_info.enabled is False
            
            # 验证已安装列表
            installed = manager.get_installed_plugins()
            assert len(installed) == 1
            assert installed[0].id == manifest["id"]
            assert installed[0].enabled is False
            
            # 2. 启用插件
            manager.enable_plugin(manifest["id"])
            
            # 验证状态更新
            plugin = manager.get_plugin(manifest["id"])
            assert plugin is not None
            assert plugin.enabled is True
            assert manager.is_plugin_loaded(manifest["id"]) is True
            
            # 3. 禁用插件
            manager.disable_plugin(manifest["id"])
            
            # 验证状态更新
            plugin = manager.get_plugin(manifest["id"])
            assert plugin is not None
            assert plugin.enabled is False
            assert manager.is_plugin_loaded(manifest["id"]) is False
            
            # 4. 卸载插件
            manager.uninstall_plugin(manifest["id"])
            
            # 验证已卸载
            installed = manager.get_installed_plugins()
            assert len(installed) == 0
            assert manager.get_plugin(manifest["id"]) is None


# ============== Property 17: 插件错误隔离 ==============

class TestPluginErrorIsolation:
    """
    Property 17: 插件错误隔离
    
    For any 执行时抛出异常的插件，Plugin_Manager应捕获异常并返回错误信息，
    主程序应继续正常运行。
    
    Feature: huawei-pdf-reader, Property 17: 插件错误隔离
    Validates: Requirements 7.6
    """

    def test_plugin_load_error_is_isolated(self):
        """
        Property 17: 插件错误隔离
        
        插件加载时抛出的异常应被捕获，不影响主程序。
        
        Feature: huawei-pdf-reader, Property 17: 插件错误隔离
        Validates: Requirements 7.6
        """
        manifest = {
            "id": "error_plugin",
            "name": "Error Plugin",
            "version": "1.0.0",
            "entry_point": "main.py",
            "permissions": [],
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            db_path = tmpdir_path / "test.db"
            plugins_dir = tmpdir_path / "plugins"
            plugins_dir.mkdir()
            
            # 创建会抛出错误的插件
            plugin_dir = create_error_plugin_dir(tmpdir_path / "source", manifest)
            
            # 创建插件管理器
            db = Database(db_path)
            manager = PluginManager(db, plugins_dir)
            
            # 安装插件
            plugin_info = manager.install_plugin(plugin_dir)
            assert plugin_info.id == manifest["id"]
            
            # 启用插件应该抛出异常但被捕获
            with pytest.raises(ValueError) as exc_info:
                manager.enable_plugin(manifest["id"])
            
            # 验证错误信息
            assert "加载插件失败" in str(exc_info.value) or "Plugin load error" in str(exc_info.value)
            
            # 验证主程序仍然正常运行
            installed = manager.get_installed_plugins()
            assert len(installed) == 1
            
            # 验证可以获取错误信息
            error = manager.get_plugin_error(manifest["id"])
            assert error is not None

    def test_sandbox_execute_safely_catches_exceptions(self):
        """
        Property 17: 插件错误隔离
        
        沙箱的execute_safely方法应捕获所有异常。
        
        Feature: huawei-pdf-reader, Property 17: 插件错误隔离
        Validates: Requirements 7.6
        """
        sandbox = PluginSandbox(plugin_id="test_plugin")
        
        # 定义会抛出异常的函数
        def error_func():
            raise RuntimeError("Test error")
        
        # 执行应该不抛出异常
        success, result, error = sandbox.execute_safely(error_func)
        
        # 验证结果
        assert success is False
        assert result is None
        assert error is not None
        assert "RuntimeError" in error
        assert "Test error" in error
        
        # 验证错误计数增加
        assert sandbox.error_count == 1
        assert sandbox.last_error is not None

    @given(error_count=st.integers(min_value=0, max_value=10))
    @settings(max_examples=100)
    def test_sandbox_should_disable_after_max_errors(self, error_count: int):
        """
        Property 17: 插件错误隔离
        
        沙箱在达到最大错误次数后应建议禁用。
        
        Feature: huawei-pdf-reader, Property 17: 插件错误隔离
        Validates: Requirements 7.6
        """
        sandbox = PluginSandbox(plugin_id="test_plugin", max_errors=5)
        sandbox.error_count = error_count
        
        # 验证should_disable逻辑
        if error_count >= 5:
            assert sandbox.should_disable() is True
        else:
            assert sandbox.should_disable() is False


# ============== Property 18: 插件自动加载 ==============

class TestPluginAutoLoad:
    """
    Property 18: 插件自动加载
    
    For any 已启用的插件集合，应用启动后这些插件应全部处于已加载状态。
    
    Feature: huawei-pdf-reader, Property 18: 插件自动加载
    Validates: Requirements 7.7
    """

    @given(manifest=valid_manifest_strategy())
    @settings(max_examples=100)
    def test_enabled_plugins_auto_load_on_startup(self, manifest: dict):
        """
        Property 18: 插件自动加载
        
        已启用的插件在调用load_enabled_plugins后应处于已加载状态。
        
        Feature: huawei-pdf-reader, Property 18: 插件自动加载
        Validates: Requirements 7.7
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            db_path = tmpdir_path / "test.db"
            plugins_dir = tmpdir_path / "plugins"
            plugins_dir.mkdir()
            
            # 创建测试插件
            plugin_dir = create_test_plugin_dir(tmpdir_path / "source", manifest)
            
            # 创建插件管理器并安装启用插件
            db = Database(db_path)
            manager1 = PluginManager(db, plugins_dir)
            
            # 安装并启用插件
            manager1.install_plugin(plugin_dir)
            manager1.enable_plugin(manifest["id"])
            
            # 验证插件已启用
            plugin = manager1.get_plugin(manifest["id"])
            assert plugin is not None
            assert plugin.enabled is True
            
            # 模拟应用重启：创建新的插件管理器
            manager2 = PluginManager(db, plugins_dir)
            
            # 验证插件在数据库中仍然是启用状态
            plugin = manager2.get_plugin(manifest["id"])
            assert plugin is not None
            assert plugin.enabled is True
            
            # 但尚未加载
            assert manager2.is_plugin_loaded(manifest["id"]) is False
            
            # 调用自动加载
            results = manager2.load_enabled_plugins()
            
            # 验证加载结果
            assert manifest["id"] in results
            assert results[manifest["id"]] is None  # None表示成功
            
            # 验证插件已加载
            assert manager2.is_plugin_loaded(manifest["id"]) is True


# ============== PluginAPI 测试 ==============

class TestPluginAPI:
    """PluginAPI功能测试"""

    @given(permissions=permission_strategy)
    @settings(max_examples=100)
    def test_api_permission_check(self, permissions: List[str]):
        """测试API权限检查"""
        api = PluginAPI("test_plugin", permissions)
        
        # 验证拥有的权限
        for perm in permissions:
            assert api.has_permission(perm) is True
        
        # 验证权限列表
        assert set(api.get_permissions()) == set(permissions)

    def test_api_callback_registration_requires_permission(self):
        """测试回调注册需要events权限"""
        # 无events权限
        api_no_perm = PluginAPI("test_plugin", [])
        result = api_no_perm.register_callback("test_event", lambda: None)
        assert result is False
        
        # 有events权限
        api_with_perm = PluginAPI("test_plugin", ["events"])
        result = api_with_perm.register_callback("test_event", lambda: None)
        assert result is True

    def test_api_storage_requires_permission(self):
        """测试存储功能需要storage权限"""
        # 无storage权限
        api_no_perm = PluginAPI("test_plugin", [])
        result = api_no_perm.store_data("key", "value")
        assert result is False
        assert api_no_perm.get_data("key") is None
        
        # 有storage权限
        api_with_perm = PluginAPI("test_plugin", ["storage"])
        result = api_with_perm.store_data("key", "value")
        assert result is True
        assert api_with_perm.get_data("key") == "value"

    def test_api_cleanup(self):
        """测试API清理功能"""
        api = PluginAPI("test_plugin", ["events", "storage"])
        
        # 添加一些数据
        api.register_callback("event1", lambda: None)
        api.store_data("key1", "value1")
        api.log("test message")
        
        # 清理
        api.cleanup()
        
        # 验证已清理
        assert api.get_callbacks("event1") == []
        assert api.get_data("key1") is None
        assert api.get_logs() == []
