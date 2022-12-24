from django.core.paginator import Paginator

POSTS_TO_SHOW_ON_PAGE: int = 10


def dry_paginator(post_list, request):
    paginator = Paginator(post_list, POSTS_TO_SHOW_ON_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
