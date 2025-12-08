import os
import json
from typing import Dict, List, Any, Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

client = genai.Client(api_key=GEMINI_API_KEY)


def process_query(
    query: str,
    columns: List[Dict[str, Any]],
    dataset_url: str,
    conversation_history: List[Dict[str, str]]
) -> Dict[str, Any]:
    column_info = "\n".join(
        [
            f"- {col['name']}: {col['datatype']} (example: {col.get('example_value', 'N/A')})"
            for col in columns
        ]
    )

    context_messages = []
    for msg in conversation_history:
        role = "User" if msg["sender"] == "user" else "Assistant"
        context_messages.append(f"{role}: {msg['message_txt']}")

    conversation_context = "\n".join(context_messages) if context_messages else "No previous conversation."

    decision_prompt = f"""You are a data analysis assistant. Given a dataset schema, conversation history, and a new user query, decide if you need to run Python code to answer, or if you can answer directly from the conversation context.

Dataset Schema:
{column_info}

Previous Conversation:
{conversation_context}

New User Query: {query}

DECISION RULES:
- If the answer is already in the conversation history (e.g., same question was asked before), respond with "NO_CODE" and provide the answer directly.
- If the user is asking a follow-up question that can be answered from previous results, respond with "NO_CODE".
- If the user is asking for clarification or explanation about previous results, respond with "NO_CODE".
- If the user needs NEW data from the dataset (calculations, specific values, filtering, aggregations, etc.), respond with "NEEDS_CODE".
- If the user is asking about what columns exist or the schema, respond with "NO_CODE" and use the schema above.

Respond in this EXACT JSON format:
{{"decision": "NO_CODE" or "NEEDS_CODE", "reason": "brief explanation", "direct_response": "your response if NO_CODE, otherwise null"}}

Output ONLY the JSON, nothing else."""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=decision_prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=1024,
            ),
        )

        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:].strip()
        if response_text.startswith("```"):
            response_text = response_text[3:].strip()
        if response_text.endswith("```"):
            response_text = response_text[:-3].strip()

        decision = json.loads(response_text)

        if decision.get("decision") == "NO_CODE":
            return {
                "needs_code": False,
                "response": decision.get("direct_response", "I can help with that based on our conversation.")
            }
        else:
            code = generate_analysis_code(query, columns, dataset_url, conversation_context)
            return {
                "needs_code": True,
                "code": code
            }

    except json.JSONDecodeError:
        code = generate_analysis_code(query, columns, dataset_url, conversation_context)
        return {
            "needs_code": True,
            "code": code
        }
    except Exception as e:
        raise Exception(f"Failed to process query: {str(e)}")


def generate_analysis_code(
    query: str,
    columns: List[Dict[str, Any]],
    dataset_url: str,
    conversation_context: Optional[str] = None
) -> str:
    column_info = "\n".join(
        [
            f"- {col['name']}: {col['datatype']} (example: {col.get('example_value', 'N/A')})"
            for col in columns
        ]
    )

    context_section = ""
    if conversation_context and conversation_context != "No previous conversation.":
        context_section = f"""
Previous Conversation (for context on what the user might be referring to):
{conversation_context}

"""

    prompt = f"""You are a Python data analysis code generator. Generate Python code to analyze a dataset.

Dataset URL: {dataset_url}
Available Columns:
{column_info}
{context_section}
User Query: {query}

Generate Python code that:
1. Imports pandas as pd and any other needed libraries
2. Loads data with: df = pd.read_csv("{dataset_url}")
3. Performs the requested analysis
4. Prints results in MARKDOWN FORMAT

OUTPUT FORMAT RULES:
- When showing tabular data (multiple rows/columns), ALWAYS use markdown tables:
  | Column1 | Column2 | Column3 |
  |---------|---------|---------|
  | value1  | value2  | value3  |
- For single values or simple results, use plain text
- Use headers (## or ###) to organize sections if needed
- The AI decides: if data is better shown as a table, output a table

HELPER FUNCTION (include this for table output):
def df_to_markdown(df, max_rows=None):
    if max_rows and len(df) > max_rows:
        df = df.head(max_rows)
        note = f"\\n*Showing first {{max_rows}} rows*"
    else:
        note = ""
    return df.to_markdown(index=False) + note

NOTE: If the user asks for "all", "every", or "each" item, show ALL rows (pass max_rows=None).
Only limit rows if the dataset is very large (100+ rows) and user didn't explicitly ask for all.

CRITICAL: Use the EXACT URL provided above. Do NOT create variables for the URL.
CRITICAL: The code must be complete and runnable as-is.
CRITICAL: Print output in markdown format for better display.

Example structure:
import pandas as pd

def df_to_markdown(df, max_rows=None):
    if max_rows and len(df) > max_rows:
        df = df.head(max_rows)
        note = f"\\n*Showing first {{max_rows}} rows*"
    else:
        note = ""
    return df.to_markdown(index=False) + note

try:
    df = pd.read_csv("{dataset_url}")
    # Your analysis here
    result_df = df[['col1', 'col2']]  # example
    print(df_to_markdown(result_df))  # shows all rows
    # Or: print(df_to_markdown(result_df, max_rows=50)) to limit
except Exception as e:
    print(f"Error: {{e}}")

Output ONLY executable Python code. No markdown code blocks, no explanations."""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=2048,
            ),
        )

        code = response.text.strip()

        if code.startswith("```python"):
            code = code[len("```python") :].strip()
        if code.startswith("```"):
            code = code[3:].strip()
        if code.endswith("```"):
            code = code[:-3].strip()

        return code

    except Exception as e:
        raise Exception(f"Failed to generate code with Gemini: {str(e)}")


