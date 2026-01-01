# 华为平板PDF阅读器

适用于华为平板的PDF阅读器软件，支持PDF和Word文档阅读、华为手写笔注释、防误触、区域翻译（英汉互译）、繁简转换以及插件扩展功能。

## 功能特性

- **文档阅读**: 支持PDF和Word文档的流畅阅读
- **手写笔注释**: 支持华为手写笔，多种笔工具和压感
- **防误触**: 智能识别手掌和笔尖输入
- **放大镜工具**: 区域选择、翻译和繁简转换
- **文件管理**: 文档库组织、搜索、标签
- **插件系统**: 可扩展的插件架构
- **云备份**: 支持百度网盘和OneDrive

## 安装

```bash
# 克隆项目
git clone <repository-url>
cd huawei_pdf_reader

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -e ".[dev]"
```

## 运行

```bash
# 运行应用（GUI模式）
python -m huawei_pdf_reader.main

# 运行应用（无头模式，用于测试）
python -m huawei_pdf_reader.main --headless

# 打开指定文档
python -m huawei_pdf_reader.main /path/to/document.pdf

# 显示版本信息
python -m huawei_pdf_reader.main --version
```

## Android 打包

### 前置条件

1. Linux 或 WSL 环境（Windows 不直接支持 Buildozer）
2. Python 3.10+
3. Java JDK 17+

### 安装 Buildozer

```bash
pip install buildozer cython==0.29.36
```

### 构建 APK

```bash
# 检查构建环境
python build_android.py check

# 构建 debug 版本
python build_android.py debug

# 构建 release 版本
python build_android.py release

# 或直接使用 buildozer
buildozer -v android debug
```

### 部署到设备

```bash
# 部署并运行
buildozer android deploy run logcat

# 或使用脚本
python build_android.py deploy
```

### 华为平板优化

- 支持 arm64-v8a 和 armeabi-v7a 架构
- 针对大屏幕平板优化布局
- 支持华为手写笔输入
- 深绿色主题设计

### GitHub Actions 自动构建

项目配置了 GitHub Actions 工作流，会在以下情况自动构建 APK：

- Push 到 main 或 develop 分支
- 创建 Pull Request
- 创建版本标签（v*）

构建产物可在 Actions 页面下载。

## 开发

```bash
# 运行测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=src/huawei_pdf_reader --cov-report=html

# 运行属性测试
pytest tests/property/

# 代码格式化
black src/ tests/
isort src/ tests/

# 类型检查
mypy src/
```

## 项目结构

```
huawei_pdf_reader/
├── src/
│   └── huawei_pdf_reader/
│       ├── __init__.py
│       ├── main.py            # 主入口
│       ├── app.py             # 应用容器和依赖注入
│       ├── models.py          # 数据模型
│       ├── database.py        # 数据库操作
│       ├── document_processor.py
│       ├── annotation_engine.py
│       ├── palm_rejection.py
│       ├── magnifier.py
│       ├── translation_service.py
│       ├── chinese_converter.py
│       ├── plugin_manager.py
│       ├── file_manager.py
│       ├── backup_service.py
│       └── ui/                # UI 组件
│           ├── main_window.py
│           ├── reader_view.py
│           ├── file_manager_view.py
│           ├── settings_view.py
│           ├── annotation_tools.py
│           ├── magnifier_widget.py
│           └── theme.py
├── tests/
│   ├── unit/
│   ├── property/
│   └── integration/
├── buildozer.spec             # Android 打包配置
├── build_android.py           # Android 打包脚本
├── pyproject.toml
├── requirements.txt
└── README.md
```

## 许可证

MIT License
