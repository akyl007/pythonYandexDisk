from django.shortcuts import render, redirect
from django.http import HttpResponse
import requests

YANDEX_API_URL = "https://cloud-api.yandex.net/v1/disk/public/resources"
YANDEX_DOWNLOAD_URL = "https://cloud-api.yandex.net/v1/disk/public/resources/download"


def index(request) -> HttpResponse:
    """
    Главная страница с формой для ввода публичной ссылки.

    :param request: объект HttpRequest
    :return: объект HttpResponse с формой для ввода публичной ссылки
    """
    return render(request, 'yandex_app/index.html')


def extract_public_key(public_url: str) -> str:
    """
    Извлекает публичный ключ из URL, если передана полная ссылка.

    :param public_url: строка URL или ключа
    :return: публичный ключ
    """
    # Проверяем, содержит ли ссылка домен "disk.yandex.kz" или "disk.yandex.ru"
    if "disk.yandex" in public_url:
        return public_url.split('/')[-1]  # Получаем последний сегмент URL
    return public_url


def files(request):
    """
    Получает список файлов по публичной ссылке и отображает их.
    """
    public_url = request.GET.get('public_key')

    if not public_url:
        return redirect('index')

    try:
        response = requests.get(YANDEX_API_URL, params={'public_key': public_url})
        print(f"Request URL: {response.url}")
        print(f"Status Code: {response.status_code}, Response: {response.text}")

        response.raise_for_status()

        items = response.json().get('_embedded', {}).get('items', [])
        return render(request, 'yandex_app/files.html', {'items': items, 'public_key': public_url})

    except requests.exceptions.HTTPError as http_err:
        error_message = f"HTTP error occurred: {http_err}"
        print(error_message)
        return HttpResponse(error_message, status=response.status_code)

    except Exception as err:
        error_message = f"Other error occurred: {err}"
        print(error_message)
        return HttpResponse("Ошибка при получении данных с Яндекс.Диска.", status=500)


def download_file(request) -> HttpResponse:
    """
    Скачивает выбранный файл с Яндекс.Диска.

    :param request: объект HttpRequest с параметрами 'public_key' и 'file_path'
    :return: объект HttpResponse с загруженным файлом или сообщение об ошибке
    """
    public_key = request.GET.get('public_key')
    file_path = request.GET.get('file_path')

    if not public_key or not file_path:
        return redirect('index')

    # Извлекаем публичный ключ
    public_key = extract_public_key(public_key)

    try:
        # Запрашиваем ссылку для скачивания файла
        response = requests.get(YANDEX_DOWNLOAD_URL, params={'public_key': public_key, 'path': file_path})

        print(f"Download Status Code: {response.status_code}, Response: {response.text}")

        response.raise_for_status()

        download_url = response.json().get('href')
        file_response = requests.get(download_url)

        response = HttpResponse(file_response.content, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file_path.split('/')[-1]}"'
        return response

    except requests.exceptions.HTTPError as http_err:
        error_message = f"HTTP error occurred: {http_err}"
        print(error_message)
        return HttpResponse(error_message, status=response.status_code)

    except Exception as err:
        error_message = f"Other error occurred: {err}"
        print(error_message)
        return HttpResponse("Ошибка при скачивании файла с Яндекс.Диска.", status=500)
