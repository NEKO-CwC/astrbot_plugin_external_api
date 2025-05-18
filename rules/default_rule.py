# rules/default_rule.py
from typing import Dict, Any, Optional, Tuple
from .abstract_rule import AbstractRule

class DefaultRule(AbstractRule):
    """默认规则实现
    
    总是匹配成功，用作后备选项
    """
    
    def _do_match(self, message: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """执行默认匹配，永远返回成功
        
        Args:
            message: 要匹配的消息
            
        Returns:
            Tuple[bool, Optional[Dict]]: 匹配结果和参数
        """
        # 默认规则总是匹配成功
        return True, {"message": message}