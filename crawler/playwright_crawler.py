import asyncio
import os
import re
from urllib.parse import urlparse

from playwright.async_api import async_playwright, Response
from playwright_stealth import stealth_async

from utils.utils import CrawlerParams, make_info_file, stealth


async def playwright_main(url: str, target: str, gsb: str) -> str:
    async with async_playwright() as playwright:
        # ブラウザを起動
        browser = await playwright.chromium.launch_persistent_context(
            os.path.join(os.getcwd(), 'tmp/playwright'),
            headless=False,
            ignore_https_errors=True,
            java_script_enabled=True,
            user_agent=CrawlerParams.USER_AGENT_FIREFOX,
            locale="ja",
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
        )
        # 新しいページを開く
        page = await browser.new_page()
        # 検知回避策
        await stealth_async(page)
        await stealth(page)
        # URLに移動
        await page.goto(url)
        await page.wait_for_timeout(3000)
        # URLがパスのみの場合, index.htmlを追加
        if page.url.endswith("/"):
            new_url = f"{page.url}index.html"
        else:
            new_url = page.url
        # 保存ディレクトリとinfo.txtを作成
        saved_dirname = await make_info_file(f".{urlparse(new_url).path}.html", "", page.url, target, gsb)
        # ページの再読み込み
        await page.close()
        page = await browser.new_page()
        # リソースを保存
        page.on('response', lambda res: save_resources(res, f'{saved_dirname}'))
        await page.goto(url)
        await page.wait_for_timeout(3000)
        # スクショを保存
        await page.screenshot(path=f'{saved_dirname}/snapshot.png', full_page=True)
        # 10秒待機
        await asyncio.sleep(3)
        # ページを保存
        page_content = await page.content()
        depth = urlparse(page.url).path.count('/') - 1
        print(depth)
        await save_main_page(page_content, f'{saved_dirname}{urlparse(new_url).path}', depth)

        # zip化
        # filename = urlparse(page.url).netloc
        # shutil.make_archive(filename, format='zip', root_dir=saved_dirname)
        # shutil.move(f'{filename}.zip', saved_dirname)

        return urlparse(page.url).netloc


async def save_resources(res: Response, dirname: str) -> None:
    body = await res.body()
    url = res.url

    filename = f'{dirname}{urlparse(url).path}'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    try:
        with open(filename, 'wb') as f:
            f.write(body)
    except:
        with open(filename, 'wb') as f:
            f.write(body)

    print(f'{url}\n{filename}\n')


async def save_main_page(content: str, filename: str, depth: int) -> None:
    # パスの書き換え
    add_path = "../" * depth if depth >= 1 else "./"
    content = re.sub('src="//', 'src="https://', content)
    content = re.sub('href="//', 'href="https://', content)
    content = re.sub('src="/(.+?)"', f'src="{add_path}\\1"', content)
    content = re.sub('href="/(.+?)"', f'href="{add_path}\\1"', content)

    pathname = os.path.split(filename)[0]
    filename = f'{pathname}/index.html'

    # 内容を保存
    os.makedirs(pathname, exist_ok=True)
    with open(filename, 'w') as f:
        f.write(content)
    # ファイル名の最後にhtmlを追加
    os.rename(filename, f'{filename}.html')


if __name__ == '__main__':
    input_url = input("URLを入力してください > ")
    input_target = input("Targetを入力してください > ")
    input_gsb = input("GSBを入力してください > ")
    asyncio.run(playwright_main(input_url, input_target, input_gsb))
