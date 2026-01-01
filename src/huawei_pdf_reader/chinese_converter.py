"""
华为平板PDF阅读器 - 繁简转换器

使用 OpenCC 实现繁体中文和简体中文之间的转换。
"""

from abc import ABC, abstractmethod
from typing import Optional
import unicodedata

try:
    from opencc import OpenCC
except ImportError:
    OpenCC = None

from .models import ConversionDirection


class IChineseConverter(ABC):
    """中文转换器接口"""
    
    @abstractmethod
    def convert(self, text: str, direction: ConversionDirection) -> str:
        """转换文本"""
        pass
    
    @abstractmethod
    def is_traditional(self, char: str) -> bool:
        """判断是否为繁体字"""
        pass


class ChineseConverter(IChineseConverter):
    """
    中文转换器实现
    
    使用 OpenCC 库进行繁简转换。
    - 繁转简 (t2s): 繁体中文 -> 简体中文
    - 简转繁 (s2t): 简体中文 -> 繁体中文
    
    Requirements: 6.1, 6.2, 6.4
    """
    
    def __init__(self):
        """初始化转换器"""
        if OpenCC is None:
            raise ImportError(
                "OpenCC library is not installed. "
                "Please install it with: pip install opencc-python-reimplemented"
            )
        
        # 创建转换器实例
        # t2s: Traditional Chinese to Simplified Chinese
        # s2t: Simplified Chinese to Traditional Chinese
        self._t2s_converter = OpenCC('t2s')
        self._s2t_converter = OpenCC('s2t')
        
        # 常见繁体字集合（用于快速判断）
        # 这些是一些常见的繁体字，用于 is_traditional 方法
        self._traditional_chars = self._build_traditional_char_set()
    
    def _build_traditional_char_set(self) -> set:
        """构建繁体字集合"""
        # 常见繁体字样本
        traditional_samples = (
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
            "網路網站網頁網絡網際網民網友網購網紅"
            "開始開放開發開展開創開拓開闢開設開辦"
            "發展發現發明發生發布發表發行發揮發動"
            "設計設備設施設置設定設立設想設法設身"
            "圖片圖書圖表圖案圖像圖形圖畫圖示圖解"
            "館藏館員館長館內館外館舍館址館名館史"
            "歷史歷程歷屆歷年歷來歷經歷任歷代歷時"
            "經濟經驗經過經常經典經營經理經費經歷"
            "體系體制體現體會體驗體育體質體積體面"
            "驗證驗收驗血驗屍驗明驗算驗貨驗傷驗光"
            "實際實現實驗實踐實質實體實用實力實情"
            "環境環節環繞環保環球環顧環視環抱環行"
            "資訊資料資源資金資產資格資助資深資歷"
            "處理處置處分處罰處境處於處方處事處世"
            "數據數字數量數目數學數值數碼數位數額"
            "庫存庫房庫藏庫容庫區庫款庫銀庫管庫務"
            "應該應用應對應付應急應變應答應聘應徵"
            "認識認為認定認可認真認同認知認證認領"
            "問題問答問候問好問世問津問鼎問罪問責"
            "關係關於關心關注關鍵關閉關聯關懷關照"
            "變化變動變更變革變遷變形變質變異變態"
            "過程過去過來過度過渡過濾過問過失過錯"
            "結構結果結束結合結論結算結餘結晶結緣"
            "組織組成組合組建組裝組團組閣組員組長"
            "機構機關機會機制機器機械機能機密機遇"
            "運動運行運用運作運輸運營運算運轉運氣"
            "動態動作動力動機動員動向動靜動搖動盪"
            "傳統傳播傳遞傳達傳說傳承傳授傳染傳真"
            "現實現在現代現象現場現狀現金現行現有"
        )
        return set(traditional_samples)
    
    def convert(self, text: str, direction: ConversionDirection) -> str:
        """
        转换文本
        
        Args:
            text: 要转换的文本
            direction: 转换方向 (TRADITIONAL_TO_SIMPLIFIED 或 SIMPLIFIED_TO_TRADITIONAL)
        
        Returns:
            转换后的文本
        
        Requirements: 6.1, 6.2, 6.4
        - 繁体转简体
        - 简体转繁体
        - 保持非中文字符不变
        """
        if not text:
            return text
        
        if direction == ConversionDirection.TRADITIONAL_TO_SIMPLIFIED:
            return self._t2s_converter.convert(text)
        elif direction == ConversionDirection.SIMPLIFIED_TO_TRADITIONAL:
            return self._s2t_converter.convert(text)
        else:
            raise ValueError(f"Unknown conversion direction: {direction}")
    
    def is_traditional(self, char: str) -> bool:
        """
        判断是否为繁体字
        
        Args:
            char: 单个字符
        
        Returns:
            如果是繁体字返回 True，否则返回 False
        
        Note:
            这个方法通过比较字符转换前后是否相同来判断。
            如果一个字符转换为简体后发生变化，则认为它是繁体字。
        """
        if not char or len(char) != 1:
            return False
        
        # 检查是否是中文字符
        if not self._is_chinese_char(char):
            return False
        
        # 通过转换来判断：如果繁转简后字符改变，说明原字符是繁体
        simplified = self._t2s_converter.convert(char)
        return simplified != char
    
    def _is_chinese_char(self, char: str) -> bool:
        """判断是否为中文字符"""
        if not char:
            return False
        
        # 使用 Unicode 范围判断
        code_point = ord(char)
        
        # CJK Unified Ideographs (中日韩统一表意文字)
        if 0x4E00 <= code_point <= 0x9FFF:
            return True
        
        # CJK Unified Ideographs Extension A
        if 0x3400 <= code_point <= 0x4DBF:
            return True
        
        # CJK Unified Ideographs Extension B
        if 0x20000 <= code_point <= 0x2A6DF:
            return True
        
        # CJK Compatibility Ideographs
        if 0xF900 <= code_point <= 0xFAFF:
            return True
        
        return False
    
    def is_simplified(self, char: str) -> bool:
        """
        判断是否为简体字
        
        Args:
            char: 单个字符
        
        Returns:
            如果是简体字返回 True，否则返回 False
        """
        if not char or len(char) != 1:
            return False
        
        if not self._is_chinese_char(char):
            return False
        
        # 如果不是繁体字，且是中文字符，则认为是简体字
        return not self.is_traditional(char)
    
    def detect_text_type(self, text: str) -> str:
        """
        检测文本类型
        
        Args:
            text: 要检测的文本
        
        Returns:
            "traditional" - 主要是繁体
            "simplified" - 主要是简体
            "mixed" - 混合
            "non_chinese" - 非中文
        """
        if not text:
            return "non_chinese"
        
        traditional_count = 0
        simplified_count = 0
        
        for char in text:
            if self._is_chinese_char(char):
                if self.is_traditional(char):
                    traditional_count += 1
                else:
                    simplified_count += 1
        
        total = traditional_count + simplified_count
        
        if total == 0:
            return "non_chinese"
        
        traditional_ratio = traditional_count / total
        
        if traditional_ratio > 0.8:
            return "traditional"
        elif traditional_ratio < 0.2:
            return "simplified"
        else:
            return "mixed"
