import streamlit as st
from google import genai
from google.genai import types

from prompts import (
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
    SUMMARY_REQUEST_PROMPT
)


# -----------------------------
# Page Configuration
# -----------------------------

st.set_page_config(
    page_title="SnapStudy AI",
    page_icon="📚",
    layout="centered"
)


# -----------------------------
# API Key
# -----------------------------

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]


# -----------------------------
# Gemini Client
# -----------------------------

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()


# -----------------------------
# Render Messages
# -----------------------------

def render_message(message):

    with st.chat_message(message["role"]):

        if message["kind"] == "text":
            st.write(message["content"])

        elif message["kind"] == "image":
            st.image(message["content"])


# -----------------------------
# Add Message
# -----------------------------

def add_message(role, kind, content):

    st.session_state.messages.append(
        {
            "role": role,
            "kind": kind,
            "content": content
        }
    )

    render_message(
        st.session_state.messages[-1]
    )


# -----------------------------
# Ask Gemini
# -----------------------------

def ask_gemini(parts):

    try:

        response = st.session_state.chat.send_message(parts)

        return response.text

    except Exception as error:

        return f"Sorry, something went wrong: {error}"


# -----------------------------
# Onboarding
# -----------------------------

if "onboarded" not in st.session_state:

    st.title("📚 SnapStudy AI")

    st.caption(
        "Snap it. Understand it. Learn it."
    )

    with st.form("onboarding_form"):

        name = st.text_input(
            "Your name"
        )

        email = st.text_input(
            "Your email address"
        )

        submitted = st.form_submit_button(
            "Start Learning 🚀"
        )

        if submitted:

            if not name.strip() or not email.strip():

                st.warning(
                    "Please enter both your name and email."
                )

            else:

                st.session_state.name = name.strip()

                st.session_state.email = email.strip()

                st.session_state.chat = (
                    gemini_client.chats.create(
                        model="gemini-3.5-flash",
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT
                        )
                    )
                )

                st.session_state.messages = []

                st.session_state.onboarded = True

                st.rerun()

    st.stop()


# -----------------------------
# Email Function
# -----------------------------

def send_email(
    to_address,
    subject,
    body
):

    import smtplib
    from email.mime.text import MIMEText

    try:

        gmail_address = st.secrets["GMAIL_ADDRESS"]

        gmail_app_password = st.secrets[
            "GMAIL_APP_PASSWORD"
        ]

        message = MIMEText(body)

        message["Subject"] = subject

        message["From"] = gmail_address

        message["To"] = to_address

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465
        ) as server:

            server.login(
                gmail_address,
                gmail_app_password
            )

            server.send_message(message)

        return True, "Email sent successfully!"

    except Exception as error:

        return False, str(error)


# -----------------------------
# Header
# -----------------------------

header_col, button_col = st.columns(
    [5, 2]
)

with header_col:

    st.title("📚 SnapStudy AI")

with button_col:

    send_disabled = (
        len(st.session_state.messages) <= 1
    )

    if st.button(
        "📧 Send Notes",
        disabled=send_disabled,
        use_container_width=True
    ):

        with st.spinner(
            "Preparing your study notes..."
        ):

            summary = ask_gemini(
                [SUMMARY_REQUEST_PROMPT]
            )

            success, info = send_email(
                st.session_state.email,
                "Your SnapStudy AI Notes 📚",
                summary
            )

            if success:

                st.success(
                    "Study notes sent to your email! 📧"
                )

            else:

                st.error(
                    f"Couldn't send the email: {info}"
                )


# -----------------------------
# User Information
# -----------------------------

st.caption(
    f"Student: {st.session_state.name} "
    f"| Notes will be sent to: "
    f"{st.session_state.email}"
)


# -----------------------------
# Conversation History
# -----------------------------

if not st.session_state.messages:

    add_message(
        "assistant",
        "text",
        WELCOME_MESSAGE_TEMPLATE.format(
            name=st.session_state.name
        )
    )

else:

    for message in st.session_state.messages:

        render_message(message)


# -----------------------------
# Chat Input
# -----------------------------

user_input = st.chat_input(
    "Ask a question or upload a photo...",
    accept_file=True,
    file_type=[
        "jpg",
        "jpeg",
        "png"
    ]
)


# -----------------------------
# Process User Input
# -----------------------------

if user_input:

    photo = (
        user_input.files[0]
        if user_input.files
        else None
    )

    text = user_input.text

    parts = []


    # Image

    if photo is not None:

        photo_bytes = photo.getvalue()

        add_message(
            "user",
            "image",
            photo_bytes
        )

        parts.append(
            types.Part.from_bytes(
                data=photo_bytes,
                mime_type=photo.type
            )
        )


    # Text

    if text:

        add_message(
            "user",
            "text",
            text
        )

        parts.append(text)


    # Image without text

    elif photo is not None:

        parts.append(
            """
            Analyze this image carefully.

            Explain the question, topic, diagram,
            or notes in simple language.

            If it is a problem, solve it step by step.
            If it is a diagram or notes, explain the
            important concepts and key points.
            """
        )


    # Gemini Response

    with st.spinner(
        "SnapStudy AI is thinking... 🤔"
    ):

        answer = ask_gemini(parts)

        add_message(
            "assistant",
            "text",
            answer
        )