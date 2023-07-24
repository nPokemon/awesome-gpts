import json

from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import ResponseSchema, StructuredOutputParser, OutputFixingParser
from langchain.prompts import ChatPromptTemplate
from langchain.schema import OutputParserException
from pydantic import BaseModel, Field

from tools.chat import chat_completion, retry

chat = ChatOpenAI(
    model_name='gpt-3.5-turbo',
    temperature=0,
    max_tokens=4000,
)


class TranslateResponseSchema(BaseModel):
    result: str = Field(..., description="the translated value")

    @classmethod
    def schema(cls, by_alias=True):
        schema = super().schema(by_alias)
        schema.pop('title', None)
        return schema

    @classmethod
    def schema_json(cls, by_alias=True, **dumps_kwargs):
        schema_str = json.dumps(cls.schema(by_alias), **dumps_kwargs)
        return json.loads(schema_str)


class SummarizationResponseSchema(BaseModel):
    result: str = Field(..., description="the summarized value from value of res")

    @classmethod
    def schema(cls, by_alias=True):
        schema = super().schema(by_alias)
        schema.pop('title', None)
        return schema

    @classmethod
    def schema_json(cls, by_alias=True, **dumps_kwargs):
        schema_str = json.dumps(cls.schema(by_alias), **dumps_kwargs)
        return json.loads(schema_str)


def translate(text: str, lang: str) -> str:
    """Translate text to the specified language."""
    prompt_template = """
    Now you have to translate the following text into {lang}:
    ### Text to translate:
    {text}
    ### Target language:
    {lang}
    ### Output format:
    your translation should in the following format:
    {{'res': 'your translation'}}
    """
    function = [
        {
            "name": "print_translation",
            "description": "Print the translation for the given text.",
            "parameters": TranslateResponseSchema.schema_json()
        }
    ]

    message = prompt_template.format(text=text, lang=lang)
    # get the response from the chat
    response = chat_completion(message)

    # parse the response
    response = chat_completion(response.content, functions=function)
    result = eval(response['function_call']['arguments'])['result']
    return result


def classification(summary: str) -> dict:
    pass


@retry(Exception, tries=5, delay=1, backoff=5)
def summarization(description: str, readme: str) -> str:
    """Summarize the description and readme of the repo."""
    prompt_template = """
    Now you have to summarize the following text into a short paragraph:
    ### Description:
    {description}
    ### Readme:
    {readme}
    ### Output format:
    your summary should in the following format:
    {{'res': 'your summary'}}
    """
    prompt = prompt_template.format(description=description, readme=readme)
    if len(prompt) > 2000:
        prompt = prompt[:2000]
    # get the response from the chat
    response = chat_completion(prompt)
    # parse the response
    response = chat_completion(response.content, functions=[
        {
            "name": "print_summary",
            "description": "Print the summary for the given text.",
            "parameters": SummarizationResponseSchema.schema_json(),
        }
    ])
    print(response)
    result = eval(response['function_call']['arguments'])['result']
    return result


if __name__ == '__main__':
    text = 'Collection of Open Source Projects Related to GPT，GPT相关开源项目合集🚀、精选🔥🔥'
    lang = 'en'
    res = translate(text, lang)
    print(res)
