from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import ResponseSchema, StructuredOutputParser, OutputFixingParser
from langchain.prompts import ChatPromptTemplate
from langchain.schema import OutputParserException
from pydantic import BaseModel

from tools.chat import chat_completion

chat = ChatOpenAI(
    model_name='gpt-3.5-turbo',
    temperature=0,
    max_tokens=4000,
)


class ResponseSchema(BaseModel):
    translations: str


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
            "parameters": ResponseSchema.schema()
        }
    ]
    function_call = {
        "name": "print_translation",
    }

    message = prompt_template.format(text=text, lang=lang)
    res = chat_completion(message, functions=function, function_call=function_call)
    return res


def classification(summary: str) -> dict:
    pass


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
    message = ChatPromptTemplate.from_template(prompt_template)
    response_schema = ResponseSchema(
        name="res",
        description="your summary",
        type="dict",
    )
    output_parser = StructuredOutputParser.from_response_schemas([response_schema])
    format_instructions = output_parser.get_format_instructions()
    prompt = message.format_messages(
        description=description,
        readme=readme,
        format_instructions=format_instructions,
    )
    if len(prompt) > 1000:
        prompt = prompt[:1000]
    print(len(prompt))
    res = chat(prompt)
    try:
        print(res.content)
        res = output_parser.parse(res.content)
        return res["res"]
    except OutputParserException as exc:
        print(exc)
        fix_parse = OutputFixingParser.from_llm(parser=output_parser, llm=chat)
        res = fix_parse.parse(res.content)
        return res["res"]


if __name__ == '__main__':
    text = 'Collection of Open Source Projects Related to GPT，GPT相关开源项目合集🚀、精选🔥🔥'
    lang = 'en'
    res = translate(text, lang)
    print(res)
