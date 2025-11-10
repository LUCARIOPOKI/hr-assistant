# Agentic RAG Implementation Summary

## Overview

Successfully transformed the HR Assistant from a simple RAG system into an **Agentic RAG** system where the LLM autonomously plans, uses tools, reasons, and generates comprehensive answers.

## What Changed

### 1. Agent Tools in Retrieval Plugin
**File**: `src/plugins/retrieval_plugin/retrieval_plugin.py`

Added 4 new agent tools (Semantic Kernel functions):

1. **`search_policy_documents`** - Search for specific policies by topic/keyword
   - Parameters: query (str), top_k (int)
   - Returns: Formatted policy texts with relevance scores and sources

2. **`get_document_details`** - Get complete information from a specific document
   - Parameters: document_identifier (str)
   - Returns: Full document content with all chunks combined

3. **`search_related_topics`** - Find connections between different policy areas
   - Parameters: topic1 (str), topic2 (str)
   - Returns: Policies that relate to both topics, highlighting connections

4. **`list_available_policies`** - List all available policy categories and documents
   - Parameters: None
   - Returns: List of all documents in the knowledge base

**Key Pattern**: Each tool is decorated with `@kernel_function` and has clear descriptions that guide the LLM on when to use them.

### 2. Agent Execution Method
**File**: `src/services/llm_service.py`

Added `agent_execute()` method with:

- **Auto Function Calling**: Uses `FunctionChoiceBehavior.Auto()` to enable autonomous tool calling
- **Iterative Reasoning**: Loops up to `max_iterations` (default: 5) allowing the agent to call multiple tools
- **Comprehensive Tracking**: Records all tool calls with arguments, iteration numbers
- **Graceful Handling**: Returns best available answer even if max iterations reached

**Return Structure**:
```python
{
    "answer": str,           # Final response
    "tool_calls": [          # All tools called
        {
            "tool_name": str,
            "arguments": dict,
            "iteration": int
        }
    ],
    "iterations": int,       # Total iterations taken
    "agent_plan": str        # Summary of execution
}
```

### 3. Query Endpoint (Agentic Mode)
**File**: `src/api/routes.py`

**Previous Flow**:
```
User Query → Retrieve Documents → Build Prompt → Generate Response → Return
```

**New Agentic Flow**:
```
User Query → Agent Plans → Agent Calls Tools → Agent Reasons → Comprehensive Answer
```

**Key Changes**:

1. **Agent System Prompt**: Built dynamically with:
   - HR context from `HR_SYSTEM_PROMPT`
   - Available tools description
   - Conversation history
   - Clear instructions to plan and use tools

2. **Steps Tracking**:
   - `session_initialization` - Create/get session
   - `agent_planning` - Agent executes with tool calling (NEW)
   - `source_extraction` - Extract document sources
   - `finalization` - Save and return response

3. **Status Store**: Now tracks:
   - `agent_plan` - Agent's reasoning summary
   - `tool_calls` - Array of all tool invocations
   - `iterations` - Number of reasoning iterations
   - `retrieved_documents` - All documents accessed

### 4. Response Schemas
**File**: `src/api/schemas.py`

Updated `QueryResponse` with agent fields:

```python
class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []
    conversation_id: int
    session_id: str
    metadata: Optional[Dict[str, Any]] = None
    # NEW: Agentic RAG fields
    agent_plan: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = []
    iterations: Optional[int] = 0
```

### 5. Status Endpoint Enhancement
**File**: `src/api/routes.py`

Status endpoint (`/status/{query_id}`) now returns:

- **Agent Plan**: Summary of execution (e.g., "Completed in 3 iteration(s) with 2 tool call(s)")
- **Tool Calls**: Detailed list of every tool called with arguments and iteration number
- **Iterations**: Total reasoning cycles
- **Retrieved Documents**: Full list with scores, previews, chunk IDs

## How It Works

### Example Execution Flow

**User asks**: "What are the vacation and sick leave policies, and how do they relate?"

1. **Agent Planning Phase**:
   - LLM receives query + system prompt describing available tools
   - Agent decides to call `search_policy_documents` with "vacation policy"

2. **Tool Call 1** (Iteration 1):
   - Tool searches Pinecone, returns vacation policy chunks
   - Result added to conversation history

