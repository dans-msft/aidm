"""LLM client module."""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union, NoReturn
from requests import HTTPError, Response

from .base import LLMProvider, LLMError
from .openai import OpenAI
from .anthropic import Anthropic

logger = logging.getLogger(__name__)

class LLMClient:
    """Client for interacting with the LLM API."""
    
    def __init__(
        self,
        endpoint: str,
        api_key: str,
        provider: str = 'anthropic'
    ) -> None:
        """Initialize the LLM client.
        
        Args:
            endpoint: The LLM API endpoint URL (not used with OpenAI provider).
            api_key: The API key for the LLM provider.
            provider: The LLM provider to use ('openai' or 'anthropic').
        """
        self.api_key = api_key
        
        # Initialize the appropriate provider
        if provider == 'openai':
            self.provider: LLMProvider = OpenAI(api_key=self.api_key)
            print('Initializing LLM client with OpenAI provider')
        elif provider == 'anthropic':
            self.provider: LLMProvider = Anthropic(api_key=self.api_key)
            print('Initializing LLM client with Anthropic provider')
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def _handle_error(self, error: Exception, response: Optional[Response] = None) -> NoReturn:
        """Handle API errors and raise detailed LLMError.
        
        Args:
            error: The original exception.
            response: Optional response object from the request.
            
        Raises:
            LLMError: Detailed error with status code and response content.
        """
        if isinstance(error, HTTPError) and response is not None:
            try:
                content = response.text
            except Exception:
                content = "Unable to read response content"
            raise LLMError(
                message=str(error),
                status_code=response.status_code,
                response_content=content
            )
        # For other types of errors, wrap them in LLMError
        raise LLMError(f"Unexpected error: {str(error)}")
    
    def make_structured_request(
        self,
        prompt: Optional[str],
        context: List[Tuple[str, str]] = [],
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        name: str = "structure",
        use_detailed_model: bool = False
    ) -> Dict[str, Any]:
        """Make a structured request to the LLM API.
        
        Args:
            prompt: The user prompt to send.
            context: List of context tuples.  Each tuple is a pair of (user command, agent response).
            system_prompt: Optional system prompt to guide the LLM.
            schema: Optional JSON schema for the response.
            name: name to associate with the structured schema.
            use_detailed_model: True to use a more intensive/expensive model.
            
        Returns:
            The parsed JSON content from the LLM response.
            
        Raises:
            LLMError: If the request fails, with detailed error information.
        """
        try:
            augmented_system_prompt = (system_prompt or "") + '\nRespond only in JSON with no extra characters'
            messages = [
                {"role": "system", "content": augmented_system_prompt}
            ]
            for context_entry in context:
                messages.append({"role": "user", "content": context_entry[0]})
                messages.append({"role": "assistant", "content": context_entry[1]})

            if prompt:                
                messages.append({"role": "user", "content": prompt})
            
            if schema:
                return self.provider.structured_completion(
                    messages=messages,
                    schema=schema,
                    name=name,
                    temperature=0.7,
                    max_tokens=1000,
                    use_detailed_model=use_detailed_model
                )
            else:
                return self.provider.chat_completion(
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                
        except Exception as e:
            self._handle_error(e)  # type: ignore  # This will never return normally
    
    def make_self_play_request(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        conversation_context: Optional[List[Tuple[str, str]]] = None
    ) -> str:
        """Make a self-play request to the LLM API.
        
        Args:
            prompt: The user prompt to send.
            system_prompt: Optional system prompt to guide the LLM.
            conversation_context: Optional list of (user, assistant) message pairs.
            
        Returns:
            The player's response as a string.
            
        Raises:
            LLMError: If the request fails, with detailed error information.
        """
        try:
            messages = [
                {"role": "system", "content": system_prompt or "You are a player in a role-playing game."}
            ]
            
            if conversation_context:
                for user_msg, assistant_msg in conversation_context:
                    messages.append({"role": "user", "content": user_msg})
                    messages.append({"role": "assistant", "content": assistant_msg})
            
            messages.append({"role": "user", "content": prompt})
            
            response = self.provider.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response["message"]["content"]
        except Exception as e:
            self._handle_error(e)  # type: ignore  # This will never return normally 