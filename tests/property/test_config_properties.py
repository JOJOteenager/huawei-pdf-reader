"""
配置属性测试

Feature: huawei-pdf-reader, Property 23: 配置往返一致性
Validates: Requirements 10.1-10.7

测试配置对象的序列化和反序列化往返一致性。
"""

import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from hypothesis import given, settings, strategies as st

from huawei_pdf_reader.models import (
    BackupConfig,
    BackupProvider,
    ReadingConfig,
    Settings,
    StylusConfig,
    ToolsConfig,
    TranslationConfig,
)


# ============== 策略定义 ==============

# 页面方向策略
page_direction_strategy = st.sampled_from(["vertical", "horizontal"])

# 工具栏位置策略
toolbar_position_strategy = st.sampled_from(["top", "bottom", "left", "right"])

# 手写笔动作策略
stylus_action_strategy = st.sampled_from([
    "none", "eraser", "select_text", "undo", "redo", 
    "pen", "highlighter", "zoom_in", "zoom_out"
])

# 备份提供商策略
backup_provider_strategy = st.sampled_from([
    BackupProvider.LOCAL, 
    BackupProvider.BAIDU_PAN, 
    BackupProvider.ONEDRIVE
])

# 翻译方向策略
translation_direction_strategy = st.sampled_from(["en_to_zh", "zh_to_en"])

# API提供商策略
api_provider_strategy = st.sampled_from(["baidu", "youdao", "google"])

# 主题策略
theme_strategy = st.sampled_from(["dark_green", "light", "dark", "sepia"])

# 语言策略
language_strategy = st.sampled_from(["zh_CN", "zh_TW", "en_US"])


# 阅读配置策略
@st.composite
def reading_config_strategy(draw):
    return ReadingConfig(
        page_direction=draw(page_direction_strategy),
        dual_page=draw(st.booleans()),
        continuous_scroll=draw(st.booleans()),
        toolbar_position=draw(toolbar_position_strategy),
        eye_protection=draw(st.booleans()),
        keep_screen_on=draw(st.booleans()),
    )


# 手写笔配置策略
@st.composite
def stylus_config_strategy(draw):
    return StylusConfig(
        double_tap=draw(stylus_action_strategy),
        long_press=draw(stylus_action_strategy),
        primary_click=draw(stylus_action_strategy),
        secondary_click=draw(stylus_action_strategy),
        pinch=draw(stylus_action_strategy),
        swipe_up=draw(stylus_action_strategy),
        swipe_down=draw(stylus_action_strategy),
        palm_rejection_sensitivity=draw(st.integers(min_value=1, max_value=10)),
    )


# 工具配置策略
@st.composite
def tools_config_strategy(draw):
    return ToolsConfig(
        shape_recognition=draw(st.booleans()),
        pressure_sensitivity=draw(st.booleans()),
        shape_fill=draw(st.booleans()),
        long_press_select_text=draw(st.booleans()),
        long_press_create_menu=draw(st.booleans()),
    )


# 备份配置策略
@st.composite
def backup_config_strategy(draw):
    return BackupConfig(
        provider=draw(backup_provider_strategy),
        auto_backup=draw(st.booleans()),
        wifi_only=draw(st.booleans()),
        backup_path=draw(st.one_of(st.none(), st.text(min_size=1, max_size=100))),
    )


# 翻译配置策略
@st.composite
def translation_config_strategy(draw):
    return TranslationConfig(
        default_direction=draw(translation_direction_strategy),
        api_provider=draw(api_provider_strategy),
    )


# 完整设置策略
@st.composite
def settings_strategy(draw):
    return Settings(
        theme=draw(theme_strategy),
        language=draw(language_strategy),
        reading=draw(reading_config_strategy()),
        stylus=draw(stylus_config_strategy()),
        tools=draw(tools_config_strategy()),
        backup=draw(backup_config_strategy()),
        translation=draw(translation_config_strategy()),
    )


# ============== 属性测试 ==============

