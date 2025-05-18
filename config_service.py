# config_service.py
import json
import os
from typing import Dict, List, Optional, Any
from astrbot.api import logger

class ConfigService:
    """配置服务：负责解析、验证和提供API配置信息
    
    主要功能：
    1. 解析配置文件
    2. 验证配置有效性
    3. 提供API配置访问接口
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化配置服务
        
        Args:
            config: 可选的配置字典，如果为None则使用空配置
        """
        self._config = config or {}
        self._apis = {}  # 按名称索引的API配置
        self._rules = []  # 规则列表
        
        # 如果提供了配置，立即进行解析
        if self._config:
            self._parse_config()
    
    def load_config(self, config_path: str) -> bool:
        """从文件加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            if not os.path.exists(config_path):
                logger.error(f"配置文件不存在: {config_path}")
                return False
                
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
            
            return self._parse_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            return False
    
    def _parse_config(self) -> bool:
        """解析已加载的配置
        
        Returns:
            bool: 解析是否成功
        """
        try:
            # 解析API配置
            if "apis" in self._config:
                for api_config in self._config["apis"]:
                    if "name" in api_config:
                        self._apis[api_config["name"]] = api_config
            
            # 解析规则配置
            if "rules" in self._config:
                self._rules = self._config["rules"]
            
            # 解析全局配置
            self._global = self._config.get("global", {})
            
            return True
        except Exception as e:
            logger.error(f"解析配置失败: {str(e)}")
            return False
    
    def get_api_config(self, api_name: str) -> Optional[Dict[str, Any]]:
        """获取指定名称的API配置
        
        Args:
            api_name: API名称
            
        Returns:
            Dict或None: API配置，如果不存在则返回None
        """
        return self._apis.get(api_name)
    
    def get_rules(self) -> List[str]:
        """获取所有规则配置
        
        Returns:
            List[str]: 规则配置列表
        """
        return self._rules
    
    def get_global_config(self) -> Dict[str, Any]:
        """获取全局配置
        
        Returns:
            Dict: 全局配置
        """
        return self._global
    
    def validate_config(self) -> List[str]:
        """验证配置有效性
        
        Returns:
            List[str]: 错误信息列表，如果为空则表示验证通过
        """
        errors = []
        
        # 验证API配置
        if not self._apis:
            errors.append("配置中未定义任何API")
        
        for name, api in self._apis.items():
            if "endpoint" not in api:
                errors.append(f"API '{name}' 缺少必要的endpoint配置")
        
        # 验证规则配置
        if not self._rules:
            errors.append("配置中未定义任何规则")
        
        return errors