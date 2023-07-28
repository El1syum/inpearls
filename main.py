import asyncio
import random
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup

DOMAIN = 'https://www.inpearls.ru'
FILE_NAME = 'inpearls3.xml'
ENCODING = 'UTF-8'


async def get_urls(session):
    urls_list = []
    for page in range(15, 30):
        r = await session.get(f'{DOMAIN}/authors/list-famous?page={page}')
        soup = BeautifulSoup(await r.text(), 'lxml')
        urls = list(map(lambda i: urljoin(DOMAIN, i.find('a', class_='stretched-link').get('href')),
                        soup.find_all('div', attrs={'class': 'd-flex position-relative border-bottom py-3'})))
        urls_list.extend(urls)
    return urls_list


async def scrap(url, session, xml_doc):
    await asyncio.sleep(random.randint(1, 5))
    pearls = []
    page = 1
    enough = False
    while not enough:
        r = await session.get(f'{url}/page/{page}')
        print(r.status)
        if r.status != 200:
            await asyncio.sleep(1)
            continue
        soup = BeautifulSoup(await r.text(), 'lxml')
        try:
            cards = soup.find('div', class_='pearls').findChildren('div', class_='pearl')
            for card in cards:
                try:
                    text = card.find('p').text
                    title = card.find('a', class_='author-link').get('title')
                    if text in pearls:
                        enough = True
                        break
                    pearls.append(text)

                    item = ET.SubElement(xml_doc, 'item')
                    ET.SubElement(item, 'title').text = f'<![CDATA[{title}]]>'
                    ET.SubElement(item, 'content:encoded').text = f'<![CDATA[{text}]]>'
                    ET.SubElement(item, 'wp:post_type').text = '<![CDATA[post]]>'
                    ET.SubElement(item, 'wp:status').text = '<![CDATA[publish]]>'
                    ET.SubElement(item, 'category', domain='post_tag', nicename='citaty').text = '<![CDATA[Цитаты]]>'
                except AttributeError:
                    ...  # empty pearl
        except AttributeError as e:
            print(url, e)
            with open(f'index.html', 'w', encoding='utf-8') as file:
                file.write(await r.text())

        page += 1


async def gather_data():
    xml_doc = ET.Element('channel')
    ET.SubElement(xml_doc, 'language').text = 'ru-RU'
    ET.SubElement(xml_doc, 'wp:wxr_version').text = '1.2'
    author = ET.SubElement(xml_doc, 'wp:author')
    ET.SubElement(author, 'wp:author_id').text = '0'

    tasks = []
    session = aiohttp.ClientSession()
    urls = await get_urls(session)
    for url in urls:
        task = asyncio.create_task(scrap(url, session, xml_doc))
        tasks.append(task)

    await asyncio.gather(*tasks)

    tree = ET.ElementTree(xml_doc)
    tree.write(FILE_NAME, encoding=ENCODING, xml_declaration=True)
    with open(FILE_NAME, 'a', encoding=ENCODING) as file:
        file.write('</rss>')


def main():
    asyncio.run(gather_data())


if __name__ == '__main__':
    main()
