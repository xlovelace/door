import requests
import os

download_dir = '/home/xwq/Downloads/images'
image_url_txt_path = '/home/xwq/Downloads/image_urls.txt'
base_url = 'https://image.taidii.cn/'
headers = {
    'User-Agent': 'PostmanRuntime/7.20.1',
    'Host': 'image.taidii.cn',
    'Cache-Control': 'no-cache'
}

s = requests.Session()
# s.headers.update(headers)

def download(url):
    print(url)
    r = s.get(url, stream=True)
    filename = url.split('/')[-1]
    file_path = os.path.join(download_dir, filename)
    with open(file_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=1024):
            fd.write(chunk)


if __name__ == '__main__':
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    with open(image_url_txt_path, 'r',  encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            url = base_url + line
            print(url)
            download(url)
