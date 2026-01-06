"""
LLM service for Gemini API integration.
"""
import google.generativeai as genai
from typing import List, Dict, Optional
import time
from ..prompts.system_prompts import build_system_prompt, build_user_prompt


class LLMService:
    """Handles interactions with the Gemini LLM API."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.0-flash-exp",
        temperature: float = 0.7,
        max_output_tokens: int = 1024,
        top_p: float = 0.9,
        top_k: int = 40,
    ):
        """
        Initialize LLM service with Gemini API.

        Args:
            api_key: Gemini API key
            model_name: Gemini model to use
            temperature: Sampling temperature (0.0-1.0)
            max_output_tokens: Maximum tokens in response
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
        """
        # Configure Gemini API
        genai.configure(api_key=api_key)

        # Store model name for later use
        self.model_name = model_name

        # Generation configuration
        self.generation_config = {
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "max_output_tokens": max_output_tokens,
        }

        # Safety settings
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
            },
        ]

        print("✓ LLM Service initialized with Gemini model")

    def generate_hint(
        self,
        question: str,
        relevant_context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        max_retries: int = 3,
    ) -> str:
        """
        Generate a hint-based response to a student's question using RAG.

        Args:
            question: Student's question
            relevant_context: Relevant context retrieved from vector store
            conversation_history: Previous conversation messages
            max_retries: Maximum number of retry attempts on failure

        Returns:
            Hint-based response from the LLM
        """
        try:
            # Create model with dynamic system instruction based on retrieved context
            system_instruction = build_system_prompt(relevant_context)
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction,
            )

            # Format conversation history
            history_text = self._format_history(conversation_history or [])

            # Build user prompt with history
            user_prompt = build_user_prompt(question, history_text)

            # Generate response with retry logic
            for attempt in range(max_retries):
                try:
                    response = model.generate_content(
                        user_prompt,
                        generation_config=self.generation_config,
                        safety_settings=self.safety_settings,
                    )

                    # Extract and return text
                    if response.candidates:
                        return response.text
                    else:
                        # Response was blocked or empty
                        if hasattr(response, 'prompt_feedback'):
                            return "I'm unable to provide a hint for that question. Could you rephrase it or ask something related to the class materials?"
                        return "I couldn't generate a hint. Please try rephrasing your question."

                except Exception as e:
                    if attempt < max_retries - 1:
                        # Wait before retrying
                        wait_time = 2 ** attempt  # Exponential backoff
                        print(f"Retry {attempt + 1}/{max_retries} after {wait_time}s: {str(e)}")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise

        except Exception as e:
            error_msg = str(e)
            print(f"Error generating hint: {error_msg}")

            # Provide user-friendly error messages
            if "API_KEY" in error_msg.upper():
                return "Configuration error: Please check that your Gemini API key is set correctly in the .env file."
            elif "RATE_LIMIT" in error_msg.upper() or "429" in error_msg:
                return "The service is experiencing high demand. Please wait a moment and try again."
            elif "QUOTA" in error_msg.upper():
                return "API quota exceeded. Please try again later."
            else:
                return f"I encountered an error while processing your question. Please try again. If the problem persists, check the server logs."

    def _format_history(self, history: List[Dict[str, str]]) -> str:
        """
        Format conversation history for the prompt.

        Args:
            history: List of message dictionaries with 'role' and 'content'

        Returns:
            Formatted history string
        """
        if not history:
            return "No previous conversation"

        formatted = []
        for msg in history:
            role = "Student" if msg.get("role") == "user" else "Assistant"
            content = msg.get("content", "")
            formatted.append(f"{role}: {content}")

        return "\n".join(formatted)

    def test_connection(self) -> bool:
        """
        Test the connection to Gemini API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.model.generate_content(
                "Say 'Hello' if you can read this.",
                generation_config={"max_output_tokens": 10},
            )
            return response.text is not None
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False
