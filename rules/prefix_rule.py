# rules/prefix_rule.py
from typing import Dict, Any, Optional, Tuple
from .abstract_rule import AbstractRule

class PrefixRule(AbstractRule):
    """前缀规则实现
    
    检查消息是否以指定前缀开头（不要求完全匹配）
    """
    
    def _do_match(self, message: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """执行前缀匹配
        
        Args:
            message: 要匹配的消息
            
        Returns:
            Tuple[bool, Optional[Dict]]: 匹配结果和参数
        """
        prefix = self.match_pattern
        if message.startswith(prefix):
            # 提取前缀后的内容作为参数
            content = message[len(prefix):].strip()
            return True, {"content": content}
        return False, None