# rules/command_rule.py
from typing import Dict, Any, Optional, Tuple
from .abstract_rule import AbstractRule

class CommandRule(AbstractRule):
    """命令规则实现
    
    检查消息是否以指定命令开头（完全匹配命令）
    """
    
    def _do_match(self, message: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """执行命令匹配
        
        Args:
            message: 要匹配的消息
            
        Returns:
            Tuple[bool, Optional[Dict]]: 匹配结果和参数
        """
        # 检查消息是否以命令开头
        command = self.match_pattern
        
        # 完全匹配或者以空格分隔（命令和参数）
        if message == command or message.startswith(command + " "):
            # 提取命令后的内容作为参数
            content = message[len(command):].strip()
            return True, {"content": content}
        return False, None