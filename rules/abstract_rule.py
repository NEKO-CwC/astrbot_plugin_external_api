# rules/abstract_rule.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple

class AbstractRule(ABC):
    """规则抽象基类，定义规则匹配的模板方法
    
    通过模板方法模式定义规则匹配的通用流程，具体匹配逻辑由子类实现
    """
    
    def __init__(self, rule_config: str):
        """初始化规则
        
        Args:
            rule_config: 规则配置字符串，格式取决于具体规则类型
        """
        self.rule_config = rule_config
        self.parse_rule_config()
    
    def parse_rule_config(self):
        """解析规则配置
        
        从字符串配置中提取规则参数。默认实现按逗号拆分，子类可重写
        """
        parts = self.rule_config.split(",")
        if len(parts) >= 3:
            self.rule_type = parts[0]  # 规则类型
            self.match_pattern = parts[1]  # 匹配模式
            self.api_name = parts[2]  # 目标API名称
            
            # 可选的路径覆盖
            self.path_override = parts[3] if len(parts) > 3 else None
            
            # 可选的HTTP方法覆盖
            self.method_override = parts[4] if len(parts) > 4 else None
    
    def match(self, message: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """模板方法：执行规则匹配流程
        
        Args:
            message: 要匹配的消息内容
            
        Returns:
            Tuple[bool, Optional[Dict]]: 
                - 第一个元素表示是否匹配成功
                - 第二个元素为匹配结果参数，如果不匹配则为None
        """
        # 前置检查
        if not self._pre_match(message):
            return False, None
        
        # 执行具体匹配
        match_result = self._do_match(message)
        
        # 如果匹配失败
        if not match_result[0]:
            return False, None
        
        # 后置处理
        processed_result = self._post_match(match_result[1])
        
        return True, processed_result
    
    def _pre_match(self, message: str) -> bool:
        """前置匹配检查
        
        Args:
            message: 要匹配的消息
            
        Returns:
            bool: 是否可以继续匹配
        """
        # 默认实现，子类可重写以添加前置检查逻辑
        return len(message.strip()) > 0
    
    @abstractmethod
    def _do_match(self, message: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """执行具体匹配逻辑
        
        Args:
            message: 要匹配的消息
            
        Returns:
            Tuple[bool, Optional[Dict]]: 匹配结果和匹配参数
        """
        pass
    
    def _post_match(self, match_params: Dict[str, Any]) -> Dict[str, Any]:
        """后置匹配处理
        
        Args:
            match_params: 匹配参数
            
        Returns:
            Dict: 处理后的匹配参数
        """
        # 默认实现，子类可重写以添加后置处理逻辑
        result = match_params.copy()
        result.update({
            "api_name": self.api_name,
            "path_override": self.path_override,
            "method_override": self.method_override
        })
        return result