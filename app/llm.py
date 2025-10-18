"""
LLM module using OpenRouter API
Handles conversation context and AI responses
"""
import os
import asyncio
from typing import List, Dict, Optional
from openai import AsyncOpenAI
import logging

logger = logging.getLogger(__name__)


class LLMHandler:
    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-3.5-turbo",
        base_url: str = "https://openrouter.ai/api/v1"
    ):
        """
        Initialize LLM Handler for OpenRouter
        
        Args:
            api_key: OpenRouter API key
            model: Model to use (e.g., openai/gpt-3.5-turbo)
            base_url: OpenRouter API base URL
        """
        self.api_key = api_key
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            max_retries=2,
            timeout=30.0
        )
        self.conversation_history: List[Dict[str, str]] = []
        self.system_prompt = self._get_system_prompt()
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI interviewer"""
        role = os.getenv("INTERVIEWER_ROLE", "professional technical interviewer")
        return f"""You are a {role} conducting a comprehensive job interview. 

Your role is to:
- Ask relevant, insightful questions about the candidate's experience, skills, and projects
- Listen carefully to their answers and show genuine interest
- Ask thoughtful follow-up questions to dive deeper into their responses
- Evaluate both technical competence and soft skills like communication and problem-solving
- Provide a professional, friendly, and encouraging interview experience
- Keep responses concise and conversational (2-3 sentences max per response)
- Guide the conversation naturally like a real interview
- Mix behavioral questions ("Tell me about a time when...") with technical questions
- Gradually increase the complexity of questions as the interview progresses
- End with an opportunity for the candidate to ask questions

Remember: You're not just evaluating, you're having a meaningful professional conversation.

Start by greeting the candidate and asking them to introduce themselves."""

    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []
        logger.info("Conversation history reset")
        
    async def get_response(self, user_message: str) -> str:
        """
        Get AI response for user message
        
        Args:
            user_message: User's transcribed message
            
        Returns:
            AI's response text
        """
        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Prepare messages for API
            messages = [
                {"role": "system", "content": self.system_prompt}
            ] + self.conversation_history
            
            # Call OpenRouter API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=150,
                temperature=0.7,
                stream=False
            )
            
            # Extract response
            ai_message = response.choices[0].message.content.strip()
            
            # Add AI response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": ai_message
            })
            
            logger.info(f"AI Response: {ai_message[:100]}...")
            return ai_message
            
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            return "I apologize, I'm having trouble processing that. Could you please repeat?"
    
    async def get_streaming_response(self, user_message: str):
        """
        Get streaming AI response (generator)
        
        Args:
            user_message: User's transcribed message
            
        Yields:
            Chunks of AI response text
        """
        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Prepare messages for API
            messages = [
                {"role": "system", "content": self.system_prompt}
            ] + self.conversation_history
            
            # Call OpenRouter API with streaming
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=150,
                temperature=0.7,
                stream=True
            )
            
            full_response = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
            
            # Add complete response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": full_response
            })
            
            logger.info(f"Streamed AI Response: {full_response[:100]}...")
            
        except Exception as e:
            logger.error(f"LLM streaming error: {e}")
            yield "I apologize, I'm having trouble processing that. Could you please repeat?"
    
    def get_conversation_context(self) -> List[Dict[str, str]]:
        """Get current conversation history"""
        return self.conversation_history.copy()


# Global LLM handler instance
_llm_handler: Optional[LLMHandler] = None


def get_llm_handler() -> LLMHandler:
    """Get or create global LLM handler"""
    global _llm_handler
    if _llm_handler is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not set in environment")
        model = os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")
        _llm_handler = LLMHandler(api_key, model)
    return _llm_handler