3. **Tool Call 2** (Iteration 2):
   - Agent calls `search_policy_documents` with "sick leave policy"
   - Returns sick leave policy chunks

4. **Tool Call 3** (Iteration 3):
   - Agent calls `search_related_topics` with topic1="vacation" topic2="sick leave"
   - Returns policies showing connections

5. **Final Answer** (Iteration 4):
   - Agent synthesizes all retrieved information
   - Generates comprehensive answer covering both policies and their relationship
   - No more tool calls needed → execution completes

### Key Benefits

1. **Autonomous Information Gathering**: Agent decides what tools to use and when
2. **Multi-Step Reasoning**: Can call multiple tools to build comprehensive answers
3. **Transparent Process**: All tool calls and iterations tracked and visible
4. **Better Answers**: Agent can gather related information rather than single-query retrieval
5. **Self-Correction**: Agent can call additional tools if initial results insufficient

## Configuration

### Max Iterations
Default: 5 iterations per query

Change in `src/api/routes.py`:
```python
agent_result = await llm_service.agent_execute(
    query=req.query,
    system_prompt=agent_system_prompt,
    max_iterations=5,  # Adjust here
    temperature=0.7,
    max_tokens=2000
)
```

### Temperature & Tokens
- **Temperature**: 0.7 (balanced creativity/accuracy)
- **Max Tokens**: 2000 (allows longer reasoning)

### Tool Availability
All tools in `RetrievalPlugin` are automatically available to the agent via:
```python
function_choice_behavior=FunctionChoiceBehavior.Auto(
    auto_invoke=True,
    filters={"excluded_plugins": []}  # Allow all plugins
)
```

## Testing the Agentic System

### Simple Query (Should use 1-2 tools)
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the vacation policy?",
    "user_id": "test_user"
  }'
```

**Expected**: Agent calls `search_policy_documents("vacation")` once, returns answer.

### Complex Query (Should use multiple tools)
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare the vacation and sick leave policies. How do they interact?",
    "user_id": "test_user"
  }'
```

**Expected**: Agent calls:
1. `search_policy_documents("vacation")`
2. `search_policy_documents("sick leave")`
3. `search_related_topics("vacation", "sick leave")`
4. Synthesizes comprehensive comparative answer

### Check Agent Activity
```bash
# Get the query_id from the response, then:
curl http://localhost:8000/api/v1/status/{query_id}
```

**Response includes**:
- `agent_plan`: "Completed in 3 iteration(s) with 3 tool call(s)"
- `tool_calls`: Array showing each tool, arguments, iteration
- `iterations`: Total cycles (e.g., 3)
- `retrieved_documents`: All documents accessed during execution

## Code Structure

### Agent Components

```
src/
├── services/
│   └── llm_service.py          # agent_execute() method
├── plugins/
│   └── retrieval_plugin/
│       └── retrieval_plugin.py # 4 agent tools
├── api/
│   ├── routes.py               # Agentic query endpoint
│   └── schemas.py              # QueryResponse with agent fields
└── config/
    └── prompts.py              # System prompts (unchanged)
```

### Key Imports Needed

```python
# For agent execution
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

# Already present
from semantic_kernel.functions import kernel_function
from semantic_kernel.contents import ChatHistory
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
```

## Migration from Simple RAG

The transformation was **non-breaking**:

- ✅ Same API endpoints (`/query`, `/status`, `/health`)
- ✅ Same request schema (`QueryRequest`)
- ✅ Same session management (in-memory conversation history)
- ✅ Backward compatible response (added optional fields)
- ✅ All previous functionality preserved

**Only change**: Query endpoint now uses autonomous agent instead of fixed retrieval→generate flow.

## Monitoring Agent Performance

### Check Logs
```bash
# View agent execution logs
Get-Content logs/app_*.log -Tail 100 | Select-String "\[Agent\]"
```

**Log patterns**:
- `[Agent] Starting execution for query: ...`
- `[Agent] Iteration X/5`
- `[Agent] Tool called: search_policy_documents`
- `[Agent] Final answer received`

### Status Tracking

Each query creates detailed status entry accessible via `/status/{query_id}`:

