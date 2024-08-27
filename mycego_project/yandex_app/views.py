from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseNotFound
import requests
from django.views.decorators.http import require_http_methods
from typing import List

YANDEX_API_URL = "https://cloud-api.yandex.net/v1/disk/public/resources"
YANDEX_DOWNLOAD_URL = "https://cloud-api.yandex.net/v1/disk/public/resources/download"

def index(request) -> HttpResponse:
    """
    Главная страница с формой для ввода публичной ссылки.
    """
    return render(request, 'yandex_app/index.html')

def extract_public_key(public_url: str) -> str:
    """
    Извлекает публичный ключ из URL, если передана полная ссылка.
    """
    if "disk.yandex" in public_url:
        return public_url.split('/')[-1]
    return public_url

def files(request) -> HttpResponse:
    """
    Получает список файлов по публичной ссылке и отображает их.
    """
    public_url = request.GET.get('public_key')
    file_type = request.GET.get('file_type')

    if not public_url:
        return redirect('index')

    try:
        response = requests.get(YANDEX_API_URL, params={'public_key': public_url})
        response.raise_for_status()
        items = response.json().get('_embedded', {}).get('items', [])

        if file_type:
            items = [item for item in items if item['mime_type'].startswith(file_type)]

        return render(request, 'yandex_app/files.html', {'items': items, 'public_key': public_url})

    except requests.exceptions.HTTPError as http_err:
        return HttpResponse(f"HTTP error occurred: {http_err}", status=response.status_code)
    except Exception as err:
        return HttpResponse(f"Other error occurred: {err}", status=500)

@require_http_methods(["POST"])
def download_multiple(request) -> HttpResponse:
    public_key = request.POST.get('public_key')
    file_ids = request.POST.getlist('file_ids')

    if not public_key or not file_ids:
        return HttpResponseNotFound("Параметры запроса отсутствуют.")

    download_urls = []
    for file_id in file_ids:
        try:
            download_url = f"{YANDEX_DOWNLOAD_URL}?public_key={public_key}&path={file_id}"
            response = requests.get(download_url)
            response.raise_for_status()
            download_link = response.json().get('href')
            if download_link:
                download_urls.append(download_link)
        except requests.exceptions.HTTPError as http_err:
            return HttpResponseNotFound(f"HTTP ошибка при получении файла {file_id}: {http_err}")
        except Exception as err:
            return HttpResponseNotFound(f"Ошибка при получении файла {file_id}: {err}")

    if not download_urls:
        return HttpResponseNotFound("Не удалось найти ссылки для скачивания.")

    # Формируем HTML с несколькими ссылками для скачивания
    links_html = ''.join([f'<a href="{url}" download></a>' for url in download_urls])
    return HttpResponse(links_html)

@require_http_methods(["GET"])
def download_file(request):
    public_key = request.GET.get('public_key')
    file_path = request.GET.get('file_path')
    file_name = request.GET.get('file_name')

    if not all([public_key, file_path, file_name]):
        return HttpResponseNotFound("Параметры запроса отсутствуют.")

    # Преобразование пути к файлу в URL для скачивания
    download_url = f"{YANDEX_DOWNLOAD_URL}?public_key={public_key}&path={file_path}"

    try:
        response = requests.get(download_url)
        response.raise_for_status()  # Это вызывает исключение при ошибках HTTP
        download_link = response.json().get('href')

        if not download_link:
            return HttpResponseNotFound("Не удалось найти ссылку для скачивания.")

        # Редирект на ссылку для скачивания
        return HttpResponse(f'<a href="{download_link}" download>Скачать {file_name}</a>')

    except requests.exceptions.HTTPError as http_err:
        return HttpResponseNotFound(f"HTTP ошибка: {http_err}")
    except Exception as err:
        return HttpResponseNotFound(f"Ошибка: {err}")