import requests

def call_llm_api(api_url: str, api_key: str, model_name: str, prompt: str, temperature: float = 0.7):
    """
    标准兼容格式的大语言模型 API 调用封装
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature
    }
    
    try:
        # 设置 30 秒超时，防止请求挂起导致系统卡死
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()  # 检查 HTTP 状态码
        result = response.json()
        
        # 提取并返回模型生成的文本
        return result['choices'][0]['message']['content'], None
        
    except requests.exceptions.RequestException as e:
        return None, f"网络请求异常: {str(e)}"
    except KeyError:
        return None, "解析响应失败：API 返回的 JSON 格式不兼容"
    except Exception as e:
        return None, f"未知错误: {str(e)}"