from app.config.settings import settings
from langchain_groq import ChatGroq

class LLMProvider:
    @staticmethod
    def get_openai_llm(model_name: str):
        pass

    @staticmethod
    def get_gemini_llm(model_name: str):
        pass

    @staticmethod
    def get_groq_llm(model_name: str):
        return ChatGroq(
            model=model_name,
            api_key=settings.GROQ_API_KEY,
            streaming=True,
            temperature=0.6,
        )

    @staticmethod
    def get_refiner_llm():
        return ChatGroq(
            model=settings.analyzer_model,
            api_key=settings.GROQ_API_KEY,
            streaming=True,
            temperature=0.3,
        )