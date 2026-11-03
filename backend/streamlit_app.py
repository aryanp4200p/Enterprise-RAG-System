"""Optional local UI:  streamlit run streamlit_app.py"""
import streamlit as st

from app.pipeline import QueryBlockedError, answer_question
from app.security.rbac import list_roles

st.title("Enterprise RAG Assistant")

query = st.text_input("Ask a question")
role = st.selectbox("Select Role", list_roles())

if st.button("Submit"):
    try:
        with st.spinner("Searching the knowledge base..."):
            result = answer_question(query, role)
    except QueryBlockedError as exc:
        st.error(str(exc))
    except Exception as exc:  # noqa: BLE001 - show any backend problem to the user
        st.error(f"Something went wrong: {exc}")
    else:
        st.subheader("Answer")
        st.write(result["answer"])

        st.subheader("Retrieved Chunks")
        for chunk in result["retrieved_docs"]:
            page = f", page {chunk['page']}" if chunk["page"] else ""
            st.caption(f"{chunk['source']}{page} - {chunk['department']}")
            st.write(chunk["text"])
            st.write("------")
