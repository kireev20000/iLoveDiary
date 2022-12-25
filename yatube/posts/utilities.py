from django.core.handlers.wsgi import WSGIRequest
from django.core.paginator import Page, Paginator
from django.db.models import QuerySet


def dry_paginator(
        post_list: QuerySet,
        request: WSGIRequest,
        posts_on_page: int = 10
) -> Page:
    """
    Принимает на вход кварисет и реквест, и возращает пагинатор.
    """
    paginator = Paginator(post_list, posts_on_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
