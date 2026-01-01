"""
华为平板PDF阅读器 - 备份服务

实现本地和云端备份功能。
"""

import json
import os
import shutil
import zipfile
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import uuid

from huawei_pdf_reader.models import (
    BackupConfig,
    BackupProvider,
    Settings,
)
from huawei_pdf_reader.database import Database


class BackupError(Exception):
    """备份错误"""
    pass


class RestoreError(Exception):
    """恢复错误"""
    pass


class CloudProviderError(Exception):
    """云服务提供商错误"""
    pass


class ICloudProvider(ABC):
    """云服务提供商接口"""
    
    @abstractmethod
    def authenticate(self, credentials: dict) -> bool:
        """认证"""
        pass
    
    @abstractmethod
    def upload(self, local_path: Path, remote_path: str) -> bool:
        """上传文件"""
        pass
    
    @abstractmethod
    def download(self, remote_path: str, local_path: Path) -> bool:
        """下载文件"""
        pass
    
    @abstractmethod
    def list_backups(self) -> List[dict]:
        """列出备份文件"""
        pass
    
    @abstractmethod
    def delete(self, remote_path: str) -> bool:
        """删除文件"""
        pass
    
    @abstractmethod
    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        pass
    
    @abstractmethod
    def logout(self) -> None:
        """登出"""
        pass


class BaiduPanProvider(ICloudProvider):
    """百度网盘提供商"""
    
    def __init__(self):
        self._authenticated = False
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
    
    def authenticate(self, credentials: dict) -> bool:
        """
        认证百度网盘
        
        Args:
            credentials: 包含 access_token 和 refresh_token 的字典
        """
        if "access_token" in credentials:
            self._access_token = credentials["access_token"]
            self._refresh_token = credentials.get("refresh_token")
            self._authenticated = True
            return True
        return False
    
    def upload(self, local_path: Path, remote_path: str) -> bool:
        """上传文件到百度网盘"""
        if not self._authenticated:
            raise CloudProviderError("未认证百度网盘")
        # 实际实现需要调用百度网盘API
        # 这里是模拟实现
        return True
    
    def download(self, remote_path: str, local_path: Path) -> bool:
        """从百度网盘下载文件"""
        if not self._authenticated:
            raise CloudProviderError("未认证百度网盘")
        # 实际实现需要调用百度网盘API
        return True
    
    def list_backups(self) -> List[dict]:
        """列出百度网盘中的备份"""
        if not self._authenticated:
            raise CloudProviderError("未认证百度网盘")
        # 实际实现需要调用百度网盘API
        return []
    
    def delete(self, remote_path: str) -> bool:
        """删除百度网盘中的文件"""
        if not self._authenticated:
            raise CloudProviderError("未认证百度网盘")
        return True
    
    def is_authenticated(self) -> bool:
        return self._authenticated
    
    def logout(self) -> None:
        self._authenticated = False
        self._access_token = None
        self._refresh_token = None


class OneDriveProvider(ICloudProvider):
    """OneDrive提供商"""
    
    def __init__(self):
        self._authenticated = False
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
    
    def authenticate(self, credentials: dict) -> bool:
        """
        认证OneDrive
        
        Args:
            credentials: 包含 access_token 和 refresh_token 的字典
        """
        if "access_token" in credentials:
            self._access_token = credentials["access_token"]
            self._refresh_token = credentials.get("refresh_token")
            self._authenticated = True
            return True
        return False
    
    def upload(self, local_path: Path, remote_path: str) -> bool:
        """上传文件到OneDrive"""
        if not self._authenticated:
            raise CloudProviderError("未认证OneDrive")
        # 实际实现需要调用OneDrive API
        return True
    
    def download(self, remote_path: str, local_path: Path) -> bool:
        """从OneDrive下载文件"""
        if not self._authenticated:
            raise CloudProviderError("未认证OneDrive")
        return True
    
    def list_backups(self) -> List[dict]:
        """列出OneDrive中的备份"""
        if not self._authenticated:
            raise CloudProviderError("未认证OneDrive")
        return []
    
    def delete(self, remote_path: str) -> bool:
        """删除OneDrive中的文件"""
        if not self._authenticated:
            raise CloudProviderError("未认证OneDrive")
        return True
    
    def is_authenticated(self) -> bool:
        return self._authenticated
    
    def logout(self) -> None:
        self._authenticated = False
        self._access_token = None
        self._refresh_token = None


