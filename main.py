# main.py
import os
import json
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core.star.star_tools import StarTools

from .config_service import ConfigService
from .rule_factory import RuleFactory
from .request_template_engine import RequestTemplateEngine
from .response_formatter import ResponseFormatter

@register("astrbot_plugin_external_api", "YourName", "通过简单指令调用外部API", "1.0.0", "https://github.com/yourusername/astrbot_plugin_external_api")
class ExternalAPIPlugin(Star):
    """AstrBot外部API调用插件
    
    通过简单的消息格式将用户请求转发到预配置的外部API
    """
    
    def __init__(self, context: Context, config=None):
        """初始化插件
        
        Args:
            context: AstrBot上下文
            config: 插件配置
        """
        super().__init__(context)

        # 初始化组件
        self.config_service = ConfigService()
        self.rule_factory = RuleFactory()
        self.request_engine = None
        self.response_formatter = None
        
        # 加载配置
        self.config = config
        
        # 初始化完成后的标志
        self.initialized = False
    
    async def initialize(self):
        """插件初始化"""
        logger.info("开始初始化外部API插件...")
        print(self.config)
        
        # 加载插件配置
        try:
            if self.config.apis:
                self.config_service._config = self.config
                self.config_service._parse_config()
                logger.info("从传入配置加载API配置成功")
            else:
                # 获取数据目录
                data_dir = self._get_data_dir()
                config_path = os.path.join(data_dir, "config.json")
                
                if os.path.exists(config_path):
                    self.config_service.load_config(config_path)
                    logger.info(f"从 {config_path} 加载API配置成功")
                else:
                    logger.warning(f"配置文件 {config_path} 不存在，使用默认配置")
                    # 创建示例配置
                    await self._create_sample_config(config_path)
        except Exception as e:
            logger.error(f"加载配置失败: {str(e)}")
            return
        
        # 验证配置
        errors = self.config_service.validate_config()
        if errors:
            for error in errors:
                logger.error(f"配置错误: {error}")
            return
        
        # 创建规则
        rules = self.rule_factory.build_rules(self.config_service.get_rules())
        logger.info(f"创建了 {len(rules)} 条规则")
        
        # 初始化请求引擎
        self.request_engine = RequestTemplateEngine(
            self.config_service._apis,
            self.config_service.get_global_config()
        )
        
        # 初始化响应格式化器
        self.response_formatter = ResponseFormatter(self.config_service._apis)
        
        self.initialized = True
        logger.info("外部API插件初始化完成")
    
    async def _create_sample_config(self, config_path):
        """创建示例配置文件
        
        Args:
            config_path: 配置文件路径
        """
        sample_config = {
            "global": {
                "proxy": "",
                "timeout": 30,
                "default_api": "local_test"
            },
            "apis": [
                {
                    "name": "local_test",
                    "endpoint": "http://localhost:8999",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "methods": {
                        "/hello": "POST",
                        "DEFAULT": "GET"
                    },
                    "response": {
                        "extract": {
                            "default": "$.data",
                            "by_status": {
                                "200": "$.data.result",
                                "4xx": "$.error.message"
                            }
                        },
                        "fallback": "API调用失败",
                        "format_template": "结果: {{result}}"
                    }
                }
            ],
            "rules": [
                "COMMAND,/call,local_test,/hello,POST",
                "REGEX,^请求\\s+(.+)$,local_test,/hello,POST",
                "KEYWORD,测试,local_test,/hello,POST",
                "DEFAULT,local_test"
            ]
        }
        
        # 确保目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # 写入示例配置
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(sample_config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"已创建示例配置: {config_path}")
    
    def _get_data_dir(self):
        """获取插件数据目录"""
        return str(StarTools.get_data_dir())

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def handle_all_messages(self, event: AstrMessageEvent):
        """处理所有消息
        
        尝试匹配所有消息到规则
        """
        if not self.initialized:
            return
        
        message = event.message_str
        
        # 匹配规则
        matched, params = self.rule_factory.match_message(message)
        if not matched:
            return
        
        print(f"匹配到规则: {params}")
        
        # 获取目标API
        api_name = params.get("api_name")
        if not api_name:
            return
        
        # 发送请求
        success, response = await self.request_engine.send_request(api_name, params)
        
        # 格式化响应
        result = self.response_formatter.format_response(
            api_name,
            success,
            response,
            response.get("status_code", 200) if isinstance(response, dict) else 200
        )
        
        yield event.plain_result(result)
    
    async def terminate(self):
        """插件终止时的处理"""
        logger.info("外部API插件已终止")