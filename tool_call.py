# tool_call.py
from openai import OpenAI
import os
import json

extra_body = {"enable_thinking": True}

client = OpenAI(
    api_key='sk-xxx',
    base_url="https://api.deepseek.com",
)


def get_tool_call(content: str):
    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=[
            {
                "role": "system",
                "content": """You are a planning agent for well-log facies classification.

Return ONLY valid JSON in the following format:
{
  "tools": [
    {"name": "expert_feature_description_tool", "why": "reason ..."},
    {"name": "trend_analysis_tool", "why": "reason ..."}
  ]
}

- The "name" must be one of:
  - "expert_feature_description_tool"
  - "expert_label_description_tool"
  - "classification_suggestions_tool"
  - "trend_analysis_tool"
  - "neighbor_find_tool"
- "why" should briefly explain why this tool is selected.
""",
            },
            {
                "role": "user",
                "content": content,
            },
        ],
        stream=False,
        extra_body=extra_body,
        response_format={"type": "json_object"},
    )

    think = response.choices[0].message.reasoning_content
    answer = response.choices[0].message.content  # JSON string
    return think, answer


def build_tool_select_prompt(table_str: str) -> str:
    prompt = f"""You are an expert planner deciding which tools to run for well-log classification.

Here are the tools you can use:

1. expert_feature_description_tool
   - defines and explains key features in well-log data that are critical for classification.

2. expert_label_description_tool
   - provides detailed descriptions of classification labels based on domain knowledge.

3. expert_classification_suggestions_tool
   - provides rule-based suggestions and heuristic patterns for mapping logs to lithofacies.

4. trend_analysis_tool
   - analyzes trends in well-log data (including up/down/target windows) to identify patterns and vertical continuity.

5. neighbor_finding_tool
   - finds similar well-log cases from a database using a k-nearest-neighbor approach (currently a placeholder).

Selection guidelines:
- Use a single tool when the pattern is simple and one perspective is clearly sufficient.
- Use multiple tools when:
  - Both trend analysis and expert knowledge are needed.
  - Patterns are complex or ambiguous.
  - You want both heuristic rules and data-driven references.

OUTPUT FORMAT:
Return valid JSON exactly as shown:
{{
  "tools": [
    {{"name": "XXX", "why": "Brief reason for selection XXX"}},
    ...
  ]
}}

WELL LOG DATA TO CLASSIFY (partial table, Predicted_Facies hidden here):
{table_str}

Analyze the data characteristics and select 1-5 tools that best complement each other.
Return ONLY the JSON object described above.
"""
    return prompt


def get_tool_selection(table_str: str):
    planner_prompt = build_tool_select_prompt(table_str)
    think, answer = get_tool_call(planner_prompt)
    tools_json = json.loads(answer)
    tools = tools_json.get("tools", [])
    tool_list = [t["name"] for t in tools]
    return planner_prompt, think, answer, tool_list
