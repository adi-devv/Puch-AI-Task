from typing import Annotated
from fastmcp import FastMCP
from fastmcp.server.auth.providers.bearer import BearerAuthProvider, RSAKeyPair
from mcp import ErrorData, McpError
from mcp.server.auth.provider import AccessToken
from mcp.types import INTERNAL_ERROR, INVALID_PARAMS, TextContent
from openai import BaseModel
from pydantic import AnyUrl, Field
import readabilipy
from pathlib import Path
from pdfminer.high_level import extract_text

# === ✅ YOUR CONFIG ===
TOKEN = "ca56dc8dffc0"
MY_NUMBER = "919910770554"  # <-- Replace with your number, NO '+'


# === ✅ TOOL DESCRIPTIONS ===
class RichToolDescription(BaseModel):
    description: str
    use_when: str
    side_effects: str | None


# === ✅ SIMPLE BEARER AUTH ===
class SimpleBearerAuthProvider(BearerAuthProvider):
    def __init__(self, token: str):
        k = RSAKeyPair.generate()
        super().__init__(
            public_key=k.public_key, jwks_uri=None, issuer=None, audience=None
        )
        self.token = token

    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self.token:
            return AccessToken(
                token=token,
                client_id="unknown",
                scopes=[],
                expires_at=None,
            )
        return None


# === ✅ MCP SERVER ===
mcp = FastMCP(
    "My MCP Server",
    auth=SimpleBearerAuthProvider(TOKEN),
)

# === ✅ RESUME TOOL ===
ResumeToolDescription = RichToolDescription(
    description="Serve your resume in plain markdown.",
    use_when="Puch (or anyone) asks for your resume; this must return raw markdown, no extra formatting.",
    side_effects=None,
)


@mcp.tool(description=ResumeToolDescription.model_dump_json())
async def resume() -> str:
    """
    Read your local PDF resume, extract text, return as markdown/plain text.
    """
    try:
        pdf_path = Path(r"D:\Aadit\My\CV.pdf")
        if not pdf_path.exists():
            return "<error>Resume file not found.</error>"

        text = extract_text(str(pdf_path))

        if not text.strip():
            return "<error>Could not extract text from PDF.</error>"

        return text  # Or wrap in markdown if you want

    except Exception as e:
        return f"<error>Failed to extract resume: {e}</error>"


# === ✅ VALIDATE TOOL ===
@mcp.tool
async def validate() -> str:
    """
    Required for Puch: returns your phone number for validation.
    """
    return MY_NUMBER


# === ✅ FETCH TOOL ===
class Fetch:
    IGNORE_ROBOTS_TXT = True
    USER_AGENT = "Puch/1.0 (Autonomous)"

    @classmethod
    async def fetch_url(cls, url: str, user_agent: str, force_raw: bool = False) -> tuple[str, str]:
        from httpx import AsyncClient, HTTPError

        async with AsyncClient() as client:
            try:
                response = await client.get(
                    url,
                    follow_redirects=True,
                    headers={"User-Agent": user_agent},
                    timeout=30,
                )
            except HTTPError as e:
                raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch {url}: {e!r}"))

            if response.status_code >= 400:
                raise McpError(ErrorData(code=INTERNAL_ERROR,
                                         message=f"Failed to fetch {url} - status code {response.status_code}"))

            page_raw = response.text

        content_type = response.headers.get("content-type", "")
        is_page_html = (
                "<html" in page_raw[:100] or "text/html" in content_type or not content_type
        )

        if is_page_html and not force_raw:
            return cls.extract_content_from_html(page_raw), ""

        return page_raw, f"Content type {content_type} cannot be simplified to markdown. Raw content:\n"

    @staticmethod
    def extract_content_from_html(html: str) -> str:
        ret = readabilipy.simple_json.simple_json_from_html_string(html, use_readability=True)
        if not ret["content"]:
            return "<error>Page failed to simplify from HTML</error>"
        import markdownify
        return markdownify.markdownify(ret["content"], heading_style=markdownify.ATX)


FetchToolDescription = RichToolDescription(
    description="Fetch a URL and return its content.",
    use_when="When the user provides a URL and asks for its content.",
    side_effects="Returns the content in simplified format or raw HTML.",
)


@mcp.tool(description=FetchToolDescription.model_dump_json())
async def fetch(
        url: Annotated[AnyUrl, Field(description="URL to fetch")],
        max_length: Annotated[int, Field(default=5000, gt=0, lt=1000000)] = 5000,
        start_index: Annotated[int, Field(default=0, ge=0)] = 0,
        raw: Annotated[bool, Field(default=False)] = False,
) -> list[TextContent]:
    url_str = str(url).strip()
    if not url:
        raise McpError(ErrorData(code=INVALID_PARAMS, message="URL is required"))

    content, prefix = await Fetch.fetch_url(url_str, Fetch.USER_AGENT, force_raw=raw)
    original_length = len(content)
    if start_index >= original_length:
        content = "<error>No more content available.</error>"
    else:
        truncated_content = content[start_index: start_index + max_length]
        if not truncated_content:
            content = "<error>No more content available.</error>"
        else:
            content = truncated_content
            remaining = original_length - (start_index + len(truncated_content))
            if len(truncated_content) == max_length and remaining > 0:
                next_start = start_index + len(truncated_content)
                content += f"\n\n<error>Content truncated. Call again with start_index={next_start} to get more.</error>"

    return [TextContent(type="text", text=f"{prefix}Contents of {url}:\n{content}")]

# === ✅ MAIN ENTRYPOINT ===
async def main():
    await mcp.run_async(
        "streamable-http",
        host="0.0.0.0",
        port=8085,
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
