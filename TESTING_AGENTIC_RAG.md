# Testing Agentic RAG System

## Quick Start Testing Guide

### Prerequisites

```powershell
# Activate environment
.\capestone_prj\Scripts\Activate.ps1

# Start the server
python src/main.py
```

Server should start on `http://localhost:8000`

## Test 1: Simple Single-Tool Query

**Expected behavior**: Agent should call `search_policy_documents` once and return answer.

```powershell
# Using Invoke-WebRequest (PowerShell)
$body = @{
    query = "What is the vacation policy?"
    user_id = "test_user"
} | ConvertTo-Json

$response = Invoke-WebRequest `
    -Uri "http://localhost:8000/api/v1/query" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

$result = $response.Content | ConvertFrom-Json
Write-Output "Answer: $($result.answer)"
Write-Output "Iterations: $($result.iterations)"
Write-Output "Tool Calls: $($result.tool_calls.Count)"
Write-Output "Agent Plan: $($result.agent_plan)"

# Save query_id for status check
$queryId = $result.metadata.query_id
```

**Expected Output**:
```
Answer: [Detailed vacation policy answer from HR manual]
Iterations: 1 or 2
Tool Calls: 1
Agent Plan: Completed in 1 iteration(s) with 1 tool call(s)
```

## Test 2: Complex Multi-Tool Query

**Expected behavior**: Agent should call multiple tools to gather comprehensive information.

```powershell
$body = @{
    query = "Compare vacation and sick leave policies. How do they differ and what are the eligibility requirements for each?"
    user_id = "test_user"
} | ConvertTo-Json

$response = Invoke-WebRequest `
    -Uri "http://localhost:8000/api/v1/query" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

$result = $response.Content | ConvertFrom-Json
Write-Output "Answer length: $($result.answer.Length) chars"
Write-Output "Iterations: $($result.iterations)"
Write-Output "Tool Calls: $($result.tool_calls.Count)"
Write-Output "`nTools Used:"
$result.tool_calls | ForEach-Object {
    Write-Output "  - Iteration $($_.iteration): $($_.tool_name)"
}
Write-Output "`nAgent Plan: $($result.agent_plan)"

$queryId = $result.metadata.query_id
```

**Expected Output**:
```
Answer length: 800+ chars
Iterations: 3-5
Tool Calls: 2-4
Tools Used:
  - Iteration 1: search_policy_documents
  - Iteration 2: search_policy_documents
  - Iteration 3: search_related_topics
Agent Plan: Completed in 3 iteration(s) with 3 tool call(s)
```

## Test 3: Check Query Status

**Use the query_id from previous tests**:

```powershell
$statusResponse = Invoke-WebRequest `
    -Uri "http://localhost:8000/api/v1/status/$queryId" `
    -Method GET

$status = $statusResponse.Content | ConvertFrom-Json

Write-Output "Query Status: $($status.status)"
Write-Output "Duration: $($status.duration_seconds) seconds"
Write-Output "`nProcessing Steps:"
$status.steps | ForEach-Object {
    Write-Output "  [$($_.status)] $($_.step): $($_.details)"
}

Write-Output "`nAgent Details:"
Write-Output "  Plan: $($status.agent_plan)"
Write-Output "  Iterations: $($status.iterations)"
Write-Output "  Tool Calls: $($status.tool_calls.Count)"

Write-Output "`nRetrieved Documents:"
$status.retrieved_documents | ForEach-Object {
    Write-Output "  - $($_.filename) (score: $($_.score))"
}
```

**Expected Output**:
```
Query Status: completed
Duration: 3.5 seconds

Processing Steps:
  [completed] session_initialization: Session ID: xyz
  [completed] agent_planning: Agent completed in 3 iteration(s) with 3 tool call(s)
  [completed] source_extraction: Extracted 5 source documents
  [completed] finalization: Query processing complete

Agent Details:
  Plan: Completed in 3 iteration(s) with 3 tool call(s)
  Iterations: 3
  Tool Calls: 3

Retrieved Documents:
  - HR Policy Manual 2023.pdf (score: 0.92)
  - Employee Handbook.pdf (score: 0.88)
  ...
```

## Test 4: List Available Policies

**Test if agent can discover what's in the knowledge base**:

```powershell
$body = @{
    query = "What policy documents are available in the system?"
    user_id = "test_user"
} | ConvertTo-Json

$response = Invoke-WebRequest `
    -Uri "http://localhost:8000/api/v1/query" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

$result = $response.Content | ConvertFrom-Json
Write-Output $result.answer
```

**Expected**: Agent calls `list_available_policies` tool and returns list of all documents in the KB.

## Test 5: Document Detail Retrieval

**Test specific document retrieval**:

```powershell
$body = @{
    query = "Give me detailed information about the HR Policy Manual 2023"
    user_id = "test_user"
} | ConvertTo-Json

$response = Invoke-WebRequest `
    -Uri "http://localhost:8000/api/v1/query" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

$result = $response.Content | ConvertFrom-Json
Write-Output "Tool used: $($result.tool_calls[0].tool_name)"
Write-Output "Answer preview: $($result.answer.Substring(0, 200))..."
```

**Expected**: Agent calls `get_document_details` with document identifier.

## Test 6: Health Check

**Verify all systems operational**:

```powershell
$healthResponse = Invoke-WebRequest `
    -Uri "http://localhost:8000/api/v1/health" `
    -Method GET

$health = $healthResponse.Content | ConvertFrom-Json

