import streamlit as st
import google.generativeai as genai
from PIL import Image
import tempfile
import os
import time

# --- 页面配置 ---
st.set_page_config(page_title="设计稿文案检查助手", page_icon="🔍", layout="centered")

st.title("🔍 设计稿文案与错别字检查工具")
st.markdown("支持上传单张图片或**多页 PDF**，AI 将帮你找出隐藏的错别字、标点错误和语病！")

# --- API Key 配置区域 ---
api_key = st.text_input("请输入你的 API Key (例如 Gemini API Key):", type="password")

if api_key:
    genai.configure(api_key=api_key)
    
    # 文件上传组件，新增了 pdf 支持
    uploaded_file = st.file_uploader("请上传设计稿 (支持 JPG, PNG, PDF 格式)", type=["jpg", "jpeg", "png", "pdf"])
    
    if uploaded_file is not None:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        # 1. 处理图片类型
        if file_extension in ['jpg', 'jpeg', 'png']:
            image = Image.open(uploaded_file)
            st.image(image, caption="已上传的设计稿", use_column_width=True)
            
            if st.button("🚀 开始检查文案"):
                with st.spinner("AI 正在像素级扫描并检查文案，请稍候..."):
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash-latest')
                        prompt = """
                        你现在是一个专业的设计稿文案校对专家。
                        请仔细阅读这张图片中的所有文本，并执行以下任务：
                        1. 提取图片中的所有文本内容。
                        2. 检查其中的错别字、错误的标点符号（如中英文标点混用）、以及明显的语病。
                        3. 以清晰的列表形式输出你的检查结果。格式如下：
                           - **原句**：[包含错误的句子]
                           - **错误**：[具体错在哪里]
                           - **建议修改**：[正确的写法]
                        如果没有发现任何错误，请直接回复：“太棒了！文案非常完美，没有发现错误。”
                        """
                        response = model.generate_content([prompt, image])
                        st.success("检查完成！")
                        st.markdown("### 📝 检查报告")
                        st.write(response.text)
                    except Exception as e:
                        st.error(f"发生错误：{e}")

        # 2. 处理 PDF 类型
        elif file_extension == 'pdf':
            st.info(f"📄 已上传 PDF 文件：{uploaded_file.name}")
            
            if st.button("🚀 开始全面检查 PDF 文案"):
                # 创建一个临时文件来保存上传的 PDF
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                    temp_pdf.write(uploaded_file.read())
                    temp_pdf_path = temp_pdf.name
                
                with st.spinner("正在上传 PDF 并进行逐页深度扫描...文件越大所需时间越长，请耐心等待 ☕"):
                    try:
                        # 使用 Gemini 的 File API 上传文档
                        gemini_file = genai.upload_file(path=temp_pdf_path, display_name=uploaded_file.name)
                        
                        # PDF 处理可能需要几秒钟，需要轮询等待状态变为 ACTIVE
                        while gemini_file.state.name == "PROCESSING":
                            time.sleep(2)
                            gemini_file = genai.get_file(gemini_file.name)
                            
                        if gemini_file.state.name == "FAILED":
                            st.error("PDF 处理失败，请检查文件是否损坏。")
                        else:
                            model = genai.GenerativeModel('gemini-1.5-flash-latest')
                            prompt = """
                            你现在是一个专业的设计稿文案校对专家。
                            这是一份多页的设计稿 PDF 文件。请你逐页仔细阅读其中的所有文本，并执行以下任务：
                            1. 检查其中的错别字、错误的标点符号（如中英文标点混用）、以及明显的语病。
                            2. 必须明确标出错误出现在**第几页**。
                            3. 以清晰的列表形式输出你的检查结果。格式如下：
                               **第 [X] 页**：
                               - **原句**：[包含错误的句子]
                               - **错误**：[具体错在哪里]
                               - **建议修改**：[正确的写法]
                            如果某一页没有错误，无需提及。如果全篇都没有错误，请回复：“太棒了！全篇文案非常完美，没有发现错误。”
                            """
                            response = model.generate_content([gemini_file, prompt])
                            st.success("检查完成！")
                            st.markdown("### 📝 PDF 检查报告")
                            st.write(response.text)
                            
                        # 清理云端和本地的临时文件
                        genai.delete_file(gemini_file.name)
                        
                    except Exception as e:
                        st.error(f"发生错误：{e}")
                    finally:
                        # 确保本地临时文件被删除，释放空间
                        if os.path.exists(temp_pdf_path):
                            os.remove(temp_pdf_path)

else:
    st.info("💡 请先输入 API Key 以启用检查功能。")
