"""
华为平板PDF阅读器 - 主题定义

定义深绿色主题和其他UI样式。
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class Theme:
    """UI主题配置"""
    # 主色调
    primary_color: Tuple[float, float, float, float]  # RGBA
    primary_dark: Tuple[float, float, float, float]
    primary_light: Tuple[float, float, float, float]
    
    # 背景色
    background: Tuple[float, float, float, float]
    surface: Tuple[float, float, float, float]
    card: Tuple[float, float, float, float]
    
    # 文字颜色
    text_primary: Tuple[float, float, float, float]
    text_secondary: Tuple[float, float, float, float]
    text_hint: Tuple[float, float, float, float]
    
    # 强调色
    accent: Tuple[float, float, float, float]
    error: Tuple[float, float, float, float]
    success: Tuple[float, float, float, float]
    warning: Tuple[float, float, float, float]
    
    # 边框和分隔线
    divider: Tuple[float, float, float, float]
    border: Tuple[float, float, float, float]
    
    # 导航栏
    nav_background: Tuple[float, float, float, float]
    nav_selected: Tuple[float, float, float, float]
    nav_text: Tuple[float, float, float, float]
    
    # 工具栏
    toolbar_background: Tuple[float, float, float, float]
    toolbar_icon: Tuple[float, float, float, float]
    toolbar_icon_active: Tuple[float, float, float, float]
    
    # 护眼模式滤镜
    eye_protection_tint: Tuple[float, float, float, float]


def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> Tuple[float, float, float, float]:
    """将十六进制颜色转换为RGBA元组 (0-1范围)"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b, alpha)


# 深绿色主题 - 参考StarNote应用风格
DARK_GREEN_THEME = Theme(
    # 主色调 - 深绿色
    primary_color=hex_to_rgba("#1B5E20"),      # 深绿色
    primary_dark=hex_to_rgba("#0D3D14"),       # 更深的绿色
    primary_light=hex_to_rgba("#2E7D32"),      # 浅一点的绿色
    
    # 背景色
    background=hex_to_rgba("#121212"),          # 深色背景
    surface=hex_to_rgba("#1E1E1E"),             # 表面色
    card=hex_to_rgba("#252525"),                # 卡片背景
    
    # 文字颜色
    text_primary=hex_to_rgba("#FFFFFF"),        # 主要文字 - 白色
    text_secondary=hex_to_rgba("#B0B0B0"),      # 次要文字 - 灰色
    text_hint=hex_to_rgba("#757575"),           # 提示文字 - 深灰
    
    # 强调色
    accent=hex_to_rgba("#4CAF50"),              # 强调色 - 亮绿色
    error=hex_to_rgba("#CF6679"),               # 错误色 - 红色
    success=hex_to_rgba("#81C784"),             # 成功色 - 浅绿
    warning=hex_to_rgba("#FFB74D"),             # 警告色 - 橙色
    
    # 边框和分隔线
    divider=hex_to_rgba("#333333"),             # 分隔线
    border=hex_to_rgba("#404040"),              # 边框
    
    # 导航栏
    nav_background=hex_to_rgba("#1B5E20"),      # 导航栏背景 - 深绿
    nav_selected=hex_to_rgba("#2E7D32"),        # 选中项背景
    nav_text=hex_to_rgba("#FFFFFF"),            # 导航文字
    
    # 工具栏
    toolbar_background=hex_to_rgba("#1E1E1E"),  # 工具栏背景
    toolbar_icon=hex_to_rgba("#B0B0B0"),        # 工具栏图标
    toolbar_icon_active=hex_to_rgba("#4CAF50"), # 激活的图标
    
    # 护眼模式滤镜 - 暖色调
    eye_protection_tint=hex_to_rgba("#FFE0B2", 0.15),
)


# 浅色主题（备用）
LIGHT_THEME = Theme(
    primary_color=hex_to_rgba("#2E7D32"),
    primary_dark=hex_to_rgba("#1B5E20"),
    primary_light=hex_to_rgba("#4CAF50"),
    
    background=hex_to_rgba("#FAFAFA"),
    surface=hex_to_rgba("#FFFFFF"),
    card=hex_to_rgba("#FFFFFF"),
    
    text_primary=hex_to_rgba("#212121"),
    text_secondary=hex_to_rgba("#757575"),
    text_hint=hex_to_rgba("#9E9E9E"),
    
    accent=hex_to_rgba("#4CAF50"),
    error=hex_to_rgba("#B00020"),
    success=hex_to_rgba("#4CAF50"),
    warning=hex_to_rgba("#FF9800"),
    
    divider=hex_to_rgba("#E0E0E0"),
    border=hex_to_rgba("#BDBDBD"),
    
    nav_background=hex_to_rgba("#2E7D32"),
    nav_selected=hex_to_rgba("#4CAF50"),
    nav_text=hex_to_rgba("#FFFFFF"),
    
    toolbar_background=hex_to_rgba("#FFFFFF"),
    toolbar_icon=hex_to_rgba("#757575"),
    toolbar_icon_active=hex_to_rgba("#2E7D32"),
    
    eye_protection_tint=hex_to_rgba("#FFE0B2", 0.1),
)


def get_theme(name: str) -> Theme:
    """根据名称获取主题"""
    themes = {
        "dark_green": DARK_GREEN_THEME,
        "light": LIGHT_THEME,
    }
    return themes.get(name, DARK_GREEN_THEME)
