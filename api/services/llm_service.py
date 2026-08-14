import os
from pathlib import Path

from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate


# ============================================================
# LOAD PROJECT ENVIRONMENT
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

ENV_FILE = (
    PROJECT_ROOT /
    ".env"
)

load_dotenv(
    dotenv_path=ENV_FILE
)


# ============================================================
# CONFIGURATION
# ============================================================

GROQ_API_KEY = os.getenv(
    "GROQ_API"
)

GROQ_MODEL = (
    "openai/gpt-oss-120b"
)


# ============================================================
# VALIDATE API KEY
# ============================================================

if not GROQ_API_KEY:

    raise RuntimeError(
        "GROQ_API_KEY not found. "
        "Please add GROQ_API_KEY to "
        "C:\\major-project\\.env"
    )


# ============================================================
# LLM SERVICE
# ============================================================

class LLMService:

    def __init__(self):

        print(
            "Initializing Groq LLM..."
        )

        self.model_name = (
            GROQ_MODEL
        )

        self.llm = ChatGroq(

            model=self.model_name,

            api_key=GROQ_API_KEY,

            temperature=0.2,

            max_retries=3
        )

        print(
            f"LLM model: "
            f"{self.model_name}"
        )

        print(
            "Groq LLM initialized successfully."
        )


    # ========================================================
    # SIMPLE LLM INVOCATION
    # ========================================================

    def invoke(
        self,
        system_prompt: str,
        user_prompt: str
    ):

        prompt = ChatPromptTemplate.from_messages([

            (
                "system",
                system_prompt
            ),

            (
                "human",
                user_prompt
            )
        ])


        chain = (
            prompt
            | self.llm
        )


        response = chain.invoke({})


        return response.content