import os
import streamlit as st
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
#import speech_recognition as sr
from gtts import gTTS
import pygame
import tempfile
import threading
from streamlit_chat import message
from langchain_openai import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from pinecone import Pinecone
from langchain.chains.question_answering import load_qa_chain
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_pinecone import PineconeVectorStore

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

pc=Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name="nikitha-chatbot"

llm=ChatOpenAI(model_name="gpt-3.5-turbo-0125",temperature=0.2)
embeddings=OpenAIEmbeddings(model="text-embedding-3-large",api_key=os.environ['OPENAI_API_KEY'])

retriever_new = PineconeVectorStore(index_name=index_name, embedding=embeddings)
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "answer the questions based on the given context. if the question asked is not related to 'Osteomyelitis' then your are not aware as i only specilize in so and so.do not state what you are before evey answer. Context: {context}"),
        ("human", "{input}"),
    ]
)
question_answer_chain = create_stuff_documents_chain(llm, prompt)

chain = create_retrieval_chain(retriever_new.as_retriever(search_kwargs={'k':5}), question_answer_chain)


# Initialize GoogleTranslator from deep-translator
translator = GoogleTranslator(source='auto')
#r = sr.Recognizer()

# Initialize the state for speech recognition
if "listening" not in st.session_state:
    st.session_state.listening = False
if 'transcription' not in st.session_state:
    st.session_state.transcription = ""
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'is_speaking' not in st.session_state:
    st.session_state.is_speaking = False
if 'last_spoken_text' not in st.session_state:
    st.session_state.last_spoken_text = None
if 'speech_complete' not in st.session_state:
    st.session_state.speech_complete = True

def SpeakText(text, lang='en'):
    try:
        # Create a temporary file
        # temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        # temp_filename = temp_file.name
        # temp_file.close()
        
        st.session_state.is_speaking = True
        st.session_state.speech_complete = False
        
        # Create gTTS object with specified language
        tts = gTTS(text=text, lang=lang)
        tts.save("curr.mp3")
        
        # Initialize pygame mixer
        # pygame.mixer.init()
        # pygame.mixer.music.load("curr.mp3")
        #pygame.mixer.music.play()
        
        # Wait for the audio to finish playing
        # while pygame.mixer.music.get_busy():
        #     pygame.time.Clock().tick(10)
            
        # Cleanup
        #pygame.mixer.quit()
        # with open("curr.mp3", 'rb') as audio:
        #     st.audio(audio.read(), format='audio/mp3', autoplay=True)

        
        # time.sleep(10)
        # os.remove("curr.mp3")
        
        # After speech is complete
        st.session_state.is_speaking = False
        st.session_state.speech_complete = True
        st.session_state.last_spoken_text = text
        st.rerun()
        
    except Exception as e:
        print(f"Error in text-to-speech: {str(e)}")
        st.session_state.is_speaking = False
        st.session_state.speech_complete = True
        st.rerun()

def translate_text(text, target_language):
    if target_language == "ta":
        return translator.translate(text, target='ta')
    elif target_language == "en":
        return translator.translate(text, target='en')
    return text

# def start_listening(language='en'):
#     st.session_state.listening = True
#     st.session_state.transcription = ""
    
#     status_placeholder = st.empty()
#     with status_placeholder:
#         st.info("Listening now...")  # Show listening status
    
#     # with sr.Microphone() as source:
#     try:
#         # r.adjust_for_ambient_noise(source, duration=0.2)
#         # audio = r.listen(source, phrase_time_limit=5)
#         # Recognize speech using Google Speech Recognition with the specified language
#         text = r.recognize_google("recording.mp3", language=language)
#         print(text)
#         #text = speech_to_text(language=language, use_container_width=True, just_once=True, key='STT')
#         st.session_state.transcription = text
#         st.session_state.user_input = text  # Update user_input with recognized text
#         st.session_state.listening = False
#         status_placeholder.empty()
#         process_input()
#     except sr.UnknownValueError:
#         st.session_state.listening = False
#         status_placeholder.empty()
#     except sr.RequestError as e:
#         st.session_state.listening = False
#         status_placeholder.empty()
#     except Exception as e:
#         st.session_state.listening = False
#         status_placeholder.empty()

