import os
from openai import OpenAI

extra_body = {"enable_thinking": True}

client = OpenAI(
    api_key='sk-xxx',
    base_url="https://api.deepseek.com",
)


def get_result(content: str):
    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=[
            {
                "role": "system",
                "content": """Please give your answer in json in the flollowing format:
{
  "answer": ["X1", "X2", ...]
}
here X1 means the classification result for each depth point.
There are only nine categories: 'Nonmarine sandstone', 'Nonmarine coarse siltstone', 'Nonmarine fine siltstone',
'Marine siltstone and shale', 'Mudstone', 'Wackestone', 'Dolomite', 'Packstone-grainstone', 'Phylloid-algal bafflestone'.
Your result for each depth point should be one of the nine categories above.
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
    answer = response.choices[0].message.content
    return think, answer


def get_result_trend(content: str):
    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
        stream=False,
        extra_body=extra_body,
    )

    think = response.choices[0].message.reasoning_content
    answer = response.choices[0].message.content
    return think, answer
