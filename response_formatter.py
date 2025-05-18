# response_formatter.py
import json
import re
from typing import Dict, Any, List, Optional, Union
from astrbot.api import logger

class ResponseFormatter:
    """响应格式化器：处理API响应并格式化输出
    
    负责根据API配置处理和格式化响应数据
    """
    
    def __init__(self, api_configs: Dict[str, Dict[str, Any]]):
        """初始化响应格式化器
        
        Args:
            api_configs: API配置字典，键为API名称
        """
        self.api_configs = api_configs
    
    def format_response(self, api_name: str, success: bool, response_data: Any, status_code: int = 200) -> str:
        """格式化API响应
        
        Args:
            api_name: API名称
            success: 请求是否成功
            response_data: 响应数据
            status_code: HTTP状态码
            
        Returns:
            str: 格式化后的响应文本
        """
        if not success:
            return self._format_error(response_data)
        
        # 获取API配置
        api_config = self.api_configs.get(api_name, {})
        
        # 提取响应数据
        extracted_data = self._extract_data(api_config, response_data, status_code)
        
        # 格式化输出
        return self._apply_format_template(api_config, extracted_data)
    
    def _format_error(self, error_data: Dict[str, Any]) -> str:
        """格式化错误响应
        
        Args:
            error_data: 错误数据
            
        Returns:
            str: 格式化后的错误文本
        """
        if isinstance(error_data, dict) and "error" in error_data:
            return f"错误: {error_data['error']}"
        
        try:
            return f"错误: {json.dumps(error_data, ensure_ascii=False, indent=2)}"
        except:
            return f"错误: {str(error_data)}"
    
    def _extract_data(self, api_config: Dict[str, Any], response_data: Any, status_code: int) -> Any:
        """从响应中提取数据
        
        Args:
            api_config: API配置
            response_data: 响应数据
            status_code: HTTP状态码
            
        Returns:
            Any: 提取的数据
        """
        response_config = api_config.get("response", {})
        extract_config = response_config.get("extract", {})
        
        # 如果没有提取配置，直接返回响应数据
        if not extract_config:
            return response_data
        
        # 按状态码提取数据
        by_status = extract_config.get("by_status", {})
        
        # 尝试精确匹配状态码
        if str(status_code) in by_status:
            return self._extract_by_path(response_data, by_status[str(status_code)])
        
        # 尝试状态码范围匹配(4xx, 5xx)
        status_prefix = f"{status_code // 100}xx"
        if status_prefix in by_status:
            return self._extract_by_path(response_data, by_status[status_prefix])
        
        # 使用默认提取路径
        default_path = extract_config.get("default")
        if default_path:
            return self._extract_by_path(response_data, default_path)
        
        # 没有匹配的提取配置，返回原始数据
        return response_data
    
    def _extract_by_path(self, data: Any, path: str) -> Any:
        """按路径提取数据
        
        支持简单的JSONPath风格路径：$.data.result
        
        Args:
            data: 数据对象
            path: 提取路径
            
        Returns:
            Any: 提取的数据
        """
        if not path.startswith("$."):
            return data
        
        parts = path[2:].split(".")
        current = data
        
        for part in parts:
            if part == "":
                continue
                
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                # 路径不匹配，返回原始数据
                logger.warning(f"提取路径不匹配: {path}")
                return data
        
        return current
    
    def _apply_format_template(self, api_config: Dict[str, Any], data: Any) -> str:
        """应用格式化模板
        
        Args:
            api_config: API配置
            data: 要格式化的数据
            
        Returns:
            str: 格式化后的文本
        """
        response_config = api_config.get("response", {})
        
        # 获取格式化模板
        template = response_config.get("format_template")
        if not template:
            # 没有模板，尝试序列化为JSON
            try:
                return json.dumps(data, ensure_ascii=False, indent=2)
            except:
                return str(data)
        
        # 应用模板
        try:
            if isinstance(data, dict):
                # 替换模板中的变量
                result = template
                for key, value in data.items():
                    result = result.replace(f"{{{{{key}}}}}", str(value))
                return result
            else:
                # 替换单个result变量
                return template.replace("{{result}}", str(data))
        except Exception as e:
            logger.error(f"应用格式化模板失败: {str(e)}")
            return str(data)