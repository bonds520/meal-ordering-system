# LINE Messaging API 整合模組
# 提供 LINE Bot 的封裝與工具函數

from typing import List, Optional, Dict, Any
import os
from datetime import datetime

class LineBot:
    """LINE Bot 封裝類別"""
    
    def __init__(self, channel_access_token: str, channel_secret: str):
        self.channel_access_token = channel_access_token
        self.channel_secret = channel_secret
        self.base_url = "https://api.line.me/v2"
        
    async def reply_message(self, reply_token: str, messages: List[Dict[str, Any]]):
        """回覆訊息"""
        # TODO: 實際呼叫 LINE API
        print(f"Reply to {reply_token}: {messages}")
        return True
    
    async def push_message(self, to: str, messages: List[Dict[str, Any]], notification_disabled: bool = False):
        """推送訊息"""
        # TODO: 實際呼叫 LINE API
        print(f"Push to {to}: {messages}")
        return True
    
    async def link_rich_menu(self, user_id: str, rich_menu_id: str):
        """連結 Rich Menu 到用戶"""
        # TODO: 實際呼叫 LINE API
        print(f"Link rich menu {rich_menu_id} to user {user_id}")
        return True
    
    async def create_rich_menu(self, rich_menu_id: str, rich_menu: Dict[str, Any]):
        """建立 Rich Menu"""
        # TODO: 實際呼叫 LINE API
        print(f"Create rich menu {rich_menu_id}")
        return True

# 訊息類型
class TextMessage:
    """文字訊息"""
    def __init__(self, text: str):
        self.type = "text"
        self.text = text
    
    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type, "text": self.text}

class ImageMessage:
    """圖片訊息"""
    def __init__(self, original_content_url: str, preview_content_url: str):
        self.type = "image"
        self.original_content_url = original_content_url
        self.preview_content_url = preview_content_url
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "originalContentUrl": self.original_content_url,
            "previewContentUrl": self.preview_content_url
        }

class FlexMessage:
    """Flex Message"""
    def __init__(self, alt_text: str, content: Any):
        self.type = "flex"
        self.alt_text = alt_text
        self.content = content
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "altText": self.alt_text,
            "contents": self.content.to_dict() if hasattr(self.content, 'to_dict') else self.content
        }

# Flex 模板
class BubbleTemplate:
    """Bubble Template"""
    def __init__(
        self,
        hero_image: Optional[Any] = None,
        body: Optional[Any] = None,
        footer: Optional[Any] = None,
        action: Optional[Any] = None,
        styles: Optional[Dict[str, Any]] = None
    ):
        self.type = "bubble"
        self.hero_image = hero_image
        self.body = body
        self.footer = footer
        self.action = action
        self.styles = styles
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"type": self.type}
        if self.hero_image:
            result["hero"] = self.hero_image.to_dict() if hasattr(self.hero_image, 'to_dict') else self.hero_image
        if self.body:
            result["body"] = self.body.to_dict() if hasattr(self.body, 'to_dict') else self.body
        if self.footer:
            result["footer"] = self.footer.to_dict() if hasattr(self.footer, 'to_dict') else self.footer
        if self.action:
            result["actions"] = [self.action.to_dict()] if hasattr(self.action, 'to_dict') else [self.action]
        if self.styles:
            result["styles"] = self.styles
        return result

class CarouselTemplate:
    """Carousel Template"""
    def __init__(self, contents: List[BubbleTemplate]):
        self.type = "carousel"
        self.contents = contents
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "contents": [content.to_dict() for content in self.contents]
        }

# Flex 元件
class BoxComponent:
    """Box Component"""
    def __init__(
        self,
        layout: str,
        contents: List[Any],
        spacing: Optional[str] = None,
        margin: Optional[str] = None,
        padding: Optional[str] = None,
        padding_all: Optional[int] = None,
        padding_top: Optional[int] = None,
        padding_bottom: Optional[int] = None,
        padding_start: Optional[int] = None,
        padding_end: Optional[int] = None,
        padding_left: Optional[int] = None,
        padding_right: Optional[int] = None,
        background_color: Optional[str] = None,
        border_color: Optional[str] = None,
        action: Optional[Any] = None
    ):
        self.type = "box"
        self.layout = layout
        self.contents = contents
        self.spacing = spacing
        self.margin = margin
        self.padding = padding
        self.padding_all = padding_all
        self.padding_top = padding_top
        self.padding_bottom = padding_bottom
        self.padding_start = padding_start
        self.padding_end = padding_end
        self.padding_left = padding_left
        self.padding_right = padding_right
        self.background_color = background_color
        self.border_color = border_color
        self.action = action
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": self.type,
            "layout": self.layout,
            "contents": [content.to_dict() if hasattr(content, 'to_dict') else content for content in self.contents]
        }
        if self.spacing:
            result["spacing"] = self.spacing
        if self.margin:
            result["margin"] = self.margin
        if self.padding:
            result["padding"] = self.padding
        if self.padding_all:
            result["paddingAll"] = self.padding_all
        if self.padding_top:
            result["paddingTop"] = self.padding_top
        if self.padding_bottom:
            result["paddingBottom"] = self.padding_bottom
        if self.padding_start:
            result["paddingStart"] = self.padding_start
        if self.padding_end:
            result["paddingEnd"] = self.padding_end
        if self.padding_left:
            result["paddingLeft"] = self.padding_left
        if self.padding_right:
            result["paddingRight"] = self.padding_right
        if self.background_color:
            result["backgroundColor"] = self.background_color
        if self.border_color:
            result["borderColor"] = self.border_color
        if self.action:
            result["action"] = self.action.to_dict() if hasattr(self.action, 'to_dict') else self.action
        return result

