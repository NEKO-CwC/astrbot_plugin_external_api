# rules/keyword_rule.py
from typing import Dict, Any, Optional, Tuple
from .abstract_rule import AbstractRule

class KeywordRule(AbstractRule):
    """关键词规则实现
    
    检查消息是否包含指定的关键词
    """
    
    def _do_match(self, message: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """执行关键词匹配
        
        Args:
            message: 要匹配的消息
            
        Returns:
            Tuple[bool, Optional[Dict]]: 匹配结果和参数
        """
        # 简单检查关键词是否在消息中
        if self.match_pattern in message:
            return True, {}
        return False, None