def main():
    urls = input("URL >")
    url_list = [url.replace("hxxp", "http") for url in urls.split("\n")]

    for url in url_list:
        print(url)


if __name__ == '__main__':
    main()
