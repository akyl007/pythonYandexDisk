from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseNotFound
import requests
from django.views.decorators.http import require_http_methods

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