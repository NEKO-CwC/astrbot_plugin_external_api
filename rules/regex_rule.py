# rules/regex_rule.py
import re
from typing import Dict, Any, Optional, Tuple
from .abstract_rule import AbstractRule

class RegexRule(AbstractRule):
    """正则表达式规则实现
    
    使用正则表达式匹配消息内容，并提取捕获组作为参数
    """
    
    def parse_rule_config(self):
        """解析规则配置"""
        super().parse_rule_config()
        
        # 预编译正则表达式以提高性能
        try:
            self.regex_pattern = re.compile(self.match_pattern)
        except re.error as e:
            raise ValueError(f"无效的正则表达式 '{self.match_pattern}': {str(e)}")
    
    def _do_match(self, message: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """执行正则表达式匹配
        
        Args:
            message: 要匹配的消息
            
        Returns:
            Tuple[bool, Optional[Dict]]: 匹配结果和捕获组
        """
        match = self.regex_pattern.match(message)
        if not match:
            return False, None
        
        # 提取正则捕获组
        params = {}
        for i, group in enumerate(match.groups(), 1):
            if group is not None:
                params[f"${i}"] = group
        
        # 添加命名捕获组
        params.update(match.groupdict())
        
        return True, params