def stream_analysis_code(
    query: str,
    columns: List[Dict[str, Any]],
    dataset_url: str,
    conversation_context: Optional[str] = None
):
    column_info = "\n".join(
        [
            f"- {col['name']}: {col['datatype']} (example: {col.get('example_value', 'N/A')})"
            for col in columns
        ]
    )

    context_section = ""
    if conversation_context and conversation_context != "No previous conversation.":
        context_section = f"""
Previous Conversation (for context on what the user might be referring to):
{conversation_context}

"""

    prompt = f"""You are a Python data analysis code generator. Generate Python code to analyze a dataset.

Dataset URL: {dataset_url}
Available Columns:
{column_info}
{context_section}
User Query: {query}

Generate Python code that:
1. Imports pandas as pd and any other needed libraries
2. Loads data with: df = pd.read_csv("{dataset_url}")
3. Performs the requested analysis
4. Prints results in MARKDOWN FORMAT

OUTPUT FORMAT RULES:
- When showing tabular data (multiple rows/columns), ALWAYS use markdown tables:
  | Column1 | Column2 | Column3 |
  |---------|---------|---------|
  | value1  | value2  | value3  |
- For single values or simple results, use plain text
- Use headers (## or ###) to organize sections if needed
- The AI decides: if data is better shown as a table, output a table

HELPER FUNCTION (include this for table output):
def df_to_markdown(df, max_rows=None):
    if max_rows and len(df) > max_rows:
        df = df.head(max_rows)
        note = f"\\n*Showing first {{max_rows}} rows*"
    else:
        note = ""
    return df.to_markdown(index=False) + note

NOTE: If the user asks for "all", "every", or "each" item, show ALL rows (pass max_rows=None).
Only limit rows if the dataset is very large (100+ rows) and user didn't explicitly ask for all.

CRITICAL: Use the EXACT URL provided above. Do NOT create variables for the URL.
CRITICAL: The code must be complete and runnable as-is.
CRITICAL: Print output in markdown format for better display.

Example structure:
import pandas as pd

def df_to_markdown(df, max_rows=None):
    if max_rows and len(df) > max_rows:
        df = df.head(max_rows)
        note = f"\\n*Showing first {{max_rows}} rows*"
    else:
        note = ""
    return df.to_markdown(index=False) + note

try:
    df = pd.read_csv("{dataset_url}")
    # Your analysis here
    result_df = df[['col1', 'col2']]  # example
    print(df_to_markdown(result_df))  # shows all rows
    # Or: print(df_to_markdown(result_df, max_rows=50)) to limit
except Exception as e:
    print(f"Error: {{e}}")

Output ONLY executable Python code. No markdown code blocks, no explanations."""

    try:
        for chunk in client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=2048,
            ),
        ):
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"# Error: {str(e)}"


def clean_generated_code(code: str) -> str:
    code = code.strip()
    if code.startswith("```python"):
        code = code[len("```python"):].strip()
    if code.startswith("```"):
        code = code[3:].strip()
    if code.endswith("```"):
        code = code[:-3].strip()
    return code


def generate_chat_response(query: str, context: str = None) -> str:
    prompt = query
    if context:
        prompt = f"Context: {context}\n\nUser: {query}\n\nAssistant:"

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=1024,
            ),
        )
        return response.text.strip()
    except Exception as e:
        raise Exception(f"Failed to generate response with Gemini: {str(e)}")


def stream_direct_response(
    query: str,
    columns: List[Dict[str, Any]],
    conversation_history: List[Dict[str, str]]
):
    column_info = "\n".join(
        [
            f"- {col['name']}: {col['datatype']} (example: {col.get('example_value', 'N/A')})"
            for col in columns
        ]
    )

    context_messages = []
    for msg in conversation_history:
        role = "User" if msg["sender"] == "user" else "Assistant"
        context_messages.append(f"{role}: {msg['message_txt']}")

    conversation_context = "\n".join(context_messages) if context_messages else "No previous conversation."

    prompt = f"""You are a helpful data analysis assistant. Answer the user's question based on the dataset schema and conversation history.

Dataset Schema:
{column_info}

Previous Conversation:
{conversation_context}

User Query: {query}

Provide a helpful, concise response. If referring to data from the conversation, be specific."""

    try:
        for chunk in client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=1024,
            ),
        ):
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"Error: {str(e)}"
