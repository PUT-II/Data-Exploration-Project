def download_and_save(url_: str):
    import requests
    import os

    file_path = f'./images/{url_.split("/")[-2]}.jpg'
    if os.path.exists(file_path):
        return

    response = requests.get(url_)
    with open(file_path, mode='wb') as file:
        file.write(response.content)
