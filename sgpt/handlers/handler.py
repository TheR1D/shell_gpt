import json
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional

from ..cache import Cache
from ..config import cfg
from ..function import get_function
from ..printer import MarkdownPrinter, Printer, TextPrinter
from ..role import DefaultRoles, SystemRole

completion: Callable[..., Any] = lambda *args, **kwargs: Generator[Any, None, None]

# Initialize basic kwargs without provider-specific parameters
base_url = cfg.get("API_BASE_URL")
use_litellm = cfg.get("USE_LITELLM") == "true"

additional_kwargs = {
    "timeout": int(cfg.get("REQUEST_TIMEOUT")),
    "api_key": cfg.get("OPENAI_API_KEY"),
    "base_url": None if base_url == "default" else base_url,
}

if use_litellm:
    import litellm  # type: ignore

    completion = litellm.completion
    litellm.suppress_debug_info = True
    additional_kwargs.pop("api_key")
else:
    from openai import OpenAI

    client = OpenAI(**additional_kwargs)  # type: ignore
    completion = client.chat.completions.create
    additional_kwargs = {}


def get_provider() -> str:
    """Safely get the provider with fallback."""
    try:
        return cfg.get("OPENAI_PROVIDER")
    except:
        return "openai"


def get_azure_client():
    """Get Azure OpenAI client with proper configuration."""
    try:
        provider = get_provider()
        if provider == "azure-openai":
            # Get Azure-specific configuration
            azure_endpoint = ""
            api_version = "2024-02-15-preview"
            
            try:
                azure_endpoint = cfg.get("AZURE_RESOURCE_ENDPOINT")
                api_version = cfg.get("API_VERSION")
            except:
                pass
            
            # Validate Azure configuration
            if not azure_endpoint:
                raise Exception("Azure OpenAI requires AZURE_RESOURCE_ENDPOINT configuration")
            
            # Create Azure OpenAI client with proper parameters
            from openai import AzureOpenAI
            
            azure_kwargs = {
                "api_version": api_version,
                "azure_endpoint": azure_endpoint,
                "api_key": cfg.get("OPENAI_API_KEY"),
                "timeout": int(cfg.get("REQUEST_TIMEOUT")),
            }
            
            return AzureOpenAI(**azure_kwargs)
    except Exception as e:
        print(f"Warning: Failed to create Azure OpenAI client: {e}")
        return None


