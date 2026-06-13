"""
OCR 服務模組
使用 Ollama LLM 進行圖片文字辨識
"""

import os
import json
import base64
import requests
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime

class OCRResult(BaseModel):
    """OCR 結果"""
    text: str
    confidence: float = 0.0
    raw_response: str = ""
    processing_time: float = 0.0

class OCRService:
    """OCR 服務 - 支援 Ollama 和 vLLM 兩種後端"""
    
    def __init__(self):
        # 優先使用環境變數，否則預設使用 vLLM
        self.use_vllm = os.getenv("USE_VLLM", "true").lower() == "true"
        
        if self.use_vllm:
            self.base_url = os.getenv("VLLM_BASE_URL", "http://localhost:8000")
            self.model = os.getenv("VLLM_MODEL", "QuantTrio/Qwen3.5-27B-AWQ")
            self.api_prefix = "v1"  # vLLM 使用 OpenAI 相容 API
        else:
            self.base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
            self.model = os.getenv("OLLAMA_MODEL", "llama3")
            self.api_prefix = "api"  # Ollama 使用自己的 API
        
        self.timeout = 120  # 秒
        print(f"OCR 服務初始化：使用 {'vLLM' if self.use_vllm else 'Ollama'} @ {self.base_url}")
    
    def health_check(self) -> bool:
        """檢查 LLM 服務是否可用"""
        try:
            if self.use_vllm:
                # vLLM 使用 OpenAI 相容 API
                response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            else:
                # Ollama 使用自己的 API
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"LLM 健康檢查失敗：{e}")
            return False
    
    def list_models(self) -> List[str]:
        """列出已安裝的模型"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
        except:
            pass
        return []
    
    def pull_model(self, model_name: str) -> bool:
        """下載模型"""
        try:
            print(f"正在下載模型 {model_name}...")
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                stream=True
            )
            
            for line in response.iter_lines():
                if line:
                    data = eval(line)  # Ollama 使用 newlines-delimited JSON
                    if 'status' in data:
                        print(f"  {data['status']}")
            
            return True
        except Exception as e:
            print(f"下載模型失敗：{e}")
            return False
    
    def recognize(self, image_path: str, prompt: Optional[str] = None) -> Optional[OCRResult]:
        """
        辨識圖片中的文字
        
        Args:
            image_path: 圖片路徑
            prompt: 自訂提示詞 (預設使用通用 OCR 提示)
        
        Returns:
            OCRResult 物件
        """
        import time
        start_time = time.time()
        
        # 預設提示詞
        if not prompt:
            prompt = """請辨識這張圖片中的所有文字內容。
只輸出辨識到的文字，不需要任何解釋或說明。
保持原文的格式和結構。"""
        
        try:
            # 讀取圖片並轉換為 base64
            with open(image_path, 'rb') as f:
                image_data = f.read()
                image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            if self.use_vllm:
                # vLLM 使用 OpenAI 相容 API
                response = requests.post(
                    f"{self.base_url}/v1/chat/completions",
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                                    {"type": "text", "text": prompt}
                                ]
                            }
                        ],
                        "temperature": 0.1,
                        "max_tokens": 4096
                    },
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    print(f"OCR 辨識失敗：{response.status_code} - {response.text}")
                    return None
                
                result_data = response.json()
                recognized_text = result_data['choices'][0]['message']['content']
                
            else:
                # Ollama 使用自己的 API
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "images": [image_base64],
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "num_ctx": 4096
                        }
                    },
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    print(f"OCR 辨識失敗：{response.status_code}")
                    return None
                
                result_data = response.json()
                recognized_text = result_data.get('response', '')
            
            processing_time = time.time() - start_time
            
            return OCRResult(
                text=recognized_text.strip(),
                confidence=0.9,
                raw_response=recognized_text,
                processing_time=processing_time
            )
            
        except Exception as e:
            print(f"OCR 辨識錯誤：{e}")
            import traceback
            traceback.print_exc()
            return None
    
    def recognize_menu(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        辨識菜單圖片並解析為結構化資料
        
        Args:
            image_path: 菜單圖片路徑
        
        Returns:
            包含菜單項目的字典
        """
        # 使用專門的菜單解析提示詞
        prompt = """請分析這張菜單圖片，並提取以下資訊：
1. 菜名
2. 價格
3. 是否為素食 (如果是素食請標註)

請以 JSON 格式輸出，格式如下：
[
  {
    "name": "菜名",
    "price": 價格數字，
    "food_type": "meat 或 vegetarian"
  },
  ...
]

如果無法辨識，請返回空陣列 []"""
        
        result = self.recognize(image_path, prompt)
        
        if not result:
            return None
        
        # 嘗試解析 JSON
        try:
            import json
            # 清理可能的 markdown 格式
            text = result.text
            if text.startswith('```json'):
                text = text[7:]
            if text.endswith('```'):
                text = text[:-3]
            
            menu_items = json.loads(text.strip())
            
            return {
                "success": True,
                "items": menu_items,
                "raw_text": result.text,
                "processing_time": result.processing_time
            }
        except json.JSONDecodeError as e:
            print(f"JSON 解析失敗：{e}")
            # 返回原始文字供管理員手動處理
            return {
                "success": False,
                "items": [],
                "raw_text": result.text,
                "error": f"無法自動解析，請手動輸入：{result.text}"
            }
    
    def recognize_leave_form(self, image_path: str, employee_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        辨識休假表勾選圖片
        
        Args:
            image_path: 休假表圖片路徑
            employee_id: 員工編號 (可選)
        
        Returns:
            包含休假資訊的字典
        """
        prompt = f"""請分析這張休假表圖片，找出所有被勾選的日期。

請以 JSON 格式輸出，格式如下：
{{
  "leave_dates": ["YYYY-MM-DD", "YYYY-MM-DD"],
  "leave_type": "年假/特休/事假",
  "notes": "備註內容"
}}

如果沒有看到勾選，請返回空的 leave_dates 陣列。"""
        
        result = self.recognize(image_path, prompt)
        
        if not result:
            return None
        
        # 嘗試解析 JSON
        try:
            import json
            text = result.text
            if text.startswith('```json'):
                text = text[7:]
            if text.endswith('```'):
                text = text[:-3]
            
            leave_data = json.loads(text.strip())
            
            return {
                "success": True,
                "leave_dates": leave_data.get('leave_dates', []),
                "leave_type": leave_data.get('leave_type', ''),
                "notes": leave_data.get('notes', ''),
                "raw_text": result.text,
                "processing_time": result.processing_time
            }
        except json.JSONDecodeError as e:
            print(f"JSON 解析失敗：{e}")
            return {
                "success": False,
                "leave_dates": [],
                "raw_text": result.text,
                "error": f"無法自動解析，請手動輸入：{result.text}"
            }

# 全域 OCR 服務實例
ocr_service = OCRService()
