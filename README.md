# General Tools

Collection of general-purpose command-line tools and utilities.

## Tools

### FileDetective

Intelligent file discovery and analysis CLI tool.

- **Token counting** using tiktoken (OpenAI cl100k_base)
- **Path-based wildcards** for flexible file matching
- **Multi-file comparison** with aggregate statistics
- **Structure extraction** for code (Python, JavaScript/TypeScript) and documentation
- **Case-insensitive search** across multiple project directories

See [filedetective/README.md](filedetective/README.md) for full documentation.

**Quick start:**
```bash
# Install dependencies
cd filedetective
pip install -r requirements.txt

# Set up alias
echo 'alias filedet="python3 ~/projects/general_tools/filedetective/filedet.py"' >> ~/.bashrc
source ~/.bashrc

# Use it
filedet myfile.py
filedet find "*.md"
filedet "cc-*/drafts/*.md"
```

## License

Internal tools for personal use.
