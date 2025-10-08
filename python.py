# =========================
# 💬 KHUNG CHAT AI (ADD-ON)
# Dán đoạn này vào CUỐI FILE, không cần sửa gì ở phần trên
# =========================

st.markdown("---")
st.header("💬 Chat AI về Báo cáo Tài chính")

# Khởi tạo bộ nhớ hội thoại trong session
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "assistant", "content": "Xin chào! Mình là trợ lý phân tích tài chính. Bạn có thể hỏi về tăng trưởng, cơ cấu tài sản, khả năng thanh toán… hoặc gửi yêu cầu giải thích thêm dựa trên bảng bạn đã tải lên."}
    ]

# Hiển thị lịch sử chat
for m in st.session_state.chat_messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])

# Tuỳ chọn: đính kèm bối cảnh từ bảng đã xử lý vào câu hỏi
attach_context = st.checkbox(
    "Đính kèm bối cảnh từ bảng đã xử lý (nếu có)",
    value=True,
    help="Nếu đã tải file và xử lý xong, khung chat sẽ gửi kèm phần tóm tắt bảng để AI trả lời sát dữ liệu."
)

# Hộp nhập chat
user_prompt = st.chat_input("Nhập câu hỏi hoặc yêu cầu của bạn…")
if user_prompt:
    # 1) Ghi câu hỏi của người dùng vào khung chat
    st.session_state.chat_messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)

    # 2) Chuẩn bị bối cảnh (nếu có bảng đã xử lý)
    context_text = ""
    try:
        if attach_context and "df_processed" in locals() and isinstance(df_processed, pd.DataFrame):
            # Chỉ trích xuất 10 dòng đầu để gọn nhẹ
            preview_rows = min(10, len(df_processed))
            context_text = (
                "### Ngữ cảnh dữ liệu (trích gọn):\n"
                + df_processed.head(preview_rows).to_markdown(index=False)
                + "\n\nLưu ý: Bảng trên là trích gọn từ dữ liệu đã xử lý trong phiên làm việc."
            )
        elif attach_context:
            context_text = "### Ngữ cảnh dữ liệu: Chưa có bảng đã xử lý trong phiên hiện tại."
    except Exception:
        # Không chặn chat nếu vì lý do nào đó chưa có df_processed
        context_text = "### Ngữ cảnh dữ liệu: Không truy cập được bảng đã xử lý."

    # 3) Gọi Gemini trả lời
    with st.chat_message("assistant"):
        with st.spinner("Đang phân tích với Gemini…"):
            try:
                api_key = st.secrets.get("GEMINI_API_KEY", None)
                if not api_key:
                    raise KeyError("Thiếu secrets 'GEMINI_API_KEY'.")

                client = genai.Client(api_key=api_key)
                model_name = "gemini-2.5-flash"

                system_instructions = (
                    "Bạn là chuyên gia phân tích tài chính doanh nghiệp. "
                    "Giải thích ngắn gọn, mạch lạc, có cấu trúc. "
                    "Nếu người dùng hỏi về số liệu, hãy tham chiếu các cột như 'Năm trước', 'Năm sau', "
                    "'Tốc độ tăng trưởng (%)', 'Tỷ trọng…' nếu bối cảnh có."
                )

                full_prompt = f"""
{system_instructions}

## Câu hỏi của người dùng:
{user_prompt}

{context_text if context_text else ""}
"""

                resp = client.models.generate_content(
                    model=model_name,
                    contents=full_prompt
                )
                ai_text = (resp.text or "").strip() if resp else "Không nhận được phản hồi từ mô hình."

            except APIError as e:
                ai_text = f"Lỗi gọi Gemini API: {e}"
            except KeyError as e:
                ai_text = f"Lỗi cấu hình: {e}. Vui lòng bổ sung `GEMINI_API_KEY` trong Streamlit secrets."
            except Exception as e:
                ai_text = f"Đã xảy ra lỗi không xác định khi gọi AI: {e}"

            # Hiển thị và lưu vào lịch sử chat
            st.write(ai_text)
            st.session_state.chat_messages.append({"role": "assistant", "content": ai_text})

# Hàng tiện ích xoá hội thoại
col_a, col_b = st.columns([1, 2])
with col_a:
    if st.button("🗑️ Xoá hội thoại"):
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hội thoại đã được đặt lại. Mình có thể giúp gì cho bạn?"}
        ]
        st.rerun()
with col_b:
    st.caption("Mẹo: Bật 'Đính kèm bối cảnh' để câu trả lời bám sát dữ liệu bạn vừa phân tích.")
