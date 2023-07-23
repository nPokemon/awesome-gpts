import os

import openai
import tiktoken

openai.api_key = os.getenv("OPENAI_API_KEY")

import time
from functools import wraps
import logging

# 创建日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建日志处理器
handler = logging.StreamHandler()

# 创建日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# 将处理器添加到记录器
logger.addHandler(handler)


def retry(exceptions, tries=3, delay=1, backoff=2):
    """重试修饰器

    :param exceptions: 重试的异常类，可以是一个单独的异常，也可以是一个异常类元组
    :param tries: 重试的最大次数
    :param delay: 每次重试的延迟（秒）
    :param backoff: 延迟的倍数
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    msg = f"{str(e)}, Retrying in {mdelay} seconds..."
                    logger.warning(msg)
                    logger.warning(f"Function {func.__name__} retrying...")
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return func(*args, **kwargs)

        return wrapper

    return decorator


@retry(Exception, tries=3, delay=1, backoff=2)
def chat_completion(prompt: str, model_name: str = None, max_token=4000, system_prompt: str = None,
                    functions: list = None,
                    function_call: dict = None):
    if model_name is None:
        model_name = 'gpt-3.5-turbo'
    token_of_prompt = num_tokens_from_string(prompt, 'gpt-3.5-turbo')
    if token_of_prompt > max_token:
        raise ValueError(f"prompt token {token_of_prompt} > max_token {max_token}")
    max_token -= token_of_prompt
    if system_prompt is None:
        system_prompt = "You are a ai assistant, you can answer the user's question."
    completion = openai.ChatCompletion.create(
        functions=functions,
        function_call=function_call,
        stream=True,
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )


    start_time = time.time()
    result = ''
    # create variables to collect the stream of events
    collected_events = []
    completion_text = ''
    # iterate through the stream of events
    for event in completion:
        event_time = time.time() - start_time  # calculate the time delay of the event
        collected_events.append(event)  # save the event response
        event_text = event['choices'][0]['message']  # extract the text
        completion_text += event_text  # append the text
        print(f"Text received: {event_text} ({event_time:.2f} seconds after request)")  # print the delay and text
        event_token = num_tokens_from_string(event_text, model_name)
        if event_token > max_token:
            break
        max_token -= event_token
        result += event_text
    return result


def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens
