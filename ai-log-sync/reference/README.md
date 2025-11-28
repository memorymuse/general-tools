# Reference Implementations

These files were copied from `~/cc-projects/claude-chatgpt-convo-evals/scripts/` and contain more thorough parsing logic than the initial implementation.

## Files

### conversation_parser.py
- `ClaudeParser` and `OpenAIParser` classes
- Handles: thinking blocks, tool use, voice notes, tree traversal
- Proper content type detection and metadata extraction
- Search functionality

### normalize_conversations.py
- Detailed author type detection (user, assistant, tool, system)
- Subtype detection (thinking, tool_use, voice, code, web_search, multimodal)
- Word count tracking
- Monthly organization

## Key Improvements Over Current Collectors

### Claude.ai Export Parsing
Current `collectors/claude_web_export.py` is basic. The reference `ClaudeParser` handles:
- Thinking blocks (`content.type == 'thinking'`)
- Tool use/results (`content.type == 'tool_use'`, `'tool_result'`)
- Voice notes
- Attachments
- Proper metadata extraction

### ChatGPT Export Parsing
Current `collectors/chatgpt_export.py` does basic tree traversal. The reference `OpenAIParser` handles:
- Proper tree structure traversal with `traverse_conversation_tree()`
- Hidden message filtering (`is_visually_hidden_from_conversation`)
- Code execution output
- Web search results (tether_quote, tether_browsing_display)
- Multimodal content (images)
- Thoughts/reasoning content

## Usage Recommendation

When enhancing the collectors, adapt the parsing logic from these reference files rather than starting from scratch. The reference implementations have been tested against real exports and handle edge cases.

## Original Source
`~/cc-projects/claude-chatgpt-convo-evals/`
- Full project with extraction, normalization, and search scripts
- Contains analysis of both Claude and OpenAI export schemas
- See `FINDINGS.md` and `HANDOFF.md` in that repo for detailed schema documentation
