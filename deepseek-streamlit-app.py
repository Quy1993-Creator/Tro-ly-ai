import streamlit as st
from deepseek import DeepSeekAPI
import os

# Hàm đọc nội dung từ file văn bản
def rfile(name_file):
    with open(name_file, "r", encoding="utf-8") as file:
        return file.read()

# Hiển thị logo (nếu có)
try:
    col1, col2, col3 = st.columns([3, 2, 3])
    with col2:
        st.image("logo.png", use_container_width=True)
except:
    pass

# Hiển thị tiêu đề
title_content = rfile("00.xinchao.txt")
st.markdown(
    f"""<h1 style="text-align: center; font-size: 24px;">{title_content}</h1>""",
    unsafe_allow_html=True
)

# Lấy DeepSeek API key từ st.secrets
deepseek_api_key = st.secrets.get("DEEPSEEK_API_KEY")

# Khởi tạo DeepSeek client
client = DeepSeekAPI(api_key=deepseek_api_key)

# Khởi tạo tin nhắn "system" và "assistant"
INITIAL_SYSTEM_MESSAGE = {"role": "system", "content": rfile("01.system_trainning.txt")}
INITIAL_ASSISTANT_MESSAGE = {"role": "assistant", "content": rfile("02.assistant.txt")}

# Kiểm tra nếu chưa có session lưu trữ thì khởi tạo tin nhắn ban đầu
if "messages" not in st.session_state:
    st.session_state.messages = [INITIAL_SYSTEM_MESSAGE, INITIAL_ASSISTANT_MESSAGE]

# CSS để căn chỉnh trợ lý bên trái, người hỏi bên phải, và thêm icon trợ lý
st.markdown(
    """
    <style>
        .assistant {
            padding: 10px;
            border-radius: 10px;
            max-width: 75%;
            background: none; /* Màu trong suốt */
            text-align: left;
        }
        .user {
            padding: 10px;
            border-radius: 10px;
            max-width: 75%;
            background: none; /* Màu trong suốt */
            text-align: right;
            margin-left: auto;
        }
        .assistant::before { content: "🤖 "; font-weight: bold; }
    </style>
    """,
    unsafe_allow_html=True
)

# Hiển thị lịch sử tin nhắn (loại bỏ system để tránh hiển thị)
for message in st.session_state.messages:
    if message["role"] == "assistant":
        st.markdown(f'<div class="assistant">{message["content"]}</div>', unsafe_allow_html=True)
    elif message["role"] == "user":
        st.markdown(f'<div class="user">{message["content"]}</div>', unsafe_allow_html=True)

# Ô nhập liệu cho người dùng
if prompt := st.chat_input("Bạn nhập nội dung cần trao đổi ở đây nhé?"):
    # Lưu tin nhắn người dùng vào session
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f'<div class="user">{prompt}</div>', unsafe_allow_html=True)

    # Tạo phản hồi từ API DeepSeek
    response = ""
    model_name = rfile("model_deepseek.txt").strip()
    
    # Sử dụng streaming API của DeepSeek
    stream = client.chat.completions.create(
        model=model_name,
        messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        stream=True,
        temperature=0.7,  # Có thể điều chỉnh các tham số phù hợp với DeepSeek R1
    )

    # Ghi lại phản hồi của trợ lý vào biến
    for chunk in stream:
        if chunk.choices:
            delta_content = chunk.choices[0].delta.content
            if delta_content:
                response += delta_content
    
    # Hiển thị phản hồi của trợ lý
    st.markdown(f'<div class="assistant">{response}</div>', unsafe_allow_html=True)

    # Cập nhật lịch sử tin nhắn trong session
    st.session_state.messages.append({"role": "assistant", "content": response})
