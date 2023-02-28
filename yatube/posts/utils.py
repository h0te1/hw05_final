from django.core.paginator import Paginator

from yatube.settings import PAGE_LIMIT


def paginator(request, posts, limit=PAGE_LIMIT):
    paginator = Paginator(posts, limit)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
