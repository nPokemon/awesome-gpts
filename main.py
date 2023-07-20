import base64
import os
import shutil
from datetime import datetime, timedelta

import requests

# GitHub API的基础URL
BASE_URL = 'https://api.github.com/search/repositories'
README_URL_TEMPLATE = 'https://api.github.com/repos/{owner}/{repo}/readme'

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


def get_readme_content(full_name):
    readme_url = README_URL_TEMPLATE.format(owner=full_name.split('/')[0], repo=full_name.split('/')[1])
    readme_response = requests.get(readme_url, headers=headers)

    if readme_response.status_code == 200:
        readme_data = readme_response.json()
        # Base64解码README内容
        readme_content = base64.b64decode(readme_data['content']).decode('utf-8')
        return readme_content
    else:
        return None


def archive_previous_readme():
    # 判断README.md是否存在
    if os.path.isfile('README.md'):
        # 获取当前日期的前一天
        previous_date = datetime.now() - timedelta(days=1)
        # 格式化日期
        formatted_date = previous_date.strftime('%Y-%m-%d')

        # 创建archived文件夹，如果不存在
        if not os.path.isdir('archived'):
            os.mkdir('archived')

        # 移动并重命名文件
        shutil.move('README.md', f'archived/README_{formatted_date}.md')


def load_blacklist():
    with open('blacklist.txt', 'r') as f:
        return [line.strip() for line in f]


def get_repository_data(query, max_repos=500):
    blacklist = load_blacklist()

    # 设置分页参数
    page = 1
    per_page = 100  # 最大值
    # 用于跟踪已获取的记录数量
    count = 0
    # 用于存储所有解析后的数据
    all_parsed_data = []

    while True:
        # 发送请求
        response = requests.get(f'{BASE_URL}?q={query}&sort=stars&order=desc&page={page}&per_page={per_page}',
                                headers=headers)

        # 如果请求成功
        if response.status_code == 200:
            # 获取返回的JSON数据
            data = response.json()

            # 遍历返回的仓库
            for repo in data['items']:
                if repo['full_name'] in blacklist:
                    continue  # 跳过黑名单中的仓库

                # 如果已经达到了max_repos条记录，跳出循环
                if count >= max_repos:
                    break

                last_updated = datetime.strptime(repo['updated_at'], '%Y-%m-%dT%H:%M:%SZ')

                # 解析仓库数据
                repo_data = {
                    'url': repo['html_url'],
                    'name': repo['name'],
                    'description': repo['description'],
                    'stars': repo['stargazers_count'],
                    'last_updated': last_updated.strftime('%Y-%m-%d'),
                    'language': repo['language'],
                    'readme': get_readme_content(repo['full_name'])
                }
                # 添加到列表
                all_parsed_data.append(repo_data)

                # 更新计数器
                count += 1

            # 如果返回的数据少于per_page，或者已经达到了max_repos条记录，表示没有更多数据，跳出循环
            if len(data['items']) < per_page or count >= max_repos:
                break

            # 否则，进入下一页
            page += 1

        else:
            # 如果请求失败，打印错误信息
            print(f'Request failed with status code {response.status_code}.')
            break

    return all_parsed_data


def main():
    # 遍历每个搜索规则，获取仓库数据
    all_parsed_data = []
    for query in queries:
        all_parsed_data.extend(get_repository_data(query))


    # 用于存储Markdown文本
    # 用于存储Markdown文本
    markdown_text = ''

    # 添加开头部分
    markdown_text += '# Awesome GPT Repositories\n\n'
    markdown_text += 'This repository provides a curated list of GitHub repositories related to GPT. \
    These repositories are automatically collected and updated daily based on the following criteria:\n\n'
    markdown_text += '1. The repository name or description contains "GPT" (case-insensitive).\n'
    markdown_text += '2. The repositories are sorted by the number of stars in descending order.\n\n'
    markdown_text += 'Last updated: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\n\n'

    # 添加Markdown表格的头部
    markdown_text += '| Name | Description | Language | Star|Last updated |\n'
    markdown_text += '| ---- | ----------- | -------- | ----|------------ |\n'

    # 遍历解析后的数据
    for repo in all_parsed_data:
        # 添加到Markdown表格
        markdown_text += f"| [{repo['name']}]({repo['url']}) | {repo['description']} | {repo['stars']}| {repo['language']} | {repo['last_updated']} |\n"

    # 将Markdown文本写入README文件
    with open('README.md', 'w') as f:
        f.write(markdown_text)


if __name__ == '__main__':
    archive_previous_readme()
    main()
