import asyncio
import os
import shutil
from urllib.parse import urlparse

from playwright.async_api import async_playwright

from utils.utils import CrawlerParams, make_info_file


async def wget_main(url: str, target: str, gsb: str):
    async with async_playwright() as playwright:
        # ブラウザを起動
        browser = await playwright.chromium.launch_persistent_context(
            os.path.join(os.getcwd(), 'tmp/playwright'),
            headless=True,
            ignore_https_errors=True,
            java_script_enabled=True,
            user_agent=CrawlerParams.USER_AGENT,
            args=["--disable-blink-features=AutomationControlled"],
        )
        print("[PlayWright] PlayWright Started")

        # 新しいページを開く
        page = await browser.new_page()
        # navigator.webdriverを削除
        await page.add_init_script("() => Object.defineProperty(navigator,\"webdriver\",{get: () => undefined})")
        # URLに移動
        await page.goto(url, wait_until="load")
        # 保存ディレクトリとinfo.txtを作成
        saved_dirname = await make_info_file(f".{urlparse(page.url).path}", "", page.url, target, gsb)
        print("[PlayWright] Saved Directory Created")

        # スクショを保存
        await page.screenshot(path=f'{saved_dirname}/snapshot.png', full_page=True)
        print("[PlayWright] Screenshot Saved")

        # wgetで保存
        await save_contents(url)

        # zip化
        filename = urlparse(url).netloc
        shutil.make_archive(filename, format='zip', root_dir=f'../Saved/{filename}')
        shutil.move(f'{filename}.zip', f'../Saved/{filename}')

        return urlparse(url).netloc


async def save_contents(url: str) -> None:
    os.chdir("../Saved")
    proc = await asyncio.create_subprocess_exec(
        'wget',
        '--wait=3',
        '-p',
        '-r',
        '-k',
        '-level=1',
        '-x',
        '-e',
        'robots=off',
        '--keep-session-cookies',
        f'--user-agent="{CrawlerParams.USER_AGENT}"',
        '--no-check-certificate',
        url,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    while True:
        if proc.stdout.at_eof():
            break

        stdout = (await proc.stdout.readline()).decode()
        if stdout:
            print(f'[stdout] {stdout}', end='', flush=True)

    await proc.communicate()

    print(f'exited with {proc.returncode}')

    os.chdir("../crawler")


if __name__ == '__main__':
    input_url = input("URLを入力してください > ")
    input_target = input("Targetを入力してください > ")
    input_gsb = input("GSBを入力してください > ")
    asyncio.run(wget_main(input_url, input_target, input_gsb))