class TextComponent:
    """Text Component"""
    def __init__(
        self,
        text: str,
        size: Optional[str] = None,
        weight: Optional[str] = None,
        color: Optional[str] = None,
        style: Optional[str] = None,
        align: Optional[str] = None,
        wrap: Optional[bool] = None,
        action: Optional[Any] = None,
        margin: Optional[str] = None
    ):
        self.type = "text"
        self.text = text
        self.size = size
        self.weight = weight
        self.color = color
        self.style = style
        self.align = align
        self.wrap = wrap
        self.action = action
        self.margin = margin
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": self.type,
            "text": self.text
        }
        if self.size:
            result["size"] = self.size
        if self.weight:
            result["weight"] = self.weight
        if self.color:
            result["color"] = self.color
        if self.style:
            result["style"] = self.style
        if self.align:
            result["align"] = self.align
        if self.wrap is not None:
            result["wrap"] = self.wrap
        if self.action:
            result["action"] = self.action.to_dict() if hasattr(self.action, 'to_dict') else self.action
        if self.margin:
            result["margin"] = self.margin
        return result

class ImageComponent:
    """Image Component"""
    def __init__(
        self,
        url: str,
        size: Optional[str] = None,
        duration: Optional[int] = None,
        layout: Optional[str] = None,
        action: Optional[Any] = None,
        margin: Optional[str] = None,
        gravity: Optional[str] = None
    ):
        self.type = "image"
        self.url = url
        self.size = size
        self.duration = duration
        self.layout = layout
        self.action = action
        self.margin = margin
        self.gravity = gravity
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": self.type,
            "url": self.url
        }
        if self.size:
            result["size"] = self.size
        if self.duration:
            result["duration"] = self.duration
        if self.layout:
            result["layout"] = self.layout
        if self.action:
            result["action"] = self.action.to_dict() if hasattr(self.action, 'to_dict') else self.action
        if self.margin:
            result["margin"] = self.margin
        if self.gravity:
            result["gravity"] = self.gravity
        return result

class ButtonComponent:
    """Button Component"""
    def __init__(
        self,
        label: str,
        action_type: str,
        data: Optional[str] = None,
        uri: Optional[str] = None,
        color: Optional[str] = None,
        style: Optional[str] = None,
        height: Optional[str] = None,
        margin: Optional[str] = None
    ):
        self.type = "button"
        self.label = label
        self.action_type = action_type
        self.data = data
        self.uri = uri
        self.color = color
        self.style = style
        self.height = height
        self.margin = margin
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": self.type,
            "label": self.label
        }
        
        if self.action_type == "postback":
            result["action"] = {
                "type": "postback",
                "data": self.data
            }
        elif self.action_type == "uri":
            result["action"] = {
                "type": "uri",
                "uri": self.uri
            }
        elif self.action_type == "message":
            result["action"] = {
                "type": "message",
                "label": self.label,
                "text": self.data
            }
        
        if self.color:
            result["color"] = self.color
        if self.style:
            result["style"] = self.style
        if self.height:
            result["height"] = self.height
        if self.margin:
            result["margin"] = self.margin
        
        return result

class IconComponent:
    """Icon Component"""
    def __init__(
        self,
        url: str,
        size: Optional[str] = None,
        margin: Optional[str] = None
    ):
        self.type = "icon"
        self.url = url
        self.size = size
        self.margin = margin
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": self.type,
            "url": self.url
        }
        if self.size:
            result["size"] = self.size
        if self.margin:
            result["margin"] = self.margin
        return result

class SpanComponent:
    """Span Component (用於文字樣式)"""
    def __init__(
        self,
        text: str,
        size: Optional[str] = None,
        weight: Optional[str] = None,
        color: Optional[str] = None,
        style: Optional[str] = None
    ):
        self.type = "span"
        self.text = text
        self.size = size
        self.weight = weight
        self.color = color
        self.style = style
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": self.type,
            "text": self.text
        }
        if self.size:
            result["size"] = self.size
        if self.weight:
            result["weight"] = self.weight
        if self.color:
            result["color"] = self.color
        if self.style:
            result["style"] = self.style
        return result
