import streamlit as st
from core.llm_client import call_llm_api

st.set_page_config(page_title="LLM Sandbox", page_icon="🤖", layout="wide")
st.title("🤖 大模型 API 调试沙箱")
st.markdown("用于本地独立测试各平台大语言模型接口，调试 Prompt 与生成参数。")

# 采用表单来管理参数配置
with st.expander("⚙️ API 接口参数配置", expanded=True):
    c1, c2 = st.columns(2)
    # 默认填入兼容 OpenAI 格式的测试地址，你可以随时修改为 DeepSeek 等其他接口
    api_url = c1.text_input("API URL", value="https://api.openai.com/v1/chat/completions")
    api_key = c2.text_input("API Key", type="password", placeholder="输入密钥 (sk-...)")
    
    c3, c4 = st.columns(2)
    model_name = c3.text_input("模型名称 (Model)", value="gpt-3.5-turbo")
    temperature = c4.slider("生成温度 (Temperature)", min_value=0.0, max_value=2.0, value=0.7, step=0.1)

st.divider()

# Prompt 编辑区
prompt = st.text_area("输入测试 Prompt：", height=200, placeholder="在此输入你的提示词...")

# 提交与响应区
if st.button("🚀 发送 API 请求"):
    if not api_key:
        st.error("⚠️ 请先在上方配置 API Key。")
    elif not prompt.strip():
        st.warning("⚠️ Prompt 不能为空。")
    else:
        with st.spinner("模型推理中，请稍候..."):
            # 调用封装好的底层函数
            response, error = call_llm_api(api_url, api_key, model_name, prompt, temperature)
            
            if error:
                st.error(error)
            else:
                st.success("请求成功响应！")
                st.markdown("### ⬇️ 生成结果")
                with st.container(border=True):
                    st.write(response)