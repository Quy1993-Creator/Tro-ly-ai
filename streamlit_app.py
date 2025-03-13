import streamlit as st
from openai import OpenAI
import os
import base64
import tempfile
from PIL import Image
import io
import fitz  # PyMuPDF for PDF processing

# Hàm đọc nội dung từ file văn bản
def rfile(name_file):
    with open(name_file, "r", encoding="utf-8") as file:
        return file.read()

# Hàm chuyển đổi hình ảnh thành base64
def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# Hàm xử lý file PDF để trích xuất text và hình ảnh
def process_pdf(pdf_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_file.getvalue())
        tmp_path = tmp.name
    
    # Mở PDF với PyMuPDF
    pdf_document = fitz.open(tmp_path)
    pdf_text = ""
    pdf_images = []
    
    # Lặp qua từng trang để trích xuất text và hình ảnh
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        
        # Trích xuất text
        pdf_text += page.get_text() + "\n\n"
        
        # Trích xuất hình ảnh
        images = page.get_images(full=True)
        for img_index, img_info in enumerate(images):
            xref = img_info[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            
            # Chuyển thành đối tượng PIL Image
            try:
                image = Image.open(io.BytesIO(image_bytes))
                pdf_images.append(image)
            except Exception as e:
                st.error(f"Không thể xử lý hình ảnh trong PDF: {e}")
    
    # Đóng tài liệu PDF và xóa file tạm
    pdf_document.close()
    os.unlink(tmp_path)
    
    return pdf_text, pdf_images

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

# Lấy OpenAI API key từ st.secrets
openai_api_key = st.secrets.get("OPENAI_API_KEY")

# Khởi tạo OpenAI client
client = OpenAI(api_key=openai_api_key)

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
        .file-upload {
            padding: 10px;
            border-radius: 10px;
            max-width: 75%;
            background-color: #f0f2f6;
            text-align: left;
        }
        .uploaded-image {
            max-width: 100%;
            border-radius: 5px;
            margin-top: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Hiển thị lịch sử tin nhắn (loại bỏ system để tránh hiển thị)
for message in st.session_state.messages:
    if message["role"] == "assistant":
        st.markdown(f'<div class="assistant">{message["content"]}</div>', unsafe_allow_html=True)
    elif message["role"] == "user":
        # Kiểm tra xem tin nhắn có chứa hình ảnh không
        if "image_data" in message:
            st.markdown(f'<div class="user">{message["content"]}</div>', unsafe_allow_html=True)
            st.image(message["image_data"], caption="Uploaded Image", use_column_width=True)
        # Kiểm tra xem tin nhắn có chứa thông tin PDF không
        elif "pdf_text" in message:
            st.markdown(f'<div class="user">{message["content"]}</div>', unsafe_allow_html=True)
            with st.expander("Xem nội dung PDF"):
                st.write(message["pdf_text"])
                if "pdf_images" in message and message["pdf_images"]:
                    st.write("Hình ảnh từ PDF:")
                    for i, img in enumerate(message["pdf_images"]):
                        st.image(img, caption=f"PDF Image {i+1}", use_column_width=True)
        else:
            st.markdown(f'<div class="user">{message["content"]}</div>', unsafe_allow_html=True)

# Khu vực upload file
st.sidebar.title("Upload files")
uploaded_file = st.sidebar.file_uploader("Choose an image or PDF file", type=["jpg", "jpeg", "png", "pdf"])

if uploaded_file is not None:
    file_content = ""
    file_type = uploaded_file.type
    
    # Xử lý hình ảnh
    if file_type in ["image/jpeg", "image/png", "image/jpg"]:
        image = Image.open(uploaded_file)
        st.sidebar.image(image, caption="Uploaded Image", use_column_width=True)
        
        # Chuyển đổi hình ảnh thành base64 để gửi tới API
        base64_image = image_to_base64(image)
        file_content = f"[User uploaded an image]"
        
        # Tạo tin nhắn gửi cho AI
        if st.sidebar.button("Process Image"):
            user_message = "Đây là hình ảnh mà tôi vừa upload. Vui lòng phân tích và mô tả nó."
            
            # Lưu tin nhắn người dùng kèm hình ảnh vào session
            st.session_state.messages.append({
                "role": "user", 
                "content": user_message,
                "image_data": image
            })
            
            # Hiển thị tin nhắn người dùng trên giao diện
            st.markdown(f'<div class="user">{user_message}</div>', unsafe_allow_html=True)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            
            # Gửi tin nhắn kèm hình ảnh tới API
            messages_for_api = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages 
                               if "image_data" not in m or m["role"] != "user"]
            
            # Thêm tin nhắn cuối cùng với hình ảnh
            messages_for_api.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": user_message},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]
            })
            
            # Tạo phản hồi từ API OpenAI (model hỗ trợ xử lý hình ảnh)
            model_name = rfile("module_chatgpt.txt").strip()
            
            # Kiểm tra nếu model không hỗ trợ vision
            if "vision" not in model_name and "gpt-4" not in model_name:
                response = "Xin lỗi, model hiện tại không hỗ trợ phân tích hình ảnh. Vui lòng sử dụng model gpt-4-vision-preview hoặc tương tự."
                st.markdown(f'<div class="assistant">{response}</div>', unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                # Gọi API với multimodal
                response = ""
                try:
                    stream = client.chat.completions.create(
                        model=model_name,
                        messages=messages_for_api,
                        stream=True,
                        max_tokens=1000
                    )
                    
                    # Ghi lại phản hồi của trợ lý vào biến
                    for chunk in stream:
                        if chunk.choices:
                            content = chunk.choices[0].delta.content
                            if content:
                                response += content
                    
                    # Hiển thị phản hồi của trợ lý
                    st.markdown(f'<div class="assistant">{response}</div>', unsafe_allow_html=True)
                    
                    # Cập nhật lịch sử tin nhắn trong session
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Error with OpenAI API: {str(e)}")
    
    # Xử lý PDF
    elif file_type == "application/pdf":
        st.sidebar.write("PDF uploaded successfully!")
        
        # Xử lý PDF để trích xuất text và hình ảnh
        pdf_text, pdf_images = process_pdf(uploaded_file)
        
        # Hiển thị PDF preview trong sidebar
        with st.sidebar.expander("PDF Preview"):
            st.write(pdf_text[:500] + "..." if len(pdf_text) > 500 else pdf_text)
            if pdf_images:
                st.image(pdf_images[0], caption="First image from PDF", use_column_width=True)
        
        # Tạo tin nhắn gửi cho AI
        if st.sidebar.button("Process PDF"):
            user_message = "Đây là nội dung PDF mà tôi vừa upload. Vui lòng phân tích và tóm tắt nó."
            
            # Lưu tin nhắn người dùng kèm thông tin PDF vào session
            st.session_state.messages.append({
                "role": "user", 
                "content": user_message,
                "pdf_text": pdf_text,
                "pdf_images": pdf_images
            })
            
            # Hiển thị tin nhắn người dùng trên giao diện
            st.markdown(f'<div class="user">{user_message}</div>', unsafe_allow_html=True)
            with st.expander("Xem nội dung PDF"):
                st.write(pdf_text)
                if pdf_images:
                    st.write("Hình ảnh từ PDF:")
                    for i, img in enumerate(pdf_images):
                        st.image(img, caption=f"PDF Image {i+1}", use_column_width=True)
            
            # Gửi text từ PDF tới API
            messages_for_api = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages 
                               if "pdf_text" not in m or m["role"] != "user"]
            
            # Thêm tin nhắn cuối cùng với nội dung PDF
            messages_for_api.append({
                "role": "user",
                "content": f"{user_message}\n\nNội dung PDF:\n{pdf_text[:4000] if len(pdf_text) > 4000 else pdf_text}"
            })
            
            # Tạo phản hồi từ API OpenAI
            response = ""
            try:
                stream = client.chat.completions.create(
                    model=rfile("module_chatgpt.txt").strip(),
                    messages=messages_for_api,
                    stream=True,
                    max_tokens=1500
                )
                
                # Ghi lại phản hồi của trợ lý vào biến
                for chunk in stream:
                    if chunk.choices:
                        content = chunk.choices[0].delta.content
                        if content:
                            response += content
                
                # Hiển thị phản hồi của trợ lý
                st.markdown(f'<div class="assistant">{response}</div>', unsafe_allow_html=True)
                
                # Cập nhật lịch sử tin nhắn trong session
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error with OpenAI API: {str(e)}")

# Ô nhập liệu cho người dùng
if prompt := st.chat_input("Bạn nhập nội dung cần trao đổi ở đây nhé?"):
    # Lưu tin nhắn người dùng vào session
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f'<div class="user">{prompt}</div>', unsafe_allow_html=True)

    # Tạo phản hồi từ API OpenAI
    response = ""
    stream = client.chat.completions.create(
        model=rfile("module_chatgpt.txt").strip(),
        messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        stream=True,
    )

    # Ghi lại phản hồi của trợ lý vào biến
    for chunk in stream:
        if chunk.choices:
            content = chunk.choices[0].delta.content
            if content:
                response += content

    # Hiển thị phản hồi của trợ lý