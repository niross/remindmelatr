from math import floor
from datetime import date

from django import template
from django.template.loader import get_template
from django.core.urlresolvers import reverse


register = template.Library()


@register.simple_tag
def age(bday, d=None):
    if d is None:
        d = date.today()
    return (d.year - bday.year) - int((d.month, d.day) < (bday.month, bday.day))


@register.simple_tag
def navactive(request, urls, arg=None):
    for url in urls.split():
        if arg is not None:
            rev = reverse(url, args=[arg])
        else:
            rev = reverse(url)
        try:
            if request.path == rev:
                return "active"
        except AttributeError:
            pass
    return ""


@register.tag('common_paginate')
def common_paginate(parser, token):
    bits = token.contents.split()
    """
    Pass all of the arguments defined in the template tag except the first one,
    which will be the name of the template tag itself.
    Example: {% do_whatever arg1 arg2 arg3 %}
    *bits[1:] would be: [arg1, arg2, arg3]
    """
    return PaginationNode(*bits[1:])


class PaginationNode(template.Node):
    def __init__(self, page, pages, search_term):
        self.page = template.Variable(page)
        self.pages = int(pages)
        self.search_term = template.Variable(search_term)

    def render(self, context):
        page = self.page.resolve(context)
        search_term = self.search_term.resolve(context)

        pages_to_show = int(self.pages)
        if pages_to_show < 1:
            raise ValueError(
                'Pagination pages_to_show should be a positive '
                'integer, you specified %s' % pages_to_show
            )
        num_pages = page.paginator.num_pages
        current_page = page.number
        half_page_num = int(floor(pages_to_show / 2)) - 1
        if half_page_num < 0:
            half_page_num = 0
        first_page = current_page - half_page_num
        if first_page <= 1:
            first_page = 1
        if first_page > 1:
            pages_back = first_page - half_page_num
            if pages_back < 1:
                pages_back = 1
        else:
            pages_back = None
        last_page = first_page + pages_to_show - 1
        if pages_back is None:
            last_page += 1
        if last_page > num_pages:
            last_page = num_pages
        if last_page < num_pages:
            pages_forward = last_page + half_page_num
            if pages_forward > num_pages:
                pages_forward = num_pages
        else:
            pages_forward = None
            if first_page > 1:
                first_page -= 1
            if pages_back > 1:
                pages_back -= 1
            else:
                pages_back = None

        next_page = None
        if current_page < num_pages:
            next_page = (current_page + 1)

        prev_page = None
        if current_page > 1:
            prev_page = (current_page - 1)

        pages_shown = []
        for i in range(first_page, last_page + 1):
            pages_shown.append(i)
        return get_template("pagination.html").render(
            template.Context({
                'num_pages': num_pages,
                'current_page': current_page,
                'first_page': first_page,
                'last_page': last_page,
                'pages_shown': pages_shown,
                'pages_back': pages_back,
                'pages_forward': pages_forward,
                'search_term': search_term,
                'next_page': next_page,
                'prev_page': prev_page,
            })
        )


# Loop through the replies in a message
@register.assignment_tag
def message_replies(message):
    replies = []
    while True:
        if message.parent_msg:
            message = message.parent_msg
            replies.append(message)
        else:
            break
    return replies


@register.simple_tag
def pluralize_name(name):

    # If the whole name is in uppercase return an uppercase 'S'
    plural = 'S'
    for n in name:
        if n.isalpha() and not n.isupper() and not n.isdigit():
            plural = 's'
            break

    if name.lower().endswith('s'):
        return '%s\'' % name

    return '%s\'%s' % (name, plural)


@register.simple_tag
def range_list(value):
    return range(value)
