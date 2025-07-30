"""
Claude API wrapper for multilingual risk evaluation.
"""
import os
import time
from typing import List, Dict, Any, Optional
import logging
from .base_model import BaseModel

logger = logging.getLogger(__name__)

try:
    import anthropic
except ImportError:
    anthropic = None
    logger.warning("Anthropic package not installed. Claude models will not be available.")


class ClaudeModel(BaseModel):
    """Claude API wrapper."""
    
    def __init__(self, model_name: str = "claude-3-sonnet-20240229", api_key: Optional[str] = None, **kwargs):
        super().__init__(model_name, api_key)
        
        if anthropic is None:
            raise ImportError("anthropic package is required for Claude models. Install with: pip install anthropic")
        
        # Get API key from environment if not provided
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable or api_key parameter is required")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.max_tokens = kwargs.get("max_tokens", 1000)
        self.temperature = kwargs.get("temperature", 0.7)
        self.rate_limit_delay = kwargs.get("rate_limit_delay", 1.0)
        
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using Claude API."""
        try:
            max_tokens = kwargs.get("max_tokens", self.max_tokens)
            temperature = kwargs.get("temperature", self.temperature)
            
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response = message.content[0].text if message.content else ""
            
            if not self.validate_response(response):
                logger.warning(f"Invalid response received for prompt: {prompt[:50]}...")
                return ""
                
            return response
            
        except Exception as e:
            logger.error(f"Error generating response with Claude: {str(e)}")
            return ""
    
    def batch_generate(self, prompts: List[str], **kwargs) -> List[str]:
        """Generate responses for multiple prompts with rate limiting."""
        responses = []
        
        for i, prompt in enumerate(prompts):
            if i > 0:  # Add delay between requests to respect rate limits
                time.sleep(self.rate_limit_delay)
                
            response = self.generate(prompt, **kwargs)
            responses.append(response)
            
            if (i + 1) % 10 == 0:  # Log progress every 10 requests
                logger.info(f"Processed {i + 1}/{len(prompts)} prompts")
        
        return responses
    
    def get_model_info(self) -> Dict[str, Any]:
        """Return Claude model information."""
        info = super().get_model_info()
        info.update({
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "provider": "Anthropic"
        })
        return info