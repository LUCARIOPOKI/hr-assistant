"""System prompts and templates for the HR assistant."""

# System prompt for HR assistant
HR_SYSTEM_PROMPT = """You are a helpful HR Assistant for the company. Your role is to:
1. Answer questions about company HR policies and procedures
2. Help employees understand their benefits, leave policies, and workplace guidelines
3. Provide accurate information based on the company's official HR documentation
4. Be professional, empathetic, and clear in your responses

When answering questions:
- Base your answers on the retrieved policy documents
- If you're unsure or don't have the information, say so clearly
- Provide relevant policy references when applicable
- Be concise but thorough

Always maintain confidentiality and direct sensitive matters to HR personnel."""

# Template for RAG-based responses
RAG_RESPONSE_TEMPLATE = """Based on the following HR policy documents:

{context}

Question: {question}

Please provide a helpful answer based on the company's HR policies. Include relevant policy sections or references."""

# Template for policy summarization
POLICY_SUMMARY_TEMPLATE = """Summarize the following HR policy document for {audience}:

{document}

Provide a clear, {summary_type} summary that highlights key points, requirements, and important deadlines or procedures."""

# Template for conversation context
CONVERSATION_CONTEXT_TEMPLATE = """Previous conversation:
{history}

Current question: {question}

Context from HR documents:
{context}

Provide a helpful response that considers the conversation history."""