class Handler:
    cache = Cache(int(cfg.get("CACHE_LENGTH")), Path(cfg.get("CACHE_PATH")))

    def __init__(self, role: SystemRole, markdown: bool) -> None:
        self.role = role

        api_base_url = cfg.get("API_BASE_URL")
        self.base_url = None if api_base_url == "default" else api_base_url
        self.timeout = int(cfg.get("REQUEST_TIMEOUT"))

        self.markdown = "APPLY MARKDOWN" in self.role.role and markdown
        self.code_theme, self.color = cfg.get("CODE_THEME"), cfg.get("DEFAULT_COLOR")
        
        # Get provider and client
        self.provider = get_provider()
        self.azure_client = get_azure_client() if self.provider == "azure-openai" else None

    @property
    def printer(self) -> Printer:
        return (
            MarkdownPrinter(self.code_theme)
            if self.markdown
            else TextPrinter(self.color)
        )

    def make_messages(self, prompt: str) -> List[Dict[str, str]]:
        raise NotImplementedError

    def _get_model_name(self, model: str) -> str:
        """Get the appropriate model name based on provider."""
        if self.provider == "azure-openai":
            # For Azure OpenAI, we need to use the deployment name from config
            # The deployment name is passed as the model parameter
            try:
                deployment_name = cfg.get("AZURE_DEPLOYMENT_NAME")
                if deployment_name:
                    return deployment_name
                else:
                    # Fallback to model name if deployment name not configured
                    return model
            except:
                # If deployment name not found in config, use model name
                return model
        else:
            # Standard OpenAI model names
            return model

    def handle_function_call(
        self,
        messages: List[dict[str, Any]],
        name: str,
        arguments: str,
    ) -> Generator[str, None, None]:
        messages.append(
            {
                "role": "assistant",
                "content": "",
                "function_call": {"name": name, "arguments": arguments},
            }
        )

        if messages and messages[-1]["role"] == "assistant":
            yield "\n"

        dict_args = json.loads(arguments)
        joined_args = ", ".join(f'{k}="{v}"' for k, v in dict_args.items())
        yield f"> @FunctionCall `{name}({joined_args})` \n\n"

        result = get_function(name)(**dict_args)
        if cfg.get("SHOW_FUNCTIONS_OUTPUT") == "true":
            yield f"```text\n{result}\n```\n"
        messages.append({"role": "function", "content": result, "name": name})

    @cache
    def get_completion(
        self,
        model: str,
        temperature: float,
        top_p: float,
        messages: List[Dict[str, Any]],
        functions: Optional[List[Dict[str, str]]],
    ) -> Generator[str, None, None]:
        name = arguments = ""
        local_kwargs = {}  # Initialize local kwargs
        
        is_shell_role = self.role.name == DefaultRoles.SHELL.value
        is_code_role = self.role.name == DefaultRoles.CODE.value
        is_dsc_shell_role = self.role.name == DefaultRoles.DESCRIBE_SHELL.value
        if is_shell_role or is_code_role or is_dsc_shell_role:
            functions = None

        if functions:
            local_kwargs["tool_choice"] = "auto"
            local_kwargs["tools"] = functions
            local_kwargs["parallel_tool_calls"] = False

        # Prepare API call parameters
        disable_stream = cfg.get("DISABLE_STREAMING") == "true"
        api_call_kwargs = {
            "temperature": temperature,
            "top_p": top_p,
            "messages": messages,
            "stream": not disable_stream,  # Respect DISABLE_STREAMING configuration
            "model": self._get_model_name(model),  # Always pass model parameter
            **local_kwargs,
        }
        
        # Use appropriate client based on provider
        if self.provider == "azure-openai" and self.azure_client:
            response = self.azure_client.chat.completions.create(**api_call_kwargs)
        else:
            response = completion(**api_call_kwargs)

        try:
            for chunk in response:
                # Safety check for chunk structure
                if not hasattr(chunk, 'choices') or not chunk.choices:
                    continue
                
                # Safety check for choices array
                if len(chunk.choices) == 0:
                    continue
                
                choice = chunk.choices[0]
                
                # Handle both streaming and non-streaming responses
                if hasattr(choice, 'delta') and choice.delta is not None:
                    # Streaming response structure
                    delta = choice.delta
                    finish_reason = choice.finish_reason
                    
                    # Safety check for delta
                    if delta is None:
                        continue
                        
                    # Handle tool calls (function calls) for streaming
                    tool_calls = None
                    if self.provider == "azure-openai":
                        # Azure OpenAI tool calls - handle as object properties
                        if hasattr(delta, 'tool_calls') and delta.tool_calls:
                            tool_calls = delta.tool_calls
                    else:
                        # Standard OpenAI format
                        tool_calls = (
                            delta.get("tool_calls") if use_litellm else delta.tool_calls
                        )
                    
                    if tool_calls:
                        for tool_call in tool_calls:
                            if hasattr(tool_call, 'function'):
                                func = tool_call.function
                            else:
                                func = tool_call.get('function', {})
                            
                            if hasattr(func, 'name') and func.name:
                                name = func.name
                            elif isinstance(func, dict) and func.get('name'):
                                name = func['name']
                            
                            if hasattr(func, 'arguments') and func.arguments:
                                arguments += func.arguments
                            elif isinstance(func, dict) and func.get('arguments'):
                                arguments += func['arguments']
                    
                    if finish_reason == "tool_calls":
                        yield from self.handle_function_call(messages, name, arguments)
                        yield from self.get_completion(
                            model=model,
                            temperature=temperature,
                            top_p=top_p,
                            messages=messages,
                            functions=functions,
                            caching=False,
                        )
                        return

                    # Extract content from delta
                    content = delta.content or ""
                    yield content
                    
                elif hasattr(choice, 'message') and choice.message is not None:
                    # Non-streaming response structure (like the one you showed)
                    message = choice.message
                    finish_reason = choice.finish_reason
                    
                    # Handle tool calls for non-streaming
                    tool_calls = None
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        tool_calls = message.tool_calls
                    
                    if tool_calls:
                        for tool_call in tool_calls:
                            if hasattr(tool_call, 'function'):
                                func = tool_call.function
                            else:
                                func = tool_call.get('function', {})
                            
                            if hasattr(func, 'name') and func.name:
                                name = func.name
                            elif isinstance(func, dict) and func.get('name'):
                                name = func['name']
                            
                            if hasattr(func, 'arguments') and func.arguments:
                                arguments += func.arguments
                            elif isinstance(func, dict) and func.get('arguments'):
                                arguments += func['arguments']
                    
                    if finish_reason == "tool_calls":
                        yield from self.handle_function_call(messages, name, arguments)
                        yield from self.get_completion(
                            model=model,
                            temperature=temperature,
                            top_p=top_p,
                            messages=messages,
                            functions=functions,
                            caching=False,
                        )
                        return

                    # Extract content from message
                    content = message.content or ""
                    yield content
                    
                else:
                    # Unknown response structure, skip
                    continue
                    
        except KeyboardInterrupt:
            response.close()
        except Exception as e:
            # Handle Azure OpenAI specific errors
            if self.provider == "azure-openai":
                error_msg = str(e)
                if "deployment" in error_msg.lower():
                    raise Exception(f"Azure OpenAI deployment error: {error_msg}. Please check your deployment name and API configuration.")
                elif "api_version" in error_msg.lower():
                    raise Exception(f"Azure OpenAI API version error: {error_msg}. Please check your API version configuration.")
                elif "list index out of range" in error_msg.lower():
                    raise Exception(f"Azure OpenAI response parsing error: {error_msg}. This might be due to unexpected response format or empty choices.")
                else:
                    raise Exception(f"Azure OpenAI error: {error_msg}")
            else:
                raise e

    def handle(
        self,
        prompt: str,
        model: str,
        temperature: float,
        top_p: float,
        caching: bool,
        functions: Optional[List[Dict[str, str]]] = None,
        **kwargs: Any,
    ) -> str:
        disable_stream = cfg.get("DISABLE_STREAMING") == "true"
        messages = self.make_messages(prompt.strip())
        generator = self.get_completion(
            model=model,
            temperature=temperature,
            top_p=top_p,
            messages=messages,
            functions=functions,
            caching=caching,
            **kwargs,
        )
        return self.printer(generator, not disable_stream)
