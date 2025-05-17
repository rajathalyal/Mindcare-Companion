import streamlit as st
from groq import Groq
import time

# Initialize Groq client
client = Groq(api_key="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")

# Set page config
st.set_page_config(
    page_title="MindCare Companion",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Initialize session state for conversation history and risk score
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": """Role: You are a compassionate mental health assistant designed to assess suicide risk through conversation. Your goal is to ask questions naturally, prioritize user comfort, and identify risk factors across 6 key categories:
1. Demographics
2. Medical History
3. Behavioral/Psychological State
4. Social/Environmental Factors
5. Unstructured Cues (Text/Sentiment)
6. Temporal Changes

After each user response:
1. Ask empathetic follow-up questions to probe the 6 risk categories.
2. Update a risk score (0-10) based on new information.
3. Format your response with these sections:
   [RESPONSE]: Your conversational response
   [RISK SCORE]: X/10
   [RISK LEVEL]: Low/Medium/High
   [FACTORS]: Brief explanation of contributing factors
   [SUGGESTIONS]: Coping strategies or next steps"""
        }
    ]
    st.session_state.risk_score = 0
    st.session_state.risk_level = "Low"

# Sidebar with resources
with st.sidebar:
    st.title("🧠 MindCare Companion")
    st.markdown("### Mental Health Resources")
    st.markdown("""
    - **National Suicide Prevention Lifeline**: 112 (IN)
    - **International Association for Suicide Prevention**: [www.iasp.info/resources](https://www.iasp.info/resources)
    """)
    
    st.markdown("### Your Current Risk Assessment")
    risk_color = "risk-low"
    if st.session_state.risk_level == "Medium":
        risk_color = "risk-medium"
    elif st.session_state.risk_level == "High":
        risk_color = "risk-high"
    
    if st.button("Reset Conversation"):
        st.session_state.messages = st.session_state.messages[:1]  # Keep only system prompt
        st.session_state.risk_score = 0
        st.session_state.risk_level = "Low"
        st.rerun()

# Main chat interface
st.title("MindCare Companion")
st.caption("A compassionate mental health assistant. Share what's on your mind...")

# Display chat messages
for message in st.session_state.messages[1:]:  # Skip system prompt
    if message["role"] == "assistant":
        with st.chat_message("assistant"):
            # Parse the assistant's response to separate the risk info
            if "[RESPONSE]:" in message["content"]:
                parts = message["content"].split("[RESPONSE]:")[1].split("[RISK SCORE]:")
                response_part = parts[0].strip()
                st.markdown(f"<div class='assistant-message'>{response_part}</div>", unsafe_allow_html=True)
                
                # Extract and display risk information
                if len(parts) > 1:
                    risk_parts = parts[1].split("[RISK LEVEL]:")
                    risk_score = risk_parts[0].strip()
                    if len(risk_parts) > 1:
                        risk_level_parts = risk_parts[1].split("[FACTORS]:")
                        risk_level = risk_level_parts[0].strip()
                        if len(risk_level_parts) > 1:
                            factors_parts = risk_level_parts[1].split("[SUGGESTIONS]:")
                            factors = factors_parts[0].strip()
                            suggestions = factors_parts[1].strip() if len(factors_parts) > 1 else ""
                            
                            with st.expander("Risk Assessment Details"):
                                st.metric("Current Risk Score", risk_score)
                                st.write(f"**Level**: {risk_level}")
                                st.write(f"**Factors**: {factors}")
                                if suggestions:
                                    st.write(f"**Suggestions**: {suggestions}")
            else:
                st.markdown(f"<div class='assistant-message'>{message['content']}</div>", unsafe_allow_html=True)
    else:
        with st.chat_message("user"):
            st.markdown(f"<div class='user-message'>{message['content']}</div>", unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("How are you feeling today?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(f"<div class='user-message'>{prompt}</div>", unsafe_allow_html=True)
    
    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Get assistant response
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=st.session_state.messages,
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=True,
            stop=None,
        )
        
        # Stream the response
        for chunk in completion:
            chunk_content = chunk.choices[0].delta.content or ""
            full_response += chunk_content
            message_placeholder.markdown(f"<div class='assistant-message'>{full_response}▌</div>", unsafe_allow_html=True)
        
        message_placeholder.markdown(f"<div class='assistant-message'>{full_response}</div>", unsafe_allow_html=True)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    # Extract and update risk score from the response
    if "[RISK SCORE]:" in full_response:
        try:
            risk_info = full_response.split("[RISK SCORE]:")[1].split("/10")[0].strip()
            st.session_state.risk_score = int(risk_info)
            
            if "[RISK LEVEL]:" in full_response:
                risk_level = full_response.split("[RISK LEVEL]:")[1].split("[FACTORS]:")[0].strip()
                st.session_state.risk_level = risk_level
            
            # Rerun to update the sidebar display
            st.rerun()
        except (IndexError, ValueError):
            pass
