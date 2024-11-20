# novel crawler for cnl48.cc
import json
import requests
from bs4 import BeautifulSoup
import re
import os
import time
import random
import sys

def random_sleep():
    time.sleep(random.randint(1, 3))


def get_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    first = True
    while True:
        if not first:
            print('Retrying...')
            random_sleep()
        first = False
        try:
            r = requests.get(url, headers=headers)
            r.raise_for_status()
            r.encoding = r.apparent_encoding
            return r.text
        except Exception as e:
            print('Error in get_html:', e)


def get_content(url):
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.find('h1').text
    content = soup.find('div', id='content')
    # remove the <p style=...> part of content
    for p in content.find_all('p'):
        p.decompose()
    content = content.text
    # remove <br> and <p> tags
    content = content.replace('<br>', '')
    content = content.replace('<p>', '')
    return title, content


def get_chapter_list(url):
    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    chapter_list_origin = soup.find('div', id='list')
    chapter_list_origin = chapter_list_origin.find('dl')
    # the chapter links are <dd>, which start after the 2nd <dt> tag
    chapter_list_origin = chapter_list_origin.find_all('dt')[1].next_siblings
    chapter_list = []
    for chapter in chapter_list_origin:
        if chapter.name == 'dd':
            chapter_list.append((chapter.a.text, 'https://www.cnl48.cc' + chapter.a['href']))
    return chapter_list


def write_to_text(chapters, filename):
    with open(filename, 'w', encoding='gbk') as f:
        for chapter_title, content in chapters.items():
            f.write(chapter_title + '\n\n')
            f.write(content + '\n\n')


def process_content(content, chapter_title):
    if type(content) == str:
        content_list = []
        content = content.split('\r')
        content = [c.split('\n') for c in content]
        for c in content:
            content_list.extend(c)
        content = content_list
    assert type(content) == list
    content = [re.sub(r'<div.*?>', '', line.strip()) for line in content]
    content = ['    ' + line for line in content if line != '' and line != chapter_title]
    # concatenate the lines
    content = '\n'.join(content)
    return content

def main(url):
    # make dir_path exists_ok
    dir_path = 'output'
    os.makedirs(dir_path, exist_ok=True)

    html = get_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.find('h1').text
    print('Title: {}'.format(title))
    json_name = title + '.json'
    filename = title + '.txt'
    json_name = os.path.join(dir_path, json_name)
    filename = os.path.join(dir_path, filename)
    chapter_list = get_chapter_list(url)
    print('Total chapters:', len(chapter_list))
    print("Chapter list:", chapter_list)

    chapters = {}
    if os.path.exists(json_name):
        with open(json_name, 'r') as f:
            chapters = json.load(f)
        for chapter_title, content in chapters.items():
            chapters[chapter_title] = process_content(content, chapter_title)

    write_to_text(chapters, filename)

    for chapter_title, chapter_url in chapter_list:
        if chapter_title in chapters:
            print('Chapter {} already exists'.format(chapter_title))
        else:
            chapter_title_1, content = get_content(chapter_url)
            assert chapter_title == chapter_title_1
            chapters[chapter_title] = process_content(content, chapter_title)
            random_sleep()
            print('Chapter {} done'.format(chapter_title))
            with open(json_name, 'w') as f:
                json.dump(chapters, f)

    with open(json_name, 'w') as f:
        json.dump(chapters, f)

    write_to_text(chapters, filename)


if __name__ == '__main__':
    url = 'https://www.cnl48.cc/info/42560056445/'
    main(url)
