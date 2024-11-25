import gradio as gr
from openai import OpenAI
from typing import List, Tuple


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
        return "API Key 已设置"

    def chat(self, message: str, model: str) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
        if not self.api_key:
            return [], [("system", "请先设置 API Key")]

        self.model = model
        self.messages.append({"role": "user", "content": message})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": m["role"], "content": m["content"]} for m in self.messages]
            )

            bot_message = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": bot_message})

            # 转换消息格式以适应 Gradio 的显示
            chat_history = [
                (self.messages[idx]["content"], self.messages[idx+1]["content"])
                for idx in range(0, len(self.messages), 2)
            ]
            return chat_history, chat_history

        except Exception as e:
            return [], [("system", f"错误：{str(e)}")]


bot = ChatAvater()

with gr.Blocks() as demo:
    gr.Markdown("# ChatGPT 对话界面")

    with gr.Row():
        api_key_input = gr.Textbox(
            label="OpenAI API Key",
            placeholder="在此输入你的 OpenAI API Key...",
            type="password"
        )
        api_key_button = gr.Button("设置 API Key")

    with gr.Row():
        model_selector = gr.Dropdown(
            choices=["gpt-3.5-turbo", "gpt-4", "gpt-4o"],
            label="选择模型",
            value="gpt-4o"
        )

    chatbot = gr.Chatbot(label="对话历史")
    msg = gr.Textbox(label="输入消息")
    clear = gr.Button("清除对话")

    api_key_button.click(
        fn=bot.set_api_key,
        inputs=api_key_input,
        outputs=gr.Textbox(label="状态")
    )

    msg.submit(
        fn=bot.chat,
        inputs=[msg, model_selector],
        outputs=[chatbot, chatbot]
    )

    clear.click(lambda: None, None, chatbot, queue=False)

demo.launch(share=True)
