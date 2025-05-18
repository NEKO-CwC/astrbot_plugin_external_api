# rule_factory.py
from typing import Dict, Type, List, Optional
from .rules.abstract_rule import AbstractRule
from .rules.regex_rule import RegexRule
from .rules.keyword_rule import KeywordRule
from .rules.command_rule import CommandRule
from .rules.prefix_rule import PrefixRule
from .rules.default_rule import DefaultRule

class RuleFactory:
    """规则工厂：创建并管理各类规则
    
    负责根据配置创建不同类型的规则对象，并按优先级组织规则
    """
    
    def __init__(self):
        """初始化规则工厂"""
        # 注册支持的规则类型
        self.rule_types: Dict[str, Type[AbstractRule]] = {
            "REGEX": RegexRule,
            "KEYWORD": KeywordRule,
            "COMMAND": CommandRule,
            "PREFIX": PrefixRule,
            "DEFAULT": DefaultRule
        }
        
        self.rules: List[AbstractRule] = []
    
    def create_rule(self, rule_config: str) -> Optional[AbstractRule]:
        """创建规则实例
        
        Args:
            rule_config: 规则配置字符串
            
        Returns:
            AbstractRule或None: 创建的规则对象，如果规则类型不支持则返回None
        """
        parts = rule_config.split(",")
        if not parts:
            return None
        
        rule_type = parts[0].upper()
        if rule_type not in self.rule_types:
            return None
        
        try:
            # 使用对应的规则类创建实例
            rule_class = self.rule_types[rule_type]
            return rule_class(rule_config)
        except Exception as e:
            from astrbot.api import logger
            logger.error(f"创建规则失败: {str(e)}")
            return None
    
    def build_rules(self, rule_configs: List[str]) -> List[AbstractRule]:
        """根据配置构建规则列表
        
        Args:
            rule_configs: 规则配置字符串列表
            
        Returns:
            List[AbstractRule]: 构建的规则对象列表
        """
        self.rules = []
        for config in rule_configs:
            rule = self.create_rule(config)
            if rule:
                self.rules.append(rule)
        
        return self.rules
    
    def match_message(self, message: str):
        """匹配消息到规则
        
        Args:
            message: 要匹配的消息
            
        Returns:
            Tuple[bool, Optional[Dict]]: 是否匹配成功和匹配参数
        """
        for rule in self.rules:
            matched, params = rule.match(message)
            if matched:
                return True, params
        
        return False, None