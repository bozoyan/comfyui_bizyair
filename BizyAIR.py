# BizyAIR API远程调用插件
import requests
import json
import os
import base64
import torch
from PIL import Image
import numpy as np
from io import BytesIO
import mimetypes
import urllib.parse
import hashlib
import shutil

def download_and_cache_image(image_url):
    """下载图像并缓存到本地文件夹"""
    try:
        # 获取ComfyUI根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 找到ComfyUI根目录 (向上回溯找到custom_nodes的上级目录)
        comfyui_root = current_dir
        while os.path.basename(comfyui_root) != 'custom_nodes' and comfyui_root != os.path.dirname(comfyui_root):
            comfyui_root = os.path.dirname(comfyui_root)
        if os.path.basename(comfyui_root) == 'custom_nodes':
            comfyui_root = os.path.dirname(comfyui_root)
        else:
            # 如果找不到，使用当前目录
            comfyui_root = current_dir
        
        # 创建 temp 文件夹
        temp_dir = os.path.join(comfyui_root, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # 使用URL的哈希值作为文件名，避免重复下载
        url_hash = hashlib.md5(image_url.encode('utf-8')).hexdigest()
        
        # 从 URL 获取文件扩展名
        parsed_url = urllib.parse.urlparse(image_url)
        original_ext = os.path.splitext(parsed_url.path)[1].lower()
        if not original_ext:
            original_ext = '.webp'  # 默认扩展名
        
        # 生成缓存文件路径
        cache_filename = f"{url_hash}{original_ext}"
        cache_file_path = os.path.join(temp_dir, cache_filename)
        
        # 检查是否已经缓存
        if os.path.exists(cache_file_path):
            # print(f"📋 使用缓存图像: {cache_filename}")
            return cache_file_path
        
        # 下载图像
        # print(f"🌐 下载图像: {image_url}")
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # 保存到缓存文件
        with open(cache_file_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ 图像保存到: {cache_file_path}")
        return cache_file_path
        
    except Exception as e:
        print(f"❌ 下载和缓存图像失败: {e}")
        return None

def image_file_to_base64(image_path):
    """将本地图像文件转换为WebP格式的base64编码"""
    try:
        # 使用PIL打开图像
        with Image.open(image_path) as pil_image:
            # 确保图像是RGB格式
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # 转换为numpy数组并转换为torch张量
            image_np = np.array(pil_image).astype(np.float32) / 255.0
            # 添加batch维度以符合 [batch, height, width, channels] 格式
            image_tensor = torch.from_numpy(image_np)[None,]  # [1, H, W, C]
            
            # 确保图像张量是正确的格式 [batch, height, width, channels]
            if len(image_tensor.shape) == 4:
                image_tensor = image_tensor[0]  # 取第一张图
            
            # 转换为numpy数组并确保数据类型正确
            if image_tensor.dtype != torch.uint8:
                image_tensor = (image_tensor * 255).clamp(0, 255).to(torch.uint8)
            
            image_np_final = image_tensor.cpu().numpy()
            
            # 转换为PIL图像
            pil_image_processed = Image.fromarray(image_np_final)
            
            # 转换为WebP格式的base64（不压缩，使用无损模式）
            buffer = BytesIO()
            pil_image_processed.save(buffer, format='WebP')  # 与 image_to_base64 保持一致
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            print(f"✅ 本地图像文件转换为WebP base64成功，大小: {len(img_base64)} 字符")
            return f"data:image/webp;base64,{img_base64}"
            
    except Exception as e:
        print(f"❌ 图像文件转换base64失败: {e}")
        return None

# 全局变量用于追踪当前的Key索引
CURRENT_KEY_INDEX = 0

def get_bizyair_api_key():
    """获取BizyAIR API密钥，支持多Key轮询"""
    global CURRENT_KEY_INDEX
    key_path = os.path.join(os.path.dirname(__file__), "key", "siliconflow_API_key.txt")
    try:
        if not os.path.exists(key_path):
            return ""
            
        with open(key_path, "r", encoding="utf-8") as f:
            # 读取所有行并过滤空行
            keys = [line.strip() for line in f.readlines() if line.strip()]
            
        if not keys:
            return ""
            
        # 轮询选择
        if CURRENT_KEY_INDEX >= len(keys):
            CURRENT_KEY_INDEX = 0
            
        selected_key = keys[CURRENT_KEY_INDEX]
        
        # 更新索引以供下次调用
        CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(keys)
        
        # print(f"🔑 使用API Key [{CURRENT_KEY_INDEX}/{len(keys)}]: {selected_key[:8]}...")
        return selected_key
    except Exception as e:
        print(f"❌ 读取API Key失败: {e}")
        return ""

def save_bizyair_api_key(new_key):
    """保存新的API Key到文件，自动去重"""
    if not new_key or not new_key.strip():
        return
        
    key_path = os.path.join(os.path.dirname(__file__), "key", "siliconflow_API_key.txt")
    try:
        # 读取现有Keys
        keys = []
        if os.path.exists(key_path):
            with open(key_path, "r", encoding="utf-8") as f:
                keys = [line.strip() for line in f.readlines() if line.strip()]
        
        # 添加新Key（如果不存在）
        clean_key = new_key.strip()
        if clean_key not in keys:
            keys.append(clean_key)
            
            # 写回文件
            with open(key_path, "w", encoding="utf-8") as f:
                for key in keys:
                    f.write(f"{key}\n")
            print(f"✅ 新API Key已保存到: {key_path}")
            
    except Exception as e:
        print(f"❌ 保存API Key失败: {e}")

def image_to_base64(image_tensor):
    """将图像张量转换为base64字符串"""
    # 确保图像张量是正确的格式 [batch, height, width, channels]
    if len(image_tensor.shape) == 4:
        image_tensor = image_tensor[0]  # 取第一张图
    
    # 转换为numpy数组并确保数据类型正确
    if image_tensor.dtype != torch.uint8:
        image_tensor = (image_tensor * 255).clamp(0, 255).to(torch.uint8)
    
    image_np = image_tensor.cpu().numpy()
    
    # 转换为PIL图像
    pil_image = Image.fromarray(image_np)
    
    # 转换为base64
    buffer = BytesIO()
    pil_image.save(buffer, format='WebP')
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return f"data:image/webp;base64,{img_base64}"

def url_to_tensor(image_url):
    """将URL图像转换为ComfyUI张量格式"""
    try:
        # print(f"🌐 开始下载图像: {image_url}")
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # 从响应中获取图像数据
        image_data = response.content
        # print(f"💾 图像数据下载成功，大小: {len(image_data)} 字节")
        
        # 使用PIL打开图像
        image = Image.open(BytesIO(image_data))
        print(f"🖼️ PIL图像加载成功，格式: {image.mode}, 尺寸: {image.size}")
        
        # 确保图像是RGB格式
        if image.mode != 'RGB':
            image = image.convert('RGB')
            # print(f"🎨 图像已转换为RGB格式")
        
        # 转换为numpy数组
        image_np = np.array(image).astype(np.float32) / 255.0
        
        # 转换为torch张量并添加batch维度
        image_tensor = torch.from_numpy(image_np)[None,]  # [1, H, W, C]
        
        # print(f"✅ 图像转换为张量成功，形状: {image_tensor.shape}, 数据类型: {image_tensor.dtype}")
        return image_tensor
    except Exception as e:
        print(f"❌ 加载图像失败: {e}")
        # 返回一个默认的64x64空白图像
        empty_image = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
        print(f"🖼️ 返回默认空白图像: {empty_image.shape}")
        return empty_image

class BA_BizyAIR_Main:
    """BizyAIR主界面API调用节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "web_app_id": ("INT", {"default": 36259, "min": 1, "max": 999999}),
                "api_key": ("STRING", {"default": "", "multiline": False}),
            },
            "optional": {
                "input_1": ("STRING", {"default": ""}),
                "input_2": ("STRING", {"default": ""}),
                "input_3": ("STRING", {"default": ""}),
                "input_4": ("STRING", {"default": ""}),
                "input_5": ("STRING", {"default": ""}),
                "input_6": ("STRING", {"default": ""}),
                "input_7": ("STRING", {"default": ""}),
                "input_8": ("STRING", {"default": ""}),
                "input_9": ("STRING", {"default": ""}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING", "IMAGE")
    RETURN_NAMES = ("response_json", "task_id", "image_url", "image")
    FUNCTION = "process_api_call"
    CATEGORY = "🇨🇳BOZO/BizyAir"
    
    def process_api_call(self, web_app_id, api_key="", **kwargs):
        # 获取API密钥
        if api_key and api_key.strip():
            # 如果提供了Key，尝试保存
            save_bizyair_api_key(api_key.strip())
        else:
            # 否则从文件获取
            api_key = get_bizyair_api_key()
        
        if not api_key:
            print("错误: 未找到API密钥")
            return ("{}", "", "", torch.zeros((1, 64, 64, 3), dtype=torch.float32))
        
        # 构建请求数据
        input_values = {}
        for i in range(1, 10):
            input_key = f"input_{i}"
            if input_key in kwargs and kwargs[input_key].strip():
                # 分析输入格式，例如: "91:LoadImage.image|https://example.com/image.jpg"
                input_data = kwargs[input_key].strip()
                if '|' in input_data:
                    node_name, value = input_data.split('|', 1)
                    input_values[node_name] = value
        
        # API请求配置
        url = "https://api.bizyair.cn/w/v1/webapp/task/openapi/create"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "web_app_id": web_app_id,
            "suppress_preview_output": True,
            "input_values": input_values
        }
        
        try:
            # 发送请求
            # print(f"BizyAIR请求数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            response = requests.post(url, headers=headers, json=data, timeout=300)
            response.raise_for_status()
            
            result = response.json()
            print(f"📊 BizyAIR响应状态: {result.get('status', 'Unknown')}")
            print(f"📋 响应数据摘要: 包含 {len(result.get('outputs', []))} 个输出")
            
            # 检查执行状态和错误处理
            if result.get('status') == 'Failed':
                print("=== BizyAIR执行失败 ===")
                if 'outputs' in result and len(result['outputs']) > 0:
                    error_info = result['outputs'][0]
                    error_type = error_info.get('error_type', 'Unknown')
                    error_msg = error_info.get('error_msg', 'No error message')
                    
                    print(f"错误类型: {error_type}")
                    print(f"错误信息: {error_msg}")
                    
                    # 解析具体的ComfyUI错误
                    if 'exception_message' in error_msg:
                        if 'size of tensor' in error_msg and 'must match' in error_msg:
                            print("⚠️  张量维度不匹配错误 - 这通常是由以下原因造成的:")
                            print("   1. 输入图像尺寸与模型期望不匹配")
                            print("   2. 工作流中的节点参数配置错误")
                            print("   3. 模型和采样器不兼容")
                            print("   4. 建议检查图像尺寸和工作流配置")
                    
                    # 提供解决建议
                    if 'SamplerCustomAdvanced' in error_msg:
                        print("💡 建议解决方案:")
                        print("   - 确保输入图像尺寸为标准比例 (如 1024x1024, 512x768 等)")
                        print("   - 检查采样器设置与模型兼容性")
                        print("   - 尝试使用不同的采样器或调整参数")
            
            # 提取结果 - 返回完整的API响应数据
            response_json = json.dumps(result, ensure_ascii=False, indent=2)
            task_id = result.get('request_id', '')
            print(f"任务 ID：{task_id}")
            
            # 获取图像URL和转换为张量
            image_url = ""
            image_tensor = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
            
            # 只有在成功时才尝试获取图像
            status = result.get('status', '').lower()
            if status in ['completed', 'success'] and 'outputs' in result and len(result['outputs']) > 0:
                try:
                    # 获取第一个输出的图像URL
                    output = result['outputs'][0]
                    if 'object_url' in output:
                        image_url = output['object_url']
                        print(f"✅ 获取图像URL成功: {image_url}")
                        
                        # 下载并转换图像
                        # print(f"📥 正在下载图像: {image_url}")
                        image_tensor = url_to_tensor(image_url)
                        # print(f"🖼️ 图像下载并转换为张量成功，尺寸: {image_tensor.shape}")
                    else:
                        print("⚠️ 输出中未找到 object_url 字段")
                except Exception as e:
                    print(f"❌ 处理图像输出时发生错误: {e}")
            elif status == 'failed':
                print("❌ 任务执行失败，返回空白图像")
            else:
                print(f"⚠️ 未知状态: {status}，返回空白图像")
            
            return (response_json, task_id, image_url, image_tensor)
            
        except Exception as e:
            print(f"BizyAIR API调用失败: {e}")
            error_response = {
                "error": str(e),
                "message": "API调用过程中发生错误"
            }
            return (json.dumps(error_response, ensure_ascii=False, indent=2), "", "", torch.zeros((1, 64, 64, 3), dtype=torch.float32))

class BA_LoadImage:
    """BizyAIR图像输入节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "node_name": ("STRING", {"default": "91:LoadImage.image", "multiline": False}),
                "use_url": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "image": ("IMAGE",),
                "image_url": ("STRING", {"default": "", "multiline": False}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("formatted_input",)
    FUNCTION = "format_image_input"
    CATEGORY = "🇨🇳BOZO/BizyAir"
    
    def format_image_input(self, node_name, use_url=False, image=None, image_url=""):
        try:
            if use_url and image_url.strip():
                # 使用URL模式，先下载到本地缓存，再转换为WebP base64
                print(f"🌐 URL模式：处理图像URL: {image_url.strip()}")
                
                # 下载并缓存图像
                cached_file_path = download_and_cache_image(image_url.strip())
                formatted = f"{node_name}|{image_url.strip()}"
                # if cached_file_path:
                #     # 将本地文件转换为WebP base64编码
                #     base64_data = image_file_to_base64(cached_file_path)
                    
                #     if base64_data:
                #         formatted = f"{node_name}|{base64_data}"
                #         print(f"✅ 图像输入格式化完成(使用URL+本地缓存): {node_name}")
                #     else:
                #         print(f"❌ 本地文件转换base64失败")
                #         formatted = f"{node_name}|"
                # else:
                #     print(f"❌ 下载和缓存图像失败")
                #     formatted = f"{node_name}|"
                    
            elif not use_url and image is not None:
                # 使用base64模式，需要检测image输入
                base64_data = image_to_base64(image)
                formatted = f"{node_name}|{base64_data}"
                # print(f"✅ 图像输入格式化完成(使用Base64): {node_name}")
            elif use_url and not image_url.strip():
                # URL模式但未提供URL
                print(f"❌ 错误: 已启用URL模式但未提供图像URL")
                formatted = f"{node_name}|"
            elif not use_url and image is None:
                # Base64模式但未提供图像
                print(f"❌ 错误: 未启用URL模式但未提供图像输入")
                formatted = f"{node_name}|"
            else:
                # 其他情况
                formatted = f"{node_name}|"
            
            return (formatted,)
            
        except Exception as e:
            print(f"❌ 图像格式化失败: {e}")
            return (f"{node_name}|",)

class BA_Float_Value:
    """BizyAIR数值输入节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "value": ("FLOAT", {"default": 2.0, "min": 0.0, "max": 2048.0, "step": 0.1}),
                "node_name": ("STRING", {"default": "99:easy float.value", "multiline": False}),
                "use_float": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("formatted_input",)
    FUNCTION = "format_value_input"
    CATEGORY = "🇨🇳BOZO/BizyAir"
    
    def format_value_input(self, value, node_name, use_float=False):
        try:
            if use_float:
                # 使用浮点数
                formatted_value = f"{value:.1f}"
                # print(f"数值输入格式化完成(浮点数): {node_name} = {formatted_value}")
            else:
                # 使用整数
                formatted_value = str(int(value))
                # print(f"数值输入格式化完成(整数): {node_name} = {formatted_value}")
            
            formatted = f"{node_name}|{formatted_value}"
            return (formatted,)
        except Exception as e:
            print(f"数值格式化失败: {e}")
            return (f"{node_name}|2",)

class BA_String_Value:
    """BizyAIR字符串输入节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "", "multiline": True}),
                "node_name": ("STRING", {"default": "14:PrimitiveStringMultiline.value", "multiline": False}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("formatted_input",)
    FUNCTION = "format_string_input"
    CATEGORY = "🇨🇳BOZO/BizyAir"
    
    def format_string_input(self, text, node_name):
        try:
            formatted = f"{node_name}|{text}"
            # print(f"字符串输入格式化完成: {node_name}")
            return (formatted,)
        except Exception as e:
            print(f"字符串格式化失败: {e}")
            return (f"{node_name}|",)

class BA_Image_Resizer:
    """BizyAIR图像尺寸调整节点 - 用于解决张量维度不匹配问题"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "width": ("INT", {"default": 1536, "min": 64, "max": 4096, "step": 64}),
                "height": ("INT", {"default": 1536, "min": 64, "max": 4096, "step": 64}),
            },
            "optional": {
                "resample_method": (["LANCZOS", "BILINEAR", "BICUBIC", "NEAREST"], {"default": "LANCZOS"}),
                "maintain_aspect_ratio": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "size_info")
    FUNCTION = "resize_image"
    CATEGORY = "🇨🇳BOZO/PIC"
    
    def resize_image(self, image, width, height, resample_method="LANCZOS", maintain_aspect_ratio=True):
        try:
            # 确保图像张量是正确的格式 [batch, height, width, channels]
            if len(image.shape) == 4:
                image_tensor = image[0]  # 取第一张图
            else:
                image_tensor = image
            
            # 转换为numpy数组
            if image_tensor.dtype != torch.uint8:
                image_np = (image_tensor * 255).clamp(0, 255).to(torch.uint8).cpu().numpy()
            else:
                image_np = image_tensor.cpu().numpy()
            
            # 转换为PIL图像
            pil_image = Image.fromarray(image_np)
            original_size = pil_image.size
            
            # 计算新尺寸
            if maintain_aspect_ratio:
                # 保持宽高比
                aspect_ratio = original_size[0] / original_size[1]
                if width / height > aspect_ratio:
                    # 以高度为准
                    new_width = int(height * aspect_ratio)
                    new_height = height
                else:
                    # 以宽度为准
                    new_width = width
                    new_height = int(width / aspect_ratio)
                
                # 确保尺寸是64的倍数
                new_width = (new_width // 64) * 64
                new_height = (new_height // 64) * 64
                
                # 确保最小尺寸
                new_width = max(new_width, 64)
                new_height = max(new_height, 64)
            else:
                new_width = width
                new_height = height
            
            # 调整图像尺寸 - PIL版本兼容性处理
            # 使用数值常量避免版本兼容性问题
            resample_map = {
                "LANCZOS": 1,  # Image.LANCZOS 或 Image.Resampling.LANCZOS
                "BILINEAR": 2,  # Image.BILINEAR 或 Image.Resampling.BILINEAR
                "BICUBIC": 3,  # Image.BICUBIC 或 Image.Resampling.BICUBIC
                "NEAREST": 0  # Image.NEAREST 或 Image.Resampling.NEAREST
            }
            
            resized_image = pil_image.resize((new_width, new_height), resample_map[resample_method])
            
            # 转换回张量格式
            resized_np = np.array(resized_image).astype(np.float32) / 255.0
            resized_tensor = torch.from_numpy(resized_np)[None,]  # [1, H, W, C]
            
            size_info = f"原始尺寸: {original_size[0]}x{original_size[1]} -> 调整后: {new_width}x{new_height}"
            print(f"图像尺寸调整完成: {size_info}")
            
            return (resized_tensor, size_info)
            
        except Exception as e:
            print(f"图像尺寸调整失败: {e}")
            # 返回默认尺寸的图像
            default_image = torch.zeros((1, height, width, 3), dtype=torch.float32)
            return (default_image, f"调整失败: {str(e)}")

class BA_Task_Status_Checker:
    """BizyAIR任务状态检查节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "task_id": ("STRING", {"default": "", "multiline": False}),
                "api_key": ("STRING", {"default": "", "multiline": False}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "IMAGE")
    RETURN_NAMES = ("status_info", "image_url", "image")
    FUNCTION = "check_task_status"
    CATEGORY = "🇨🇳BOZO/BizyAir"
    
    def check_task_status(self, task_id, api_key=""):
        # 获取API密钥
        if not api_key.strip():
            api_key = get_bizyair_api_key()
        
        if not api_key or not task_id.strip():
            return ("错误: 缺少API密钥或任务ID", "", torch.zeros((1, 64, 64, 3), dtype=torch.float32))
        
        # 检查任务状态的API端点
        url = f"https://api.bizyair.cn/w/v1/webapp/task/{task_id}"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            status = result.get('status', 'Unknown')
            
            status_info = f"任务状态: {status}\n"
            status_info += f"创建时间: {result.get('created_at', 'N/A')}\n"
            status_info += f"更新时间: {result.get('updated_at', 'N/A')}\n"
            
            if status == 'Failed' and 'outputs' in result:
                status_info += "\n错误详情:\n"
                for output in result['outputs']:
                    if 'error_msg' in output:
                        status_info += f"错误信息: {output['error_msg'][:200]}...\n"
            
            # 获取图像
            image_url = ""
            image_tensor = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
            
            if status == 'Completed' and 'outputs' in result and len(result['outputs']) > 0:
                image_url = result['outputs'][0].get('object_url', '')
                if image_url:
                    image_tensor = url_to_tensor(image_url)
            
            return (status_info, image_url, image_tensor)
            
        except Exception as e:
            error_info = f"检查任务状态失败: {str(e)}"
            return (error_info, "", torch.zeros((1, 64, 64, 3), dtype=torch.float32))
