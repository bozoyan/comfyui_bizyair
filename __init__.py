# ComfyUI BizyAir 插件初始化文件

from .BizyAIR import BA_BizyAIR_Main, BA_LoadImage, BA_Float_Value, BA_String_Value, BA_Image_Resizer, BA_Task_Status_Checker

# （必填）填写 import的类名称，命名需要唯一，key或value与其他插件冲突可能引用不了。这是决定是否能引用的关键。
# key(自定义):value(import的类名称)
NODE_CLASS_MAPPINGS = {
    
    # BizyAIR API节点
    "BA_BizyAIR_Main": BA_BizyAIR_Main,
    "BA_LoadImage": BA_LoadImage,
    "BA_Float_Value": BA_Float_Value,
    "BA_String_Value": BA_String_Value,
    "BA_Image_Resizer": BA_Image_Resizer,
    "BA_Task_Status_Checker": BA_Task_Status_Checker,
}


# （可不写）填写 ui界面显示名称，命名会显示在节点ui左上角，如不写会用类的名称显示在节点ui上
# key(自定义):value(ui显示的名称)
NODE_DISPLAY_NAME_MAPPINGS = {

  
  
    
    # BizyAIR API节点显示名称
    "BA_BizyAIR_Main": "BizyAIR API主界面~ 🎯BOZO ",
    "BA_LoadImage": "BizyAIR 图像输入~ 🎯BOZO ",
    "BA_Float_Value": "BizyAIR 数值输入~ 🎯BOZO ",
    "BA_String_Value": "BizyAIR 字符串输入~ 🎯BOZO ",
    "BA_Image_Resizer": "图像尺寸调整~ 🎯BOZO ",
    "BA_Task_Status_Checker": "BizyAIR 任务状态检查~ 🎯BOZO ",
}

WEB_DIRECTORY = "web"

# 引入以上两个字典的内容
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
