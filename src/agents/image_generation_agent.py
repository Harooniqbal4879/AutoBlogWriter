from typing import Dict, Any
from ..utils.config import Config
from ..utils.image_pipeline import pipeline

class ImageGenerationAgent:
    """Produces custom visuals with prompt optimization"""
    def __init__(self):
        from langchain_openai import ChatOpenAI
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
        except ImportError:
            from langchain.schema import HumanMessage, SystemMessage
        self.HumanMessage = HumanMessage
        self.SystemMessage = SystemMessage
        self.llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=Config.OPENAI_TEMPERATURE,
            api_key=Config.OPENAI_API_KEY
        )

    def generate_images(self, context: Dict[str, Any]) -> Dict[str, Any]:
        import openai
        import os
        prompt = f"""
        You are a creative visual designer. Based on the following topic and context, generate 2 highly descriptive prompts for DALL-E 3 image generation.
        Topic: {context.get('topic', '')}
        Research Summary: {context.get('research_summary', '')}
        Target Audience: {context.get('target_audience', '')}
        Brand Voice: {context.get('brand_voice', '')}
        Each prompt should be unique, visually rich, and suitable for blog or social media use.
        """
        messages = [
            self.SystemMessage(content="You are a creative visual designer."),
            self.HumanMessage(content=prompt)
        ]
        response = self.llm.invoke(messages)
        prompts = [p.strip() for p in response.content.split('\n') if p.strip()]
        images = []
        openai.api_key = Config.OPENAI_API_KEY
        for p in prompts:
            try:
                dalle_response = openai.images.generate(
                    model="dall-e-3",
                    prompt=p,
                    n=1,
                    size="1024x1024"
                )
                image_url = dalle_response.data[0].url if hasattr(dalle_response, 'data') and dalle_response.data else None
                images.append(image_url or "")
            except Exception as e:
                images.append("")
        # Download, process, and store images locally
        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../generated_images/raw'))
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../generated_images/processed'))
        processed_files = pipeline(images, save_dir, output_dir, resize=(1024, 1024), fmt='PNG')
        return {
            "images": processed_files,
            "prompts": prompts
        }
