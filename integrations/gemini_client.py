"""
Gemini API Client Integration with Production-Grade Rate Limiting
"""
import google.generativeai as genai
from typing import Dict, List, Optional, Any
from loguru import logger
from config.settings import settings
import asyncio
import hashlib

class GeminiClient:
    """Client for interacting with Google's Gemini API"""
    
    def __init__(self):
        """Initialize the Gemini client"""
        try:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro-latest')
            logger.info("Gemini client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise

    async def generate_batch_responses(
        self,
        prompts: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> List[str]:
        """
        Generate multiple responses in parallel for better performance
        
        Args:
            prompts: List of prompt dictionaries with 'prompt' and optional 'system_prompt' keys
            temperature: Sampling temperature
            max_tokens: Maximum tokens per response
            
        Returns:
            List of generated response texts in same order as input
        """
        try:
            logger.info(f"Processing {len(prompts)} API calls in parallel batch")
            
            # Create tasks for parallel execution
            tasks = []
            for prompt_data in prompts:
                task = self.generate_response(
                    prompt=prompt_data.get('prompt', ''),
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_prompt=prompt_data.get('system_prompt')
                )
                tasks.append(task)
            
            # Execute all API calls in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle any exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Batch API call {i} failed: {result}")
                    processed_results.append(f"Error: {str(result)}")
                else:
                    processed_results.append(result)
            
            logger.info(f"Completed {len(prompts)} API calls in parallel batch")
            return processed_results
            
        except Exception as e:
            logger.error(f"Error in batch API calls: {e}")
            return [f"Batch error: {str(e)}"] * len(prompts)
    
    async def generate_response(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None,
        use_cache: bool = True
    ) -> str:
        """
        Generate a response using Gemini API with caching support
        
        Args:
            prompt: The user prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt for context
            use_cache: Whether to use caching for this request
            
        Returns:
            Generated response text
        """
        # Apply rate limiting and circuit breaker protection
        try:
            from utils.rate_limiter import api_manager, RateLimitExceededError, CircuitBreakerOpenError
            
            # Check rate limiting
            rate_limiter = api_manager.get_rate_limiter('gemini_api')
            allowed, info = await rate_limiter.is_allowed()
            
            if not allowed:
                logger.warning(f"Gemini API rate limit exceeded: {info}")
                # Return cached response if available during rate limiting
                if use_cache:
                    try:
                        from utils.cache import performance_cache
                        prompt_hash = hashlib.md5(
                            f"{prompt}_{temperature}_{max_tokens}".encode()
                        ).hexdigest()
                        cached_response = await performance_cache.get_api_response(prompt_hash)
                        if cached_response:
                            logger.info("Using cached response due to rate limiting")
                            return cached_response
                    except ImportError:
                        pass
                
                return f"Rate limit exceeded. Retry after {info.get('retry_after', 60)} seconds."
            
        except ImportError:
            logger.debug("Rate limiting not available")
        
        try:
            # Combine system prompt and user prompt if system prompt exists
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"SYSTEM: {system_prompt}\n\nUSER: {prompt}"
            
            # Check cache if enabled
            if use_cache:
                prompt_hash = hashlib.md5(
                    f"{full_prompt}_{temperature}_{max_tokens}".encode()
                ).hexdigest()
                
                try:
                    from utils.cache import performance_cache
                    cached_response = await performance_cache.get_api_response(prompt_hash)
                    if cached_response:
                        logger.debug(f"Using cached response for prompt: {prompt[:50]}...")
                        return cached_response
                except ImportError:
                    logger.warning("Performance cache not available")
            
            # Apply circuit breaker protection
            try:
                from utils.rate_limiter import api_manager
                circuit_breaker = api_manager.get_circuit_breaker('gemini_api')
                
                async def _make_api_call():
                    generation_config = genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                        top_p=0.8,
                        top_k=40
                    )
                    
                    response = await self.model.generate_content_async(
                        full_prompt,
                        generation_config=generation_config
                    )
                    return response.text
                
                response_text = await circuit_breaker.call(_make_api_call)
                
            except (ImportError, CircuitBreakerOpenError) as e:
                if isinstance(e, CircuitBreakerOpenError):
                    logger.warning(f"Gemini API circuit breaker open: {e}")
                    # Try to return cached response as fallback
                    if use_cache:
                        try:
                            from utils.cache import performance_cache
                            cached_response = await performance_cache.get_api_response(prompt_hash)
                            if cached_response:
                                logger.info("Using cached response due to circuit breaker")
                                return cached_response
                        except ImportError:
                            pass
                    return "Service temporarily unavailable. Using fallback response."
                else:
                    # Fallback to direct API call if circuit breaker not available
                    generation_config = genai.types.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                        top_p=0.8,
                        top_k=40
                    )
                    
                    response = await self.model.generate_content_async(
                        full_prompt,
                        generation_config=generation_config
                    )
                    response_text = response.text
            
            # Cache the response if enabled
            if use_cache:
                try:
                    from utils.cache import performance_cache
                    await performance_cache.set_api_response(prompt_hash, response_text)
                except ImportError:
                    pass
            
            logger.debug(f"Gemini response generated for prompt: {prompt[:100]}...")
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating Gemini response: {e}")
            return f"Error: Unable to generate response - {str(e)}"
    
    def generate_response_sync(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Synchronous version of generate_response
        
        Args:
            prompt: The user prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt for context
            
        Returns:
            Generated response text
        """
        try:
            # Combine system prompt and user prompt if system prompt exists
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"SYSTEM: {system_prompt}\n\nUSER: {prompt}"
            
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=0.8,
                top_k=40
            )
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            logger.debug(f"Gemini response generated for prompt: {prompt[:100]}...")
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating Gemini response: {e}")
            return f"Error: Unable to generate response - {str(e)}"
    
    def extract_structured_data(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data using Gemini with a specific schema
        
        Args:
            prompt: The input text to analyze
            schema: Expected output schema
            
        Returns:
            Structured data matching the schema
        """
        system_prompt = f"""
        You are a precise data extraction assistant. Extract information from the provided text 
        and return it in JSON format matching this exact schema:
        {schema}
        
        If any field cannot be determined from the text, use null for that field.
        Return ONLY the JSON object, no additional text.
        """
        
        try:
            response = self.generate_response_sync(prompt, system_prompt=system_prompt, temperature=0.3)
            logger.debug(f"Raw Gemini response: {response}")
            
            # Try to parse JSON from response
            import json
            import re
            
            # Clean up the response
            cleaned_response = response.strip()
            
            # Try direct JSON parsing first
            try:
                return json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                logger.debug(f"Direct JSON parsing failed: {e}")
                
                # Try to extract JSON from response using more robust regex
                json_patterns = [
                    r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Simple nested objects
                    r'\{.*?\}',  # Basic object match
                    r'```json\s*(\{.*?\})\s*```',  # JSON in code blocks
                    r'```\s*(\{.*?\})\s*```',  # Generic code blocks
                ]
                
                for pattern in json_patterns:
                    json_match = re.search(pattern, response, re.DOTALL)
                    if json_match:
                        try:
                            json_str = json_match.group(1) if json_match.groups() else json_match.group(0)
                            return json.loads(json_str)
                        except json.JSONDecodeError:
                            continue
                
                # If all JSON extraction fails, try to create a basic structure
                logger.warning(f"Could not extract valid JSON from Gemini response, creating fallback structure")
                logger.debug(f"Failed response: {response}")
                return {}
                    
        except Exception as e:
            logger.error(f"Error extracting structured data: {e}")
            return {}

# Global Gemini client instance
gemini_client = GeminiClient() 






