import sys
import time
import os
from dotenv import load_dotenv
from groq import Groq
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QScrollArea, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent, QFont
from PyQt5 import QtWidgets

# Load environment variables from .env file
dotenv_path = '/Users/fsponline/Projects/.env'
load_dotenv(dotenv_path=dotenv_path)

# Fetch the API key from environment variables
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError("API_KEY not found in environment variables.")

# Create the Groq client
client = Groq(api_key=API_KEY)

# Set the system prompt
system_prompt = {
    "role": "system",
    "content": "I want you to become my Prompt Creator. Your goal is to help me craft the best possible prompt for my needs..."
}

# Initialize the chat history
chat_history = [system_prompt]


def get_full_response(user_input):
    """Handle potentially long responses by making multiple requests with a delay."""
    chat_history.append({"role": "user", "content": user_input})
    full_response = ""

    while True:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=chat_history,
            max_tokens=1000,  # Adjust as needed
            temperature=1.2
        )
        response_text = response.choices[0].message.content
        full_response += response_text

        # Append partial response to chat history for context
        chat_history.append({"role": "assistant", "content": response_text})

        # Check if the response is likely complete
        if len(response_text) < 1000:  # Adjust based on max_tokens
            break

        # Pause for 5 seconds before making the next request
        print("Response truncated. Pausing for 5 seconds...")
        time.sleep(5)

    return full_response


def process_text(input_text):
    """Simplify the input text for non-technical users."""
    simplified_text = input_text
    # Add any additional processing here
    return simplified_text


class SpeechBubble(QLabel):
    def __init__(self, text, is_user_message):
        super().__init__()
        self.setText(text)
        self.setWordWrap(True)  # Ensure word wrapping is enabled
        self.setFont(QFont('Poppins', 14))  # Adjust font size and style as needed
        if is_user_message:
            self.setStyleSheet("background-color: white; border: 1px solid black; padding: 10px; border-radius: 10px; color: black;")
        else:
            self.setStyleSheet("background-color: #C9E4CA; border: 1px solid black; padding: 10px; border-radius: 10px; color: black;")


class EnterKeyTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.parent and hasattr(self.parent, 'handle_send'):
                self.parent.handle_send()
                event.accept()
        else:
            super().keyPressEvent(event)


class ChatBotApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Create widgets
        self.text_edit = QVBoxLayout()
        self.text_edit.setContentsMargins(10, 10, 10, 10)
        self.text_edit.setSpacing(10)

        self.input_edit = EnterKeyTextEdit(self)
        self.input_edit.setPlaceholderText("Type your message here...")
        self.input_edit.setFixedHeight(50)
        self.input_edit.setStyleSheet("background-color: white; color: black; font-size: 14pt;")

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.handle_send)
        self.send_button.setFixedWidth(100)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        self.close_button.setFixedWidth(100)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.handle_reset)
        self.reset_button.setFixedWidth(100)

        # Create horizontal layout for buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.send_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.close_button)
        button_layout.addStretch()

        # Create scroll areas
        text_scroll_area = QScrollArea()
        text_scroll_area.setWidgetResizable(True)
        text_widget = QWidget()
        text_widget.setLayout(self.text_edit)
        text_scroll_area.setWidget(text_widget)
        text_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Set layout
        layout = QVBoxLayout()
        layout.addWidget(text_scroll_area)
        layout.addWidget(self.input_edit)
        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)
        self.setWindowTitle("Chatbot - Prompt Generator")
        self.setGeometry(100, 100, 800, 600)

    def handle_send(self):
        user_input = self.input_edit.toPlainText().strip()
        if user_input:
            chat_history.append({"role": "user", "content": user_input})

            # Display user message as a bubble
            user_bubble = SpeechBubble(user_input, is_user_message=True)
            self.text_edit.addWidget(user_bubble)

            # Get and process bot response
            bot_response = get_full_response(user_input)
            simplified_response = process_text(bot_response)
            paragraphs = simplified_response.split('\n')
            full_response = "\n".join(paragraphs)
            self.text_edit.addWidget(SpeechBubble(full_response, is_user_message=False))

            # Clear input field
            self.input_edit.clear()

            # Log conversation to a file
            with open("chatbot_output.txt", "a") as file:
                file.write(f"User: {user_input}\n")
                file.write(f"Bot: {simplified_response}\n\n")

    def handle_reset(self):
        global chat_history
        chat_history = [system_prompt]

        while self.text_edit.count():
            child = self.text_edit.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.input_edit.clear()

        with open("chatbot_output.txt", "w") as file:
            file.write("")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ChatBotApp()
    window.show()
    sys.exit(app.exec_())
