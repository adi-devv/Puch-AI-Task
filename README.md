# Puch-AI-Task

This project is a FastMCP-based server that exposes several tools for integration with the Puch AI platform. It provides endpoints for serving your resume, validating your phone number, and fetching web content in a simplified format.

## Features
- **Resume Tool**: Serves your resume in plain markdown extracted from a local PDF file.
- **Validate Tool**: Returns your phone number for validation.
- **Fetch Tool**: Fetches a URL and returns its content, simplified to markdown if possible.
- **Bearer Token Authentication**: Simple bearer token-based authentication for all endpoints.

## Requirements
- Python 3.10+
- [fastmcp](https://github.com/ramkumar-kr/fastmcp)
- [mcp](https://github.com/ramkumar-kr/mcp)
- [openai](https://pypi.org/project/openai/)
- [pydantic](https://pydantic-docs.helpmanual.io/)
- [readabilipy](https://github.com/alan-turing-institute/readabilipy)
- [pdfminer.six](https://github.com/pdfminer/pdfminer.six)
- [markdownify](https://github.com/matthewwithanm/python-markdownify)
- [httpx](https://www.python-httpx.org/)

Install dependencies with:
```bash
pip install -r requirements.txt
```

## Configuration
- Set your bearer `TOKEN` and `MY_NUMBER` in `main.py` (use placeholder values and replace them with your own).
- Place your resume PDF at the path specified in `main.py` (default: `<PATH_TO_YOUR_RESUME>.pdf`).

## Running the Server
```bash
python main.py
```
The server will start on `0.0.0.0:8085`.

## Endpoints/Tools
- `/resume`: Returns your resume as markdown/plain text.
- `/validate`: Returns your phone number for validation.
- `/fetch`: Fetches and returns the content of a given URL.

## License
See [LICENSE](LICENSE) for details. 