class BackupService:
    """备份服务"""
    
    BACKUP_VERSION = "1.0"
    BACKUP_MANIFEST = "manifest.json"
    
    def __init__(
        self,
        database: Database,
        data_dir: Path,
        backup_dir: Optional[Path] = None,
    ):
        """
        初始化备份服务
        
        Args:
            database: 数据库实例
            data_dir: 应用数据目录
            backup_dir: 备份存储目录（默认为 data_dir/backups）
        """
        self._database = database
        self._data_dir = data_dir
        self._backup_dir = backup_dir or data_dir / "backups"
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        
        self._config = BackupConfig()
        self._cloud_providers: Dict[BackupProvider, ICloudProvider] = {
            BackupProvider.BAIDU_PAN: BaiduPanProvider(),
            BackupProvider.ONEDRIVE: OneDriveProvider(),
        }
        
        self._wifi_connected = True  # 模拟WiFi状态
        self._auto_backup_enabled = False
    
    def set_config(self, config: BackupConfig) -> None:
        """设置备份配置"""
        self._config = config
        self._auto_backup_enabled = config.auto_backup
        if config.backup_path:
            self._backup_dir = Path(config.backup_path)
            self._backup_dir.mkdir(parents=True, exist_ok=True)
    
    def get_config(self) -> BackupConfig:
        """获取备份配置"""
        return self._config
    
    def backup(self, provider: BackupProvider) -> bool:
        """
        执行备份
        
        Args:
            provider: 备份提供商
            
        Returns:
            是否成功
        """
        # 检查WiFi限制
        if self._config.wifi_only and not self._wifi_connected:
            raise BackupError("仅在WiFi下备份，当前无WiFi连接")
        
        if provider == BackupProvider.LOCAL:
            return self._backup_local()
        else:
            return self._backup_cloud(provider)
    
    def restore(self, provider: BackupProvider, backup_id: Optional[str] = None) -> bool:
        """
        恢复备份
        
        Args:
            provider: 备份提供商
            backup_id: 备份ID（本地备份时为文件名）
            
        Returns:
            是否成功
        """
        if provider == BackupProvider.LOCAL:
            return self._restore_local(backup_id)
        else:
            return self._restore_cloud(provider, backup_id)
    
    def _backup_local(self) -> bool:
        """执行本地备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.zip"
        backup_path = self._backup_dir / backup_name
        
        try:
            # 创建临时目录
            temp_dir = self._backup_dir / f"temp_{timestamp}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # 导出数据库数据
            self._export_database(temp_dir)
            
            # 导出设置
            self._export_settings(temp_dir)
            
            # 创建清单文件
            manifest = {
                "version": self.BACKUP_VERSION,
                "created_at": datetime.now().isoformat(),
                "app_version": "1.0.0",
                "contents": ["database.json", "settings.json"],
            }
            manifest_path = temp_dir / self.BACKUP_MANIFEST
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
            
            # 创建ZIP文件
            with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_path in temp_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(temp_dir)
                        zf.write(file_path, arcname)
            
            # 清理临时目录
            shutil.rmtree(temp_dir)
            
            return True
            
        except Exception as e:
            # 清理临时文件
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            if backup_path.exists():
                backup_path.unlink()
            raise BackupError(f"本地备份失败: {str(e)}")
    
    def _restore_local(self, backup_id: Optional[str] = None) -> bool:
        """恢复本地备份"""
        # 如果未指定备份ID，使用最新的备份
        if backup_id is None:
            backups = self.list_local_backups()
            if not backups:
                raise RestoreError("没有可用的本地备份")
            backup_id = backups[0]["filename"]
        
        backup_path = self._backup_dir / backup_id
        if not backup_path.exists():
            raise RestoreError(f"备份文件不存在: {backup_id}")
        
        try:
            # 创建临时目录
            temp_dir = self._backup_dir / f"restore_{uuid.uuid4().hex[:8]}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # 解压备份
            with zipfile.ZipFile(backup_path, "r") as zf:
                zf.extractall(temp_dir)
            
            # 验证清单
            manifest_path = temp_dir / self.BACKUP_MANIFEST
            if not manifest_path.exists():
                raise RestoreError("无效的备份文件：缺少清单")
            
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            
            # 恢复数据库
            self._import_database(temp_dir)
            
            # 恢复设置
            self._import_settings(temp_dir)
            
            # 清理临时目录
            shutil.rmtree(temp_dir)
            
            return True
            
        except RestoreError:
            raise
        except Exception as e:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise RestoreError(f"恢复备份失败: {str(e)}")
    
    def _backup_cloud(self, provider: BackupProvider) -> bool:
        """执行云备份"""
        cloud_provider = self._cloud_providers.get(provider)
        if not cloud_provider:
            raise BackupError(f"不支持的云服务提供商: {provider}")
        
        if not cloud_provider.is_authenticated():
            raise BackupError(f"未绑定{provider.value}账号")
        
        # 先创建本地备份
        self._backup_local()
        
        # 获取最新的本地备份
        backups = self.list_local_backups()
        if not backups:
            raise BackupError("创建本地备份失败")
        
        latest_backup = backups[0]
        local_path = self._backup_dir / latest_backup["filename"]
        remote_path = f"huawei_pdf_reader/{latest_backup['filename']}"
        
        # 上传到云端
        return cloud_provider.upload(local_path, remote_path)
    
    def _restore_cloud(self, provider: BackupProvider, backup_id: Optional[str] = None) -> bool:
        """恢复云备份"""
        cloud_provider = self._cloud_providers.get(provider)
        if not cloud_provider:
            raise BackupError(f"不支持的云服务提供商: {provider}")
        
        if not cloud_provider.is_authenticated():
            raise BackupError(f"未绑定{provider.value}账号")
        
        # 列出云端备份
        cloud_backups = cloud_provider.list_backups()
        if not cloud_backups:
            raise RestoreError("云端没有可用的备份")
        
        # 选择要恢复的备份
        if backup_id:
            remote_path = f"huawei_pdf_reader/{backup_id}"
        else:
            remote_path = cloud_backups[0].get("path", "")
        
        # 下载到本地
        local_path = self._backup_dir / f"cloud_restore_{uuid.uuid4().hex[:8]}.zip"
        if not cloud_provider.download(remote_path, local_path):
            raise RestoreError("下载云端备份失败")
        
        # 恢复本地备份
        try:
            return self._restore_local(local_path.name)
        finally:
            # 清理下载的文件
            if local_path.exists():
                local_path.unlink()
    
    def _export_database(self, target_dir: Path) -> None:
        """导出数据库数据到JSON"""
        data = {
            "documents": [],
            "folders": [],
            "tags": [],
            "annotations": [],
            "bookmarks": [],
            "plugins": [],
        }
        
        # 导出文档
        docs = self._database.get_documents(include_deleted=True)
        data["documents"] = [doc.to_dict() for doc in docs]
        
        # 导出文件夹
        folders = self._database.get_folders()
        data["folders"] = [folder.to_dict() for folder in folders]
        
        # 导出标签
        tags = self._database.get_all_tags()
        data["tags"] = [tag.to_dict() for tag in tags]
        
        # 导出注释（需要遍历所有文档）
        for doc in docs:
            annotations = self._database.get_annotations(doc.id)
            for ann in annotations:
                ann_data = ann.to_dict()
                ann_data["document_id"] = doc.id
                data["annotations"].append(ann_data)
        
        # 导出书签
        for doc in docs:
            bookmarks = self._database.get_bookmarks(doc.id)
            data["bookmarks"].extend([bm.to_dict() for bm in bookmarks])
        
        # 导出插件
        plugins = self._database.get_all_plugins()
        data["plugins"] = [plugin.to_dict() for plugin in plugins]
        
        # 写入文件
        db_path = target_dir / "database.json"
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _export_settings(self, target_dir: Path) -> None:
        """导出设置"""
        settings = self._database.load_settings()
        settings_path = target_dir / "settings.json"
        with open(settings_path, "w", encoding="utf-8") as f:
            f.write(settings.to_json())
    
    def _import_database(self, source_dir: Path) -> None:
        """从JSON导入数据库数据"""
        db_path = source_dir / "database.json"
        if not db_path.exists():
            return
        
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 导入文件夹
        from huawei_pdf_reader.models import Folder, Tag, DocumentEntry, Annotation, Bookmark, PluginInfo
        
        for folder_data in data.get("folders", []):
            folder = Folder.from_dict(folder_data)
            try:
                self._database.add_folder(folder)
            except Exception:
                pass  # 忽略重复
        
        # 导入标签
        for tag_data in data.get("tags", []):
            tag = Tag.from_dict(tag_data)
            try:
                self._database.add_tag(tag)
            except Exception:
                pass
        
        # 导入文档
        for doc_data in data.get("documents", []):
            doc = DocumentEntry.from_dict(doc_data)
            try:
                self._database.add_document(doc)
            except Exception:
                pass
        
        # 导入注释
        for ann_data in data.get("annotations", []):
            doc_id = ann_data.pop("document_id", None)
            if doc_id:
                ann = Annotation.from_dict(ann_data)
                try:
                    self._database.save_annotation(doc_id, ann)
                except Exception:
                    pass
        
        # 导入书签
        for bm_data in data.get("bookmarks", []):
            bm = Bookmark.from_dict(bm_data)
            try:
                self._database.add_bookmark(bm)
            except Exception:
                pass
        
        # 导入插件
        for plugin_data in data.get("plugins", []):
            plugin = PluginInfo.from_dict(plugin_data)
            try:
                self._database.add_plugin(plugin)
            except Exception:
                pass
    
    def _import_settings(self, source_dir: Path) -> None:
        """导入设置"""
        settings_path = source_dir / "settings.json"
        if not settings_path.exists():
            return
        
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = Settings.from_json(f.read())
        
        self._database.save_settings(settings)
    
    def list_local_backups(self) -> List[dict]:
        """列出本地备份"""
        backups = []
        for file_path in self._backup_dir.glob("backup_*.zip"):
            stat = file_path.stat()
            backups.append({
                "filename": file_path.name,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        
        # 按时间倒序排列
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups
    
    def delete_local_backup(self, backup_id: str) -> bool:
        """删除本地备份"""
        backup_path = self._backup_dir / backup_id
        if backup_path.exists():
            backup_path.unlink()
            return True
        return False
    
    def bind_account(self, provider: BackupProvider, credentials: dict) -> bool:
        """
        绑定云账号
        
        Args:
            provider: 云服务提供商
            credentials: 认证凭据
            
        Returns:
            是否成功
        """
        if provider == BackupProvider.LOCAL:
            raise CloudProviderError("本地备份不需要绑定账号")
        
        cloud_provider = self._cloud_providers.get(provider)
        if not cloud_provider:
            raise CloudProviderError(f"不支持的云服务提供商: {provider}")
        
        return cloud_provider.authenticate(credentials)
    
    def unbind_account(self, provider: BackupProvider) -> None:
        """
        解绑云账号
        
        Args:
            provider: 云服务提供商
        """
        if provider == BackupProvider.LOCAL:
            return
        
        cloud_provider = self._cloud_providers.get(provider)
        if cloud_provider:
            cloud_provider.logout()
    
    def is_account_bound(self, provider: BackupProvider) -> bool:
        """检查云账号是否已绑定"""
        if provider == BackupProvider.LOCAL:
            return True
        
        cloud_provider = self._cloud_providers.get(provider)
        return cloud_provider.is_authenticated() if cloud_provider else False
    
    def set_wifi_status(self, connected: bool) -> None:
        """设置WiFi连接状态（用于测试）"""
        self._wifi_connected = connected
    
    def should_auto_backup(self) -> bool:
        """检查是否应该执行自动备份"""
        if not self._config.auto_backup:
            return False
        
        if self._config.wifi_only and not self._wifi_connected:
            return False
        
        return True
    
    def auto_backup(self) -> bool:
        """执行自动备份"""
        if not self.should_auto_backup():
            return False
        
        return self.backup(self._config.provider)
