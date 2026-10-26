try:
    from .claude_agent import Claude
except ModuleNotFoundError as exc:
    # Anthropic support is optional. Local FastChat experiments should not
    # require the external Anthropic SDK.
    if exc.name != "anthropic":
        raise
    Claude = None

from .fastchat_client import FastChatAgent
from .http_agent import HTTPAgent