Write-Output "System Status: $($health.status)"
Write-Output "`nComponent Checks:"
Write-Output "  API: $($health.checks.api)"
Write-Output "  Azure OpenAI: $($health.checks.azure_openai)"
Write-Output "  Pinecone: $($health.checks.pinecone)"
Write-Output "  MongoDB: $($health.checks.mongodb)"
Write-Output "  Semantic Kernel: $($health.checks.semantic_kernel)"

if ($health.errors) {
    Write-Output "`nErrors:"
    $health.errors | ForEach-Object {
        Write-Output "  - $_"
    }
}
```

**Expected**: All checks should return "ok" (except MongoDB may be "not_configured" if not using it).

## Test 7: Conversation Context

**Test multi-turn conversation**:

```powershell
# First question
$body1 = @{
    query = "What is the remote work policy?"
    user_id = "test_user"
    session_id = "test_session_123"
} | ConvertTo-Json

$response1 = Invoke-WebRequest `
    -Uri "http://localhost:8000/api/v1/query" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body1

$result1 = $response1.Content | ConvertFrom-Json
Write-Output "Question 1 answered"

# Follow-up question (same session)
$body2 = @{
    query = "What are the equipment requirements for that?"
    user_id = "test_user"
    session_id = "test_session_123"
} | ConvertTo-Json

$response2 = Invoke-WebRequest `
    -Uri "http://localhost:8000/api/v1/query" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body2

$result2 = $response2.Content | ConvertFrom-Json
Write-Output "Question 2 Answer: $($result2.answer)"
```

**Expected**: Agent should understand "that" refers to remote work policy from previous question.

## Monitoring Agent Behavior

### Watch Logs in Real-Time

```powershell
# In a separate PowerShell window
Get-Content logs/app_*.log -Wait -Tail 50 | Select-String "\[Agent\]"
```

**Look for**:
- `[Agent] Starting execution for query:`
- `[Agent] Iteration X/5`
- `[Agent] Tool called: [tool_name]`
- `[Agent] Final answer received`

### Check Tool Call Details

```powershell
# After a query, inspect tool calls
$queryId = "your-query-id"
$status = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/status/$queryId" | 
          Select-Object -ExpandProperty Content | 
          ConvertFrom-Json

$status.tool_calls | ForEach-Object {
    Write-Output "`nTool: $($_.tool_name)"
    Write-Output "Iteration: $($_.iteration)"
    Write-Output "Arguments:"
    $_.arguments | ConvertTo-Json -Depth 10
}
```

## Troubleshooting Tests

### Issue: Agent Not Calling Tools

**Symptoms**: `tool_calls` is empty or has 0 length

**Debug**:
```powershell
# Check if tools are registered
$healthResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health"
# Look for semantic_kernel: "ok"

# Check logs for initialization
Get-Content logs/app_*.log | Select-String "plugin"
```

**Solution**: Restart server, verify SK initialization in logs.

### Issue: Max Iterations Reached

**Symptoms**: `agent_plan` says "Reached max iterations (5)"

**Debug**:
```powershell
# Check what the agent was doing
$status.tool_calls | Group-Object tool_name | Select-Object Name, Count
```

**Solution**: Increase max_iterations or simplify query.

### Issue: Empty or Generic Answers

**Symptoms**: Answer doesn't reference specific policies

**Debug**:
```powershell
# Check retrieved documents
$status.retrieved_documents | Select-Object filename, score
```

**Solution**: Check Pinecone has documents (use health endpoint), verify embeddings working.

## Performance Benchmarks

Run this to measure average performance:

```powershell
$queries = @(
    "What is the vacation policy?",
    "Compare sick leave and vacation policies",
    "What are the remote work requirements?"
)

$results = @()

foreach ($q in $queries) {
    $start = Get-Date
    
    $body = @{
        query = $q
        user_id = "benchmark_user"
    } | ConvertTo-Json
    
    $response = Invoke-WebRequest `
        -Uri "http://localhost:8000/api/v1/query" `
        -Method POST `
        -ContentType "application/json" `
        -Body $body
    
    $end = Get-Date
    $duration = ($end - $start).TotalSeconds
    
    $result = $response.Content | ConvertFrom-Json
    
    $results += [PSCustomObject]@{
        Query = $q
        Duration = $duration
        Iterations = $result.iterations
        ToolCalls = $result.tool_calls.Count
        AnswerLength = $result.answer.Length
    }
}

$results | Format-Table -AutoSize
```

**Expected Performance**:
- Simple queries: 2-4 seconds, 1-2 iterations, 1 tool call
- Complex queries: 4-8 seconds, 2-5 iterations, 2-4 tool calls

## Success Criteria

✅ **Agent Planning Works**:
- `agent_plan` field populated in response
- Iterations > 0
- Tool calls tracked

✅ **Tools Are Called**:
- `tool_calls` array has entries
- Different tools used for different query types

✅ **Quality Answers**:
- Answers reference specific policies
- Sources included
- Context appropriate

✅ **Status Tracking**:
- All steps completed
- Duration calculated
- Retrieved documents listed

✅ **Error Handling**:
- Graceful failures
- Error status in `/status/{query_id}`
- Meaningful error messages

## Next Steps After Testing

1. **Tune Performance**: Adjust max_iterations, temperature based on results
2. **Enhance Tools**: Add more specialized agent tools based on usage patterns
3. **Optimize Prompts**: Refine system prompt to improve agent planning
4. **Add Monitoring**: Set up dashboard for agent metrics
5. **Document Patterns**: Record which tool sequences work best for different query types

---

**Pro Tip**: Keep a log of test queries and their tool call patterns. This helps identify opportunities for optimization and new tool creation.
