from .models import *
from django.core.paginator import (Paginator, EmptyPage, PageNotAnInteger)

def pagination(request, invoices):
        default_page = 1
        page = request.GET.get('page', default_page)
        paginator = Paginator(invoices, 5)
        try:
            items_page = paginator.page(page)
        except PageNotAnInteger:
            items_page = paginator.page(default_page)
        except EmptyPage:
            items_page = paginator.page(paginator.num_pages)
        return items_page

def get_invoice(pk):
    
     
     obj = Invoice.objects.get(pk=pk)
     articles = obj.article_set.all()
     context = {
            'obj':obj,
            'articles':articles
        }
     return context