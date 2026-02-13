import os

import requests
import streamlit as st

DEFAULT_BACKEND_URL = "http://localhost:8000/v1/chat/completions"
DEFAULT_MODEL = "echo-langgraph"
DEFAULT_LOG_LIMIT = 10


def short_text(value: str, max_len: int = 40) -> str:
    if len(value) <= max_len:
        return value
    return value[: max_len - 3] + "..."


def build_logs_url(chat_url: str) -> str:
    marker = "/chat/completions"
    if marker in chat_url:
        return chat_url.split(marker, 1)[0] + "/logs"
    return chat_url.rstrip("/") + "/logs"


def fetch_db_logs(chat_url: str, api_key: str, timeout_s: int, limit: int) -> list[dict]:
    logs_url = f"{build_logs_url(chat_url)}?limit={limit}"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(logs_url, headers=headers, timeout=timeout_s)
    response.raise_for_status()
    payload = response.json()
    return payload.get("data", [])


def delete_db_log(chat_url: str, api_key: str, timeout_s: int, log_id: int) -> None:
    logs_url = f"{build_logs_url(chat_url)}/{log_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.delete(logs_url, headers=headers, timeout=timeout_s)
    response.raise_for_status()


st.set_page_config(page_title="support chatbot", page_icon=":speech_balloon:", layout="centered")
st.title("support chatbot")
st.caption("ask me anything about product X")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "db_logs" not in st.session_state:
    st.session_state.db_logs = []

with st.sidebar:
    st.subheader("Connection")
    backend_url = st.text_input("Backend URL", value=os.getenv("BACKEND_URL", DEFAULT_BACKEND_URL))
    model_id = st.text_input("Model", value=os.getenv("MODEL_ID", DEFAULT_MODEL))
    api_key = st.text_input("API Key", value=os.getenv("API_KEY", "pfe-local-key"), type="password")
    timeout_s = st.number_input("Timeout (seconds)", min_value=5, max_value=120, value=30)
    logs_limit = st.number_input("History limit", min_value=1, max_value=100, value=DEFAULT_LOG_LIMIT)

    if st.button("Refresh DB History"):
        try:
            st.session_state.db_logs = fetch_db_logs(
                backend_url, api_key, int(timeout_s), int(logs_limit)
            )
            st.success(f"Loaded {len(st.session_state.db_logs)} rows from database.")
        except Exception as exc:
            st.error(f"Could not load DB history: {exc}")

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    st.subheader("History")
    if not st.session_state.db_logs:
        st.caption("No DB history yet.")
    else:
        labels = [
            (
                f"#{row.get('id')} | {str(row.get('created_at', ''))[:19]} | "
                f"{short_text(str(row.get('user_message', '')))}"
            )
            for row in st.session_state.db_logs
        ]
        selected_index = st.radio(
            "Recent conversations",
            options=list(range(len(labels))),
            format_func=lambda idx: labels[idx],
            label_visibility="collapsed",
        )
        selected_row = st.session_state.db_logs[selected_index]
        st.caption("Selected item")
        st.markdown(f"**User:** {selected_row.get('user_message', '')}")
        st.markdown(f"**Assistant:** {selected_row.get('assistant_message', '')}")

        if st.button("Delete selected", type="secondary"):
            try:
                delete_db_log(
                    backend_url, api_key, int(timeout_s), int(selected_row.get("id", 0))
                )
                st.session_state.db_logs = fetch_db_logs(
                    backend_url, api_key, int(timeout_s), int(logs_limit)
                )
                st.success("Conversation deleted from DB.")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not delete conversation: {exc}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Type your message...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    assistant_text = ""
    with st.chat_message("assistant"):
        try:
            response = requests.post(backend_url, headers=headers, json=payload, timeout=int(timeout_s))
            response.raise_for_status()
            data = response.json()
            assistant_text = data["choices"][0]["message"]["content"]
            st.markdown(assistant_text)
        except Exception as exc:
            assistant_text = f"Error: {exc}"
            st.error(assistant_text)

    st.session_state.messages.append({"role": "assistant", "content": assistant_text})
    try:
        st.session_state.db_logs = fetch_db_logs(backend_url, api_key, int(timeout_s), int(logs_limit))
    except Exception:
        # Keep chat usable even if history refresh fails.
        pass
