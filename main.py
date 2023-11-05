import streamlit as st
import os
import google.generativeai as palm

from PIL import Image

import numpy as np
import easyocr as ocr  # OCR

from PyPDF2 import PdfReader


# App title
st.set_page_config(page_title="AI Chatbot", page_icon=":speech_balloon:")


html_style = """
<style>
div[data-testid=stFileDropzoneInstructions] {
    visiibility: hidden;
    display: none;
}

div[data-testid=stFileUploader] > label {
    visiibility: hidden;
    display: none;
}

section[data-testid=stFileUploadDropzone]   {
    padding: 0;
}

section[data-testid=stFileUploadDropzone] > button  {
    padding: 0;
    width: calc(100%)
}

div[data-testid=chatAvatarIcon-user] + div[data-testid=stChatMessageContent] {
    text-align: right;
    padding-right:3em;
}

div[data-testid=chatAvatarIcon-user] {
    position: absolute; right: 0
}



[data-testid="column"] {
    width: calc(25% - 1rem) !important;
    flex: 1 1 calc(25% - 1rem) !important;
    min-width: calc(20% - 1rem) !important;
}



xxxdiv[data-testid="stHorizontalBlock"] {
    background: repeating-linear-gradient(-45deg, red 0%, yellow 7.14%, rgb(0,255,0) 14.28%, rgb(0,255,255) 21.4%, cyan 28.56%, blue 35.7%, magenta 42.84%, red 50%);

    
  position: sticky;
  bottom: 0px;
  padding-top: 10px;
  background: yellowgreen;
  width: 100%;
  height: 50px;
  display: flex;
  justify-content: space-around;
  align-items: center;
  box-shadow: 0px -4px 3px rgb(27 27 24 / 75%);


}
</style> 
"""
st.markdown(html_style, unsafe_allow_html=True) # CSS Hack

# Get PDF Content
def get_pdf_text(pdf_doc):
    text = ""
    pdf_reader = PdfReader(pdf_doc)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Get Photo content
def ocr_image(the_image):
    img = Image.open(the_image)

    reader = ocr.Reader(['en','ch_tra'], model_storage_directory=".model", gpu=True)
    result = ' '.join(reader.readtext(np.array(img), paragraph=True, detail = 0))
    return result


# Sidebar
with st.sidebar:
    st.title('💬 AI Chatbot')

    # login form
    if "login" not in st.session_state.keys():
        st.header("Login")
        st.warning('Please enter either an API token or an invite code', icon='⚠️')

        google_api = st.text_input('Google GenerativeAI API token:', type='password')
        invite_code = st.text_input('Invite Code:', type='password')

        def login():
            if invite_code != "":
                if invite_code in st.secrets["INVITE_CODES"].split(","):
                    st.session_state["login"] = "vip"
                    os.environ['API_TOKEN'] = st.secrets["GOOGLE_GENERATIVEAI_API_KEY"]
                else:
                    st.sidebar.error("Invalid Invite Code!" , icon="🚨")
            elif google_api != "":
                st.session_state["login"] = "api_key"
                os.environ['API_TOKEN'] = google_api

        btn_login = st.button(label="Confirm", on_click=login, use_container_width=True, type="primary")

    else:
        st.success('Thanks! Please enter your prompt', icon='👉')
        palm.configure(api_key=os.environ['API_TOKEN'])

        if "messages" in st.session_state.keys():
            if len(st.session_state.messages) == 1:
                st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

        # Bottom Bar

        uploaded_file = st.sidebar.file_uploader(accept_multiple_files=False, label="the_uploader", label_visibility="hidden")
        if uploaded_file is not None:
            with st.spinner("Uploading"):

                if str(uploaded_file.name).upper().endswith("TXT"):
                    file_content = uploaded_file.getvalue().decode("UTF-8")
                    st.session_state.messages.append({"role": "user", "content": file_content})

                elif str(uploaded_file.name).upper().endswith("PDF"):
                    file_content = get_pdf_text(uploaded_file)
                    st.session_state.messages.append({"role": "user", "content": file_content})

                elif str(uploaded_file.name).upper().endswith("JPG") or str(uploaded_file.name).upper().endswith("JPEG"):
                    file_content = ocr_image(uploaded_file)
                    st.session_state.messages.append({"role": "user", "content": file_content})

                elif str(uploaded_file.name).upper().endswith("PNG"):
                    file_content = ocr_image(uploaded_file)
                    st.session_state.messages.append({"role": "user", "content": file_content})

                elif str(uploaded_file.name).upper().endswith("GIF"):
                    file_content = ocr_image(uploaded_file)
                    st.session_state.messages.append({"role": "user", "content": file_content})


                else:
                    st.write("File Format not supported: " + uploaded_file.name)


def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
    if "convo" in st.session_state.keys():
        del st.session_state["convo"]



# Store generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "👈 Please login using the sidebar"}]
else:
    if "convo" in st.session_state.keys():
        st.sidebar.button('Clear Chat History', on_click=clear_chat_history, use_container_width=True)

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# Function for generating GenerativeAI response
def generate_ai_response(prompt_input):
    string_dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            string_dialogue += "User: " + dict_message["content"] + "\n\n"
        else:
            string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"

    if "convo" not in st.session_state.keys():
        convo = palm.chat(messages=f"{string_dialogue} {prompt_input} Assistant: ")
        st.session_state.convo = convo
    else:
        convo =  st.session_state["convo"] 
        convo = convo.reply(f"{prompt_input} Assistant: ")
    output = convo.last
    return output

# User-provided prompt
if prompt := st.chat_input(disabled= "login" not in st.session_state.keys()):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)



def send_msg():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)



# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_ai_response(prompt)
            placeholder = st.empty()
            full_response = response
            #for item in response:
            #    full_response += item
            #    placeholder.markdown(full_response)
            placeholder.markdown(full_response)
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)