class TestConfigRoundTrip:
    """
    Property 23: 配置往返一致性
    
    For any 有效的配置对象，序列化为JSON后再反序列化应产生等效的配置对象。
    
    Feature: huawei-pdf-reader, Property 23: 配置往返一致性
    Validates: Requirements 10.1-10.7
    """

    @given(config=reading_config_strategy())
    @settings(max_examples=100)
    def test_reading_config_round_trip(self, config: ReadingConfig):
        """阅读配置往返一致性"""
        # 序列化
        data = config.to_dict()
        # 反序列化
        restored = ReadingConfig.from_dict(data)
        
        # 验证所有字段相等
        assert restored.page_direction == config.page_direction
        assert restored.dual_page == config.dual_page
        assert restored.continuous_scroll == config.continuous_scroll
        assert restored.toolbar_position == config.toolbar_position
        assert restored.eye_protection == config.eye_protection
        assert restored.keep_screen_on == config.keep_screen_on

    @given(config=stylus_config_strategy())
    @settings(max_examples=100)
    def test_stylus_config_round_trip(self, config: StylusConfig):
        """手写笔配置往返一致性"""
        data = config.to_dict()
        restored = StylusConfig.from_dict(data)
        
        assert restored.double_tap == config.double_tap
        assert restored.long_press == config.long_press
        assert restored.primary_click == config.primary_click
        assert restored.secondary_click == config.secondary_click
        assert restored.pinch == config.pinch
        assert restored.swipe_up == config.swipe_up
        assert restored.swipe_down == config.swipe_down
        assert restored.palm_rejection_sensitivity == config.palm_rejection_sensitivity

    @given(config=tools_config_strategy())
    @settings(max_examples=100)
    def test_tools_config_round_trip(self, config: ToolsConfig):
        """工具配置往返一致性"""
        data = config.to_dict()
        restored = ToolsConfig.from_dict(data)
        
        assert restored.shape_recognition == config.shape_recognition
        assert restored.pressure_sensitivity == config.pressure_sensitivity
        assert restored.shape_fill == config.shape_fill
        assert restored.long_press_select_text == config.long_press_select_text
        assert restored.long_press_create_menu == config.long_press_create_menu

    @given(config=backup_config_strategy())
    @settings(max_examples=100)
    def test_backup_config_round_trip(self, config: BackupConfig):
        """备份配置往返一致性"""
        data = config.to_dict()
        restored = BackupConfig.from_dict(data)
        
        assert restored.provider == config.provider
        assert restored.auto_backup == config.auto_backup
        assert restored.wifi_only == config.wifi_only
        assert restored.backup_path == config.backup_path

    @given(config=translation_config_strategy())
    @settings(max_examples=100)
    def test_translation_config_round_trip(self, config: TranslationConfig):
        """翻译配置往返一致性"""
        data = config.to_dict()
        restored = TranslationConfig.from_dict(data)
        
        assert restored.default_direction == config.default_direction
        assert restored.api_provider == config.api_provider

    @given(config=settings_strategy())
    @settings(max_examples=100)
    def test_settings_round_trip(self, config: Settings):
        """
        完整设置往返一致性
        
        Property 23: 配置往返一致性
        For any 有效的配置对象，序列化为JSON后再反序列化应产生等效的配置对象。
        
        Feature: huawei-pdf-reader, Property 23: 配置往返一致性
        Validates: Requirements 10.1-10.7
        """
        # 序列化为JSON
        json_str = config.to_json()
        # 反序列化
        restored = Settings.from_json(json_str)
        
        # 验证顶层字段
        assert restored.theme == config.theme
        assert restored.language == config.language
        
        # 验证阅读配置
        assert restored.reading.page_direction == config.reading.page_direction
        assert restored.reading.dual_page == config.reading.dual_page
        assert restored.reading.continuous_scroll == config.reading.continuous_scroll
        assert restored.reading.toolbar_position == config.reading.toolbar_position
        assert restored.reading.eye_protection == config.reading.eye_protection
        assert restored.reading.keep_screen_on == config.reading.keep_screen_on
        
        # 验证手写笔配置
        assert restored.stylus.double_tap == config.stylus.double_tap
        assert restored.stylus.long_press == config.stylus.long_press
        assert restored.stylus.primary_click == config.stylus.primary_click
        assert restored.stylus.secondary_click == config.stylus.secondary_click
        assert restored.stylus.pinch == config.stylus.pinch
        assert restored.stylus.swipe_up == config.stylus.swipe_up
        assert restored.stylus.swipe_down == config.stylus.swipe_down
        assert restored.stylus.palm_rejection_sensitivity == config.stylus.palm_rejection_sensitivity
        
        # 验证工具配置
        assert restored.tools.shape_recognition == config.tools.shape_recognition
        assert restored.tools.pressure_sensitivity == config.tools.pressure_sensitivity
        assert restored.tools.shape_fill == config.tools.shape_fill
        assert restored.tools.long_press_select_text == config.tools.long_press_select_text
        assert restored.tools.long_press_create_menu == config.tools.long_press_create_menu
        
        # 验证备份配置
        assert restored.backup.provider == config.backup.provider
        assert restored.backup.auto_backup == config.backup.auto_backup
        assert restored.backup.wifi_only == config.backup.wifi_only
        assert restored.backup.backup_path == config.backup.backup_path
        
        # 验证翻译配置
        assert restored.translation.default_direction == config.translation.default_direction
        assert restored.translation.api_provider == config.translation.api_provider

    @given(config=settings_strategy())
    @settings(max_examples=100)
    def test_settings_dict_round_trip(self, config: Settings):
        """设置字典往返一致性"""
        # 序列化为字典
        data = config.to_dict()
        # 反序列化
        restored = Settings.from_dict(data)
        
        # 再次序列化并比较
        restored_data = restored.to_dict()
        assert data == restored_data
