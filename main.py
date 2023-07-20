import json
import os

import requests
import markdown

# GitHub API的基础URL
BASE_URL = 'https://api.github.com/search/repositories'

# 你的GitHub个人访问令牌
TOKEN = os.getenv('GITHUB_TOKEN')

# 定义搜索规则列表
queries = [
    'gpt in:name,description',
    # 可以在这里添加更多的规则
]

# 请求头部，添加认证
headers = {
    'Authorization': f'token {TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

# 用于存储所有解析后的数据
all_parsed_data = []

for query in queries:
    # 设置分页参数
    page = 1
    per_page = 100  # 最大值

    # 用于跟踪已获取的记录数量
    count = 0

    while True:
        # 发送请求
        response = requests.get(f'{BASE_URL}?q={query}&page={page}&per_page={per_page}', headers=headers)

        # 如果请求成功
        if response.status_code == 200:
            # 获取返回的JSON数据
            data = response.json()

            # 遍历返回的仓库
            for repo in data['items']:
                # 如果已经达到了500条记录，跳出循环
                if count >= 500:
                    break

                # 解析仓库数据
                repo_data = {
                    'url': repo['html_url'],
                    'name': repo['name'],
                    'description': repo['description'],
                    'stars': repo['stargazers_count'],
                    'last_updated': repo['updated_at'],
                    'language': repo['language'],
                }
                # 添加到列表
                all_parsed_data.append(repo_data)

                # 更新计数器
                count += 1

            # 如果返回的数据少于per_page，或者已经达到了500条记录，表示没有更多数据，跳出循环
            if len(data['items']) < per_page or count >= 500:
                break

            # 否则，进入下一页
            page += 1

        else:
            # 如果请求失败，打印错误信息
            print(f'Request failed with status code {response.status_code}.')
            break

# 创建Markdown文档
md = markdown.Markdown()

# 用于存储Markdown文本
markdown_text = ''

# save data into json file
with open('data.json', 'w') as f:
    json.dump(all_parsed_data, f)

# 遍历解析后的数据
for repo in all_parsed_data:
    # 添加到Markdown文本
    markdown_text += f"## {repo['name']}\n"
    markdown_text += f"**Description**: {repo['description']}\n"
    markdown_text += f"**Stars**: {repo['stars']}\n"
    markdown_text += f"**Last updated**: {repo['last_updated']}\n"
    markdown_text += f"**Language**: {repo['language']}\n"
    markdown_text += '\n'

# 生成Markdown文档
html = md.convert(markdown_text)

# 将Markdown文本写入README文件
with open('README.md', 'w') as f:
    f.write(markdown_text)
