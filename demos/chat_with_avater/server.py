import gradio as gr
from openai import OpenAI
from typing import List, Tuple

from .memory_utils import get_memory_config


class ChatAvater:
    def __init__(self):
        self.messages = []
        self.base_url = "https://api.openai.com/v1"
        self.api_key = ""
        self.model = "gpt-4o"
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

    def set_api_key(self, key: str) -> str:
        self.api_key = key
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        return "API Key has been set"

    def chat(self, message: str, model: str) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
        if not self.api_key:
            return [], [("system", "Please set API Key first")]

        self.model = model
        self.messages.append({"role": "user", "content": message})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": m["role"], "content": m["content"]} for m in self.messages]
            )

            bot_message = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": bot_message})

            # Convert message format to fit Gradio display
            chat_history = [
                (self.messages[idx]["content"], self.messages[idx+1]["content"])
                for idx in range(0, len(self.messages), 2)
            ]
            return chat_history, chat_history

        except Exception as e:
            return [], [("system", f"Error: {str(e)}")]


bot = ChatAvater()
with gr.Blocks() as demo:
    gr.Markdown("# Chat with Avater")

    with gr.Row():
        # Left column - Chat history
        with gr.Column(scale=6):
            chatbot = gr.Chatbot(label="Dialogue History", height=600)

        # Right column - Control panel
        with gr.Column(scale=4):
            with gr.Group():
                api_key_input = gr.Textbox(
                    label="OpenAI API Key",
                    placeholder="Enter your OpenAI API Key here...",
                    type="password"
                )
                api_key_button = gr.Button("Set API Key")

            with gr.Group():
                model_selector = gr.Dropdown(
                    choices=["gpt-3.5-turbo", "gpt-4", "gpt-4o"],
                    label="Select Model",
                    value="gpt-4o"
                )

            msg = gr.Textbox(label="Enter message")
            clear = gr.Button("Clear History")

    # Event handling remains unchanged
    api_key_button.click(
        fn=bot.set_api_key,
        inputs=api_key_input,
        outputs=gr.Textbox(label="Status")
    )

    msg.submit(
        fn=bot.chat,
        inputs=[msg, model_selector],
        outputs=[chatbot, chatbot]
    )

    clear.click(lambda: None, None, chatbot, queue=False)

demo.launch(share=True)
