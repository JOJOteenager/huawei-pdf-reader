"""
繁简转换器属性测试

Feature: huawei-pdf-reader
Property 12: 繁简转换正确性
Property 13: 繁简转换不变性
Property 14: 繁简转换往返一致性
Validates: Requirements 6.1, 6.2, 6.4, 6.5

测试繁简转换器的正确性、不变性和往返一致性。
"""

import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from hypothesis import given, settings, strategies as st, assume

from huawei_pdf_reader.chinese_converter import ChineseConverter
from huawei_pdf_reader.models import ConversionDirection


# ============== 策略定义 ==============

# 繁体中文字符策略 - 常见繁体字
traditional_chars = (
    "國語學習機電腦網絡開發設計圖書館歷史經濟"
    "體驗實際環境資訊處理數據庫應該認識問題"
    "關係發展變化過程結構組織機構運動動態"
    "傳統現實實現實驗實際實踐實質實體實用"
    "廣東廣州廣場廣告廣播廣泛廣義廣大廣闊"
    "臺灣臺北臺中臺南臺東臺商臺幣臺語臺風"
    "東亞東京東方東部東西東南東北東邊東道"
    "書籍書本書店書法書信書面書寫書記書畫"
    "學術學校學生學習學者學問學科學位學歷"
    "語言語文語法語氣語調語音語義語境語種"
    "電話電視電影電腦電子電力電氣電器電路"
)

# 简体中文字符策略 - 常见简体字
simplified_chars = (
    "国语学习机电脑网络开发设计图书馆历史经济"
    "体验实际环境资讯处理数据库应该认识问题"
    "关系发展变化过程结构组织机构运动动态"
    "传统现实实现实验实际实践实质实体实用"
    "广东广州广场广告广播广泛广义广大广阔"
    "台湾台北台中台南台东台商台币台语台风"
    "东亚东京东方东部东西东南东北东边东道"
    "书籍书本书店书法书信书面书写书记书画"
    "学术学校学生学习学者学问学科学位学历"
    "语言语文语法语气语调语音语义语境语种"
    "电话电视电影电脑电子电力电气电器电路"
)

# 非中文字符策略 - 英文、数字、标点
non_chinese_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;':\",./<>? "

# 繁体文本策略
@st.composite
def traditional_text_strategy(draw):
    """生成繁体中文文本"""
    length = draw(st.integers(min_value=1, max_value=50))
    chars = [draw(st.sampled_from(list(traditional_chars))) for _ in range(length)]
    return "".join(chars)

# 简体文本策略
@st.composite
def simplified_text_strategy(draw):
    """生成简体中文文本"""
    length = draw(st.integers(min_value=1, max_value=50))
    chars = [draw(st.sampled_from(list(simplified_chars))) for _ in range(length)]
    return "".join(chars)

# 非中文文本策略
@st.composite
def non_chinese_text_strategy(draw):
    """生成非中文文本（英文、数字、标点）"""
    length = draw(st.integers(min_value=1, max_value=50))
    chars = [draw(st.sampled_from(list(non_chinese_chars))) for _ in range(length)]
    return "".join(chars)

# 混合文本策略（繁体 + 非中文）
@st.composite
def mixed_traditional_text_strategy(draw):
    """生成混合文本（繁体中文 + 非中文字符）"""
    parts = []
    num_parts = draw(st.integers(min_value=2, max_value=6))
    for i in range(num_parts):
        if i % 2 == 0:
            # 繁体中文部分
            length = draw(st.integers(min_value=1, max_value=10))
            chars = [draw(st.sampled_from(list(traditional_chars))) for _ in range(length)]
            parts.append("".join(chars))
        else:
            # 非中文部分
            length = draw(st.integers(min_value=1, max_value=10))
            chars = [draw(st.sampled_from(list(non_chinese_chars))) for _ in range(length)]
            parts.append("".join(chars))
    return "".join(parts)


# ============== 属性测试 ==============