```json
{
  "query_id": "uuid",
  "status": "completed",
  "agent_plan": "Completed in 2 iteration(s) with 1 tool call(s)",
  "tool_calls": [
    {
      "tool_name": "search_policy_documents",
      "arguments": {"query": "vacation", "top_k": 3},
      "iteration": 1
    }
  ],
  "iterations": 2,
  "steps": [
    {"step": "session_initialization", "status": "completed", ...},
    {"step": "agent_planning", "status": "completed", ...},
    {"step": "source_extraction", "status": "completed", ...},
    {"step": "finalization", "status": "completed", ...}
  ],
  "duration_seconds": 3.2
}
```

## Troubleshooting

### Agent Not Calling Tools

**Symptom**: Agent returns answer without calling any tools (0 tool calls)

**Causes**:
1. Question too simple (agent can answer from system prompt)
2. Tools descriptions unclear
3. Temperature too low (agent too conservative)

**Solutions**:
- Check `agent_plan` in response for reasoning
- Review tool descriptions in `retrieval_plugin.py`
- Increase temperature slightly (0.8)

### Max Iterations Reached

**Symptom**: `agent_plan` says "Reached max iterations (5)"

**Causes**:
1. Complex multi-part question
2. Agent iterating unnecessarily
3. Tools returning insufficient information

**Solutions**:
- Increase `max_iterations` to 7-10 for complex queries
- Check tool responses in logs for quality
- Simplify query or split into multiple questions

### Tool Errors in Logs

**Symptom**: `[Agent] Error in iteration X: ...`

**Causes**:
1. Pinecone connection issues
2. Embedding service failure
3. Tool function exceptions

**Solutions**:
- Check health endpoint: `/health`
- Verify Pinecone index accessible
- Review specific tool error in logs

## Performance Considerations

### Latency

**Simple RAG**: ~2-3 seconds (1 retrieval + 1 generation)

**Agentic RAG**: ~3-8 seconds depending on:
- Number of tool calls (1-5)
- Iterations needed (1-5)
- Each tool call adds ~1-2 seconds

### Token Usage

**Simple RAG**: ~500-1000 tokens/query

**Agentic RAG**: ~1000-3000 tokens/query
- Each tool call adds ~200-500 tokens
- Agent reasoning adds overhead

### Optimization Tips

1. **Reduce Max Iterations**: Lower from 5 to 3 for simple use cases
2. **Cache Tool Results**: Future enhancement - cache frequently called tools
3. **Parallel Tool Calls**: Semantic Kernel supports this in newer versions
4. **Smart Tool Selection**: Use `filters` in `FunctionChoiceBehavior` to limit available tools per query type

## Future Enhancements

### 1. Multi-Agent Collaboration
Add specialized agents:
- **Policy Expert**: Focuses on detailed policy interpretation
- **Comparison Agent**: Specializes in comparing multiple policies
- **Summarization Agent**: Creates executive summaries

### 2. Memory & Learning
- Store successful tool call patterns
- Learn from past query resolutions
- Build query → tool mapping cache

### 3. Advanced Tools
Additional tools for agent:
- `verify_policy_currency`: Check if policy is most recent version
- `get_policy_history`: Retrieve historical policy versions
- `find_exceptions`: Search for policy exceptions and edge cases
- `calculate_benefits`: Compute numeric benefits (PTO days, etc.)

### 4. Agent Reflection
Add self-reflection step:
- Agent reviews answer before returning
- Checks if all parts of question addressed
- Validates sources are relevant

### 5. Parallel Tool Execution
Enable concurrent tool calls:
```python
# Future: Call multiple tools simultaneously
agent_result = await llm_service.agent_execute(
    query=req.query,
    parallel_tools=True,  # NEW
    max_parallel=3
)
```

## Conclusion

The HR Assistant is now a fully **agentic RAG system** with:

✅ **4 Agent Tools** for autonomous information gathering  
✅ **Auto Function Calling** with up to 5 reasoning iterations  
✅ **Comprehensive Tracking** of all tool calls and agent decisions  
✅ **Enhanced Responses** with agent_plan, tool_calls, iterations metadata  
✅ **Backward Compatible** with existing API contracts  

**Result**: The system can now handle complex multi-part questions by autonomously planning, calling multiple tools, and reasoning through comprehensive answers - all while maintaining full transparency of the agent's decision-making process.
