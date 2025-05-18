# request_template_engine.py
import re
import json
import aiohttp
from typing import Dict, Any, Optional, Tuple, Union
from astrbot.api import logger

class RequestTemplateEngine:
    """请求模板引擎：根据模板构造和发送API请求
    
    负责将匹配参数应用到请求模板，构造并发送HTTP请求
    """
    
    def __init__(self, api_configs: Dict[str, Dict[str, Any]], global_config: Dict[str, Any]):
        """初始化请求模板引擎
        
        Args:
            api_configs: API配置字典，键为API名称
            global_config: 全局配置
        """
        self.api_configs = api_configs
        self.global_config = global_config
        self.timeout = global_config.get("timeout", 30)
        self.proxy = global_config.get("proxy", None)
    
    async def send_request(self, api_name: str, match_params: Dict[str, Any]) -> Tuple[bool, Any]:
        """发送API请求
        
        Args:
            api_name: 目标API名称
            match_params: 匹配参数
            
        Returns:
            Tuple[bool, Any]: 请求是否成功和响应数据
        """
        # 获取API配置
        api_config = self.api_configs.get(api_name)
        if not api_config:
            logger.error(f"API配置不存在: {api_name}")
            return False, {"error": f"API配置不存在: {api_name}"}
        
        # 构造请求参数
        try:
            url, method, headers, data = self._build_request_params(api_config, match_params)
        except Exception as e:
            logger.error(f"构造请求参数失败: {str(e)}")
            return False, {"error": f"构造请求参数失败: {str(e)}"}
        
        # 发送请求
        try:
            return await self._do_request(url, method, headers, data)
        except Exception as e:
            logger.error(f"发送请求失败: {str(e)}")
            return False, {"error": f"发送请求失败: {str(e)}"}
    
    def _build_request_params(self, api_config: Dict[str, Any], match_params: Dict[str, Any]) -> Tuple[str, str, Dict[str, str], Optional[Union[Dict[str, Any], str]]]:
        """构造请求参数
        
        Args:
            api_config: API配置
            match_params: 匹配参数
            
        Returns:
            Tuple: (url, method, headers, data)
        """
        # 获取基础URL
        base_url = api_config.get("endpoint", "")
        if not base_url:
            raise ValueError("API配置缺少endpoint")
        
        # 构造路径
        path = match_params.get("path_override") or ""
        # 替换路径中的参数占位符
        for key, value in match_params.items():
            if key.startswith("$"):
                path = path.replace(f"{{{key}}}", str(value))
        
        # 构造完整URL
        url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
        
        # 确定HTTP方法
        method = match_params.get("method_override")
        if not method:
            # 查找匹配的方法配置
            method = self._determine_http_method(api_config, path)
        
        # 获取默认请求头
        headers = api_config.get("headers", {}).copy()
        
        # 构造请求体
        data = None
        if method in ["POST", "PUT", "PATCH"]:
            # 如果配置了预处理模板
            preprocess = api_config.get("preprocess", {})
            if preprocess.get("enabled", False) and "template" in preprocess:
                template = preprocess["template"]
                if "body" in template:
                    data = self._apply_template(template["body"], match_params)
        
        return url, method, headers, data
    
    def _determine_http_method(self, api_config: Dict[str, Any], path: str) -> str:
        """确定HTTP请求方法
        
        根据路径和API配置确定使用的HTTP方法
        
        Args:
            api_config: API配置
            path: 请求路径
            
        Returns:
            str: HTTP方法
        """
        methods = api_config.get("methods", {})
        if not methods:
            return "GET"  # 默认使用GET
        
        if isinstance(methods, str):
            return methods  # 如果methods直接是字符串
        
        # 查找最匹配的路径配置
        path_parts = path.strip("/").split("/")
        current_config = methods
        
        for part in path_parts:
            if not part:
                continue
                
            if isinstance(current_config, str):
                return current_config
                
            if part in current_config:
                current_config = current_config[part]
            elif "DEFAULT" in current_config:
                current_config = current_config["DEFAULT"]
            else:
                break
        
        # 返回找到的方法或默认方法
        if isinstance(current_config, str):
            return current_config
        return current_config.get("DEFAULT", "GET")
    
    def _apply_template(self, template: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """将参数应用到模板
        
        Args:
            template: 模板字典
            params: 参数字典
            
        Returns:
            Dict: 填充参数后的模板
        """
        result = {}
        
        def _process_value(value):
            if isinstance(value, str):
                # 替换字符串中的参数引用
                for param_key, param_value in params.items():
                    value = value.replace(param_key, str(param_value))
                return value
            elif isinstance(value, dict):
                return _process_dict(value)
            elif isinstance(value, list):
                return [_process_value(item) for item in value]
            return value
        
        def _process_dict(template_dict):
            result_dict = {}
            for key, value in template_dict.items():
                result_dict[key] = _process_value(value)
            return result_dict
        
        return _process_dict(template)
    
    async def _do_request(self, url: str, method: str, headers: Dict[str, str], data: Optional[Union[Dict[str, Any], str]]) -> Tuple[bool, Any]:
        """执行HTTP请求
        
        Args:
            url: 请求URL
            method: HTTP方法
            headers: 请求头
            data: 请求数据
            
        Returns:
            Tuple[bool, Any]: 请求是否成功和响应数据
        """
        async with aiohttp.ClientSession() as session:
            try:
                # 准备请求参数
                kwargs = {
                    "headers": headers,
                    "timeout": aiohttp.ClientTimeout(total=self.timeout)
                }
                
                # 添加代理配置
                if self.proxy:
                    kwargs["proxy"] = self.proxy
                
                # 添加请求数据
                if data:
                    if isinstance(data, dict):
                        # 如果是字典，序列化为JSON
                        kwargs["json"] = data
                    else:
                        # 否则作为普通数据
                        kwargs["data"] = data
                
                # 发送请求
                async with session.request(method, url, **kwargs) as response:
                    # 尝试解析JSON响应
                    try:
                        result = await response.json()
                    except:
                        # 如果不是JSON，获取文本
                        result = await response.text()
                    
                    # 检查响应状态
                    if response.status >= 400:
                        return False, {
                            "status_code": response.status,
                            "error": "请求失败",
                            "response": result
                        }
                    
                    return True, result
            except Exception as e:
                return False, {"error": str(e)}