class TestChineseConverterCorrectness:
    """
    Property 12: 繁简转换正确性
    
    For any 包含繁体中文的文本，转换后的文本长度应与原文本相同，
    且所有繁体字符应被转换为对应的简体字符。
    
    Feature: huawei-pdf-reader, Property 12: 繁简转换正确性
    Validates: Requirements 6.1, 6.2
    """

    def setup_method(self):
        """每个测试方法前初始化转换器"""
        self.converter = ChineseConverter()

    @given(text=traditional_text_strategy())
    @settings(max_examples=100)
    def test_traditional_to_simplified_length_preserved(self, text: str):
        """
        Property 12: 繁简转换正确性 - 长度保持
        
        繁体转简体后，文本长度应保持不变。
        
        Feature: huawei-pdf-reader, Property 12: 繁简转换正确性
        Validates: Requirements 6.1, 6.2
        """
        result = self.converter.convert(text, ConversionDirection.TRADITIONAL_TO_SIMPLIFIED)
        assert len(result) == len(text), f"Length mismatch: {len(result)} != {len(text)}"

    @given(text=traditional_text_strategy())
    @settings(max_examples=100)
    def test_traditional_to_simplified_all_converted(self, text: str):
        """
        Property 12: 繁简转换正确性 - 全部转换
        
        繁体转简体后，结果中不应包含原始繁体字符（除非繁简相同）。
        
        Feature: huawei-pdf-reader, Property 12: 繁简转换正确性
        Validates: Requirements 6.1, 6.2
        """
        result = self.converter.convert(text, ConversionDirection.TRADITIONAL_TO_SIMPLIFIED)
        
        # 验证结果中的每个字符都不是繁体字
        for char in result:
            assert not self.converter.is_traditional(char), \
                f"Character '{char}' is still traditional after conversion"


class TestChineseConverterInvariance:
    """
    Property 13: 繁简转换不变性
    
    For any 包含非中文字符（英文、数字、标点）的文本，
    这些字符在转换后应保持不变。
    
    Feature: huawei-pdf-reader, Property 13: 繁简转换不变性
    Validates: Requirements 6.4
    """

    def setup_method(self):
        """每个测试方法前初始化转换器"""
        self.converter = ChineseConverter()

    @given(text=non_chinese_text_strategy())
    @settings(max_examples=100)
    def test_non_chinese_unchanged_t2s(self, text: str):
        """
        Property 13: 繁简转换不变性 - 繁转简
        
        非中文字符在繁转简后应保持不变。
        
        Feature: huawei-pdf-reader, Property 13: 繁简转换不变性
        Validates: Requirements 6.4
        """
        result = self.converter.convert(text, ConversionDirection.TRADITIONAL_TO_SIMPLIFIED)
        assert result == text, f"Non-Chinese text changed: '{text}' -> '{result}'"

    @given(text=non_chinese_text_strategy())
    @settings(max_examples=100)
    def test_non_chinese_unchanged_s2t(self, text: str):
        """
        Property 13: 繁简转换不变性 - 简转繁
        
        非中文字符在简转繁后应保持不变。
        
        Feature: huawei-pdf-reader, Property 13: 繁简转换不变性
        Validates: Requirements 6.4
        """
        result = self.converter.convert(text, ConversionDirection.SIMPLIFIED_TO_TRADITIONAL)
        assert result == text, f"Non-Chinese text changed: '{text}' -> '{result}'"

    @given(text=mixed_traditional_text_strategy())
    @settings(max_examples=100)
    def test_mixed_text_non_chinese_preserved(self, text: str):
        """
        Property 13: 繁简转换不变性 - 混合文本
        
        混合文本中的非中文字符在转换后应保持不变。
        
        Feature: huawei-pdf-reader, Property 13: 繁简转换不变性
        Validates: Requirements 6.4
        """
        result = self.converter.convert(text, ConversionDirection.TRADITIONAL_TO_SIMPLIFIED)
        
        # 验证非中文字符保持不变
        for i, (orig_char, result_char) in enumerate(zip(text, result)):
            if orig_char in non_chinese_chars:
                assert orig_char == result_char, \
                    f"Non-Chinese char at position {i} changed: '{orig_char}' -> '{result_char}'"


class TestChineseConverterRoundTrip:
    """
    Property 14: 繁简转换往返一致性
    
    For any 有效的简体中文文本，转换为繁体再转换回简体应产生等效的原始文本。
    
    Feature: huawei-pdf-reader, Property 14: 繁简转换往返一致性
    Validates: Requirements 6.5
    """

    def setup_method(self):
        """每个测试方法前初始化转换器"""
        self.converter = ChineseConverter()

    @given(text=simplified_text_strategy())
    @settings(max_examples=100)
    def test_simplified_round_trip(self, text: str):
        """
        Property 14: 繁简转换往返一致性 - 简体往返
        
        简体 -> 繁体 -> 简体 应产生等效的原始文本。
        
        Feature: huawei-pdf-reader, Property 14: 繁简转换往返一致性
        Validates: Requirements 6.5
        """
        # 简体 -> 繁体
        traditional = self.converter.convert(text, ConversionDirection.SIMPLIFIED_TO_TRADITIONAL)
        # 繁体 -> 简体
        back_to_simplified = self.converter.convert(traditional, ConversionDirection.TRADITIONAL_TO_SIMPLIFIED)
        
        assert back_to_simplified == text, \
            f"Round trip failed: '{text}' -> '{traditional}' -> '{back_to_simplified}'"

    @given(text=traditional_text_strategy())
    @settings(max_examples=100)
    def test_traditional_round_trip(self, text: str):
        """
        Property 14: 繁简转换往返一致性 - 繁体往返
        
        繁体 -> 简体 -> 繁体 应产生语义等效的文本。
        
        Note: 由于中文字符的特殊性，某些繁体字有多个变体映射到同一个简体字
        （如 歷/曆 -> 历 -> 曆），因此我们验证的是：
        1. 往返后的文本长度相同
        2. 往返后的文本再次转换为简体应与第一次转换结果相同（语义等效）
        
        Feature: huawei-pdf-reader, Property 14: 繁简转换往返一致性
        Validates: Requirements 6.5
        """
        # 繁体 -> 简体
        simplified = self.converter.convert(text, ConversionDirection.TRADITIONAL_TO_SIMPLIFIED)
        # 简体 -> 繁体
        back_to_traditional = self.converter.convert(simplified, ConversionDirection.SIMPLIFIED_TO_TRADITIONAL)
        # 再次转换为简体（验证语义等效）
        simplified_again = self.converter.convert(back_to_traditional, ConversionDirection.TRADITIONAL_TO_SIMPLIFIED)
        
        # 验证长度保持不变
        assert len(back_to_traditional) == len(text), \
            f"Length mismatch: {len(back_to_traditional)} != {len(text)}"
        
        # 验证语义等效：两次转换为简体的结果应相同
        assert simplified_again == simplified, \
            f"Semantic equivalence failed: '{text}' -> '{simplified}' -> '{back_to_traditional}' -> '{simplified_again}'"

    @given(text=non_chinese_text_strategy())
    @settings(max_examples=100)
    def test_non_chinese_round_trip(self, text: str):
        """
        Property 14: 繁简转换往返一致性 - 非中文往返
        
        非中文文本往返转换后应保持不变。
        
        Feature: huawei-pdf-reader, Property 14: 繁简转换往返一致性
        Validates: Requirements 6.4, 6.5
        """
        # 繁转简再简转繁
        step1 = self.converter.convert(text, ConversionDirection.TRADITIONAL_TO_SIMPLIFIED)
        step2 = self.converter.convert(step1, ConversionDirection.SIMPLIFIED_TO_TRADITIONAL)
        
        assert step2 == text, f"Non-Chinese round trip failed: '{text}' -> '{step1}' -> '{step2}'"