def process_input():
    user_input = st.session_state.user_input  # Get the user input directly
    selected_language = st.session_state.selected_language
    translated_input = translate_text(user_input, target_language="en")
    
    if translated_input:
        if translated_input.lower() in ['quit', 'exit', 'bye', 'thank you']:
            if selected_language == 'ta': 
                thank_you_msg = "இந்த போட்டைப் பயன்படுத்தியதற்கு நன்றி."
            else:
                thank_you_msg = "Thank you for using this bot. Have a great day!"
            st.session_state.user_input = ""  # Clear the input
            st.session_state.chat_history.append((user_input, thank_you_msg))
            st.success(thank_you_msg)
            st.session_state.disable_input = True

        elif translated_input.lower() in ['hi','hello','hey','good morning','good afternoon','good evening','hey there','hello there']:
            if selected_language == 'ta':
                bot_response = "வணக்கம்! நான் உங்களுக்கு எப்படி உதவ முடியும்?"
            else:
                bot_response = "Hello! How can I assist you today?"

        else:
            # Run the flow and capture the result from lang.py
            try:
                bot_response = chain.invoke({"input": f"{user_input}"})["answer"]
            except (KeyError, IndexError, TypeError) as e:
                bot_response = "Sorry, I couldn't retrieve the response."

    if selected_language == 'ta':
        translator1 = GoogleTranslator(source='en', target='ta')
        bot_response = translator1.translate(bot_response)

    # Append the original user input and the bot response to chat history
    st.session_state.chat_history.append((user_input, bot_response))
    st.session_state.transcription = ""
    st.session_state.user_input = ""
    st.rerun()  # Refresh the app to show the new messages

def eng_out():
    st.title("Chatbot for Osteomyelitis (English)")

    chat_container = st.container()
    with chat_container:
        for i, (user_msg, bot_msg) in enumerate(st.session_state.chat_history):
            message(user_msg, is_user=True, key=f"user_msg_{i}")
            message(bot_msg, key=f"bot_msg_{i}")
            
            col1, col2, col3 = st.columns([1, 4, 1])
            with col1:
                if st.button("🔊", key=f"speak_{i}"):
                    if not st.session_state.is_speaking:
                        # Pass language code based on selected language
                        obj=threading.Thread(target=SpeakText, args=(bot_msg, 'en'))
                        obj.start()
                        obj.join()
                        st.audio("curr.mp3", format='audio/mp3', autoplay=True)
                        #os.remove("curr.mp3")
                        #SpeakText(bot_msg, lang='en')

    # Show input box if not speaking or if speech is complete
    if not st.session_state.is_speaking or st.session_state.speech_complete:
        input_placeholder = "Listening..." if st.session_state.listening else "Type something..."
        user_input = st.text_input(
            input_placeholder,
            key="user_input",
            value="",
            disabled=st.session_state.listening,
            on_change=process_input
        )
        
        # col1, col2 = st.columns([1, 3])
        # with col1:
        #     st.button(
        #         "🎤 Speak", 
        #         key="speak_button",
        #         on_click=start_listening,  # Call without language parameter for English
        #         disabled=st.session_state.listening,
        #         use_container_width=True
        #     )

def tam_out():
    st.title("ஆஸ்டியோமைலிடிஸிற்கான சாட்போட் (தமிழ்)")

    chat_container = st.container()
    with chat_container:
        for i, (user_msg, bot_msg) in enumerate(st.session_state.chat_history):
            message(user_msg, is_user=True, key=f"user_msg_{i}")
            message(bot_msg, key=f"bot_msg_{i}")
            
            col1, col2, col3 = st.columns([1, 4, 1])
            with col1:
                if st.button("🔊", key=f"speak_{i}"):
                    if not st.session_state.is_speaking:
                        # For Tamil responses
                        obj=threading.Thread(target=SpeakText, args=(bot_msg, 'ta'))
                        obj.start()
                        obj.join()
                        st.audio("curr.mp3", format='audio/mp3', autoplay=True)

    # Show input box if not speaking or if speech is complete
    if not st.session_state.is_speaking or st.session_state.speech_complete:
        input_placeholder = "கேட்கிறது..." if st.session_state.listening else "எதையாவது எழுதுங்கள்..."
        user_input = st.text_input(
            input_placeholder,
            key="user_input",
            value="",
            disabled=st.session_state.listening,
            on_change=process_input
        )
        
        # col1, col2 = st.columns([1, 3])
        # with col1:
        #     st.button(
        #         "🎤 பேசவும்", 
        #         key="speak_button_ta",
        #         on_click=lambda: start_listening(language='ta-IN'),  # Call with Tamil language parameter
        #         disabled=st.session_state.listening,
        #         use_container_width=True
        #     )

def main():
    if 'selected_language' not in st.session_state:
        st.session_state.selected_language = 'en'

    language = st.radio("Choose Language", ('English', 'Tamil'))

    if language == 'English':
        st.session_state.selected_language = 'en'
        eng_out()
    else:
        st.session_state.selected_language = 'ta'
        tam_out()

if __name__ == "__main__":
    main()