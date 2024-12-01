import asyncio
import os
import re
from urllib.parse import urlparse, unquote

from playwright.async_api import async_playwright, Response
from playwright_stealth import stealth_async

from utils.utils import make_info_file, stealth


async def playwright_main(mobile: str, url: str, target: str, gsb: str) -> str:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        if mobile == "y":
            context = await browser.new_context(
                ignore_https_errors=True,
                java_script_enabled=True,
                locale="ja",
                user_agent="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
            )
        else:
            context = await browser.new_context(
                ignore_https_errors=True,
                java_script_enabled=True,
                locale="ja",
            )

        # 新しいページを開く
        page = await context.new_page()

        # 検知回避策
        await stealth_async(page)
        await stealth(page)

        # URLに移動
        await page.goto(url)
        await page.wait_for_load_state()
        await page.wait_for_timeout(5000)

        # URLがパスのみの場合, .htmlを追加
        parsed = urlparse(page.url)
        if page.url.endswith("/"):
            new_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}index.html"
        elif not page.url.endswith(".html"):
            new_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}.html"
        else:
            new_url = page.url

        # 保存ディレクトリとinfo.txtを作成
        saved_dirname = await make_info_file(f".{urlparse(new_url).path}", "", page.url, target, gsb)

        # ページの再読み込み
        await page.close()
        page = await context.new_page()
        page.on("response", lambda res: save_resources(res, saved_dirname))  # リソース保存設定
        await page.goto(url)
        await page.wait_for_load_state()
        await page.wait_for_timeout(5000)

        # スクショを保存
        await page.screenshot(path=f'{saved_dirname}/snapshot.png', full_page=True)

        # ページを保存
        page_content = await page.content()
        depth = urlparse(page.url).path.count("/") - 1
        await save_main_page(page_content, f"{saved_dirname}{urlparse(new_url).path}", depth)

        return urlparse(page.url).netloc


async def save_resources(res: Response, dirname: str) -> None:
    # URLの最後が / なら保存しないで終了
    if res.url.endswith("/"):
        return

    filename = f"{dirname}{urlparse(unquote(res.url)).path}"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, "wb") as f:
        f.write(await res.body())

    print(res.url)
    print(filename)


async def save_main_page(content: str, filename: str, depth: int) -> None:
    # パスの書き換え
    add_path = "../" * depth if depth >= 1 else "./"
    # // を https:// に変換
    content = re.sub('src="//', 'src="https://', content)
    content = re.sub('href="//', 'href="https://', content)
    # /path を ./path に変換
    content = re.sub('src="/(.+?)"', f'src="{add_path}\\1"', content)
    content = re.sub('href="/(.+?)"', f'href="{add_path}\\1"', content)

    # 内容を保存
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        f.write(content)

    print("main page")
    print(filename)


if __name__ == "__main__":
    input_mobile = input("AndroidのUser-Agentを使用しますか (y/n) ")
    input_urls = input("URLを入力してください > ")
    input_target = input("Targetを入力してください > ")
    input_gsb = input("GSBを入力してください > ")

    # URLが複数ある場合は連続で保存
    for input_url in [url for url in input_urls.split(" ") if url != ""]:
        asyncio.run(playwright_main(input_mobile, input_url, input_target, input_gsb))
        print("\n")
