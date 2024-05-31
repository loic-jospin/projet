from django.shortcuts import render
from django.views import View
from .models import *
from django.contrib import messages
from django.db import transaction
from.utils import pagination, get_invoice
import pdfkit
import datetime
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from.decorators import *
from django.http import HttpResponse
from django.template.loader import get_template #j'importe le get template pour recuperer un fichier html

# Create your views here.
class HomeView(LoginrequireSuperuserMixin, View):
    """"Main view"""
    templates_name ='index.html'

    invoices = Invoice.objects.select_related('customer', 'save_by').all().order_by('-invoice_date_time')

    context = {
        'invoices':invoices
    }

    def get(self, request, *args, **kwargs):

        items = pagination(request, self.invoices)
        self.context['invoices'] = items

        return render(request, self.templates_name, self.context)
    
    def post(self, request, *args, **kwargs):

        #modify
        if request.POST.get('id_modified'):
            paid = request.POST.get('modified')
            try:
                obj = Invoice.objects.get(id=request.POST.get('id_modified'))
                if paid == 'True':

                    obj.paid = True

                else: 
                    obj.paid = False

                obj.save()
                messages.success(request, "change made successfully.")

            except Exception as e:

                messages.error(request, f"sorry, the following error has occured{e}.")
        #supprimer la facture
        if request.POST.get('id_supprimer'):
            try:
                obj= Invoice.objects.get(pk=request.POST.get('id_supprimer')) 
                obj.delete()
                messages.success(request, "the deletion was successful.")
            except Exception as e:
                messages.error(request, f"sorry, the following error has occured{e}.")           

        items = pagination(request, self.invoices)
        self.context['invoices'] = items
        return render(request, self.templates_name, self.context)
    
class AddCustomerView(LoginrequireSuperuserMixin, View):
    """ add new customer """
    template_name = 'add_customer.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    """ afficher le template """
    
    def post(self, request, *args, **kwargs):
        data={
            'name': request.POST.get('name'),
            'email': request.POST.get('email'),
            'phone': request.POST.get('phone'),
            'address': request.POST.get('address'),
            'age': request.POST.get('age'),
            'city': request.POST.get('city'),
            'zip_code': request.POST.get('zip'),
            'save_by': request.user
            }
        try:
            created=Customer.objects.create(**data)
            if created:
                messages.success(request, "Customer registered successfuly.")
            else:
                messages.error(request, "sorry try again the sent data is corrupt")    
        except Exception as e:
            messages.error(request, f"sorry our system is dectecting the following issues {e} ")
        return render(request, self.template_name)
    """ recuperer les valeurs """


class AddInvoiceView(LoginrequireSuperuserMixin, View):
    template_name ='add_invoice.html'
    customers =Customer.objects.select_related('save_by').all()

    context = {
        'customers':customers
    }
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.context)
    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        items = []

        try:
            customer =request.POST.get('customer')
            type =request.POST.get('invoice_type')
            articles =request.POST.getlist('article')
            qties =request.POST.getlist('qty')
            units =request.POST.getlist('unit')
            total_a =request.POST.getlist('total-a')
            total =request.POST.get('total')
            comment =request.POST.get('comment')
            invoice_object={
                'customer_id':customer,
                'save_by':request.user,
                'total':total,
                'invoice_type':type,
                'comments':comment
            }

            invoice = Invoice.objects.create(**invoice_object)
            for index, article in enumerate(articles):
                data =Article(
                    invoice_id =invoice.id,
                    name = article,
                    quantity =qties[index],
                    unit_price=units[index],
                    total=total_a[index],
                )
                items.append(data)
            created =Article.objects.bulk_create(items)
            if created:
                messages.success(request, "invoice created successfully.")
                
            else:
                messages.error(request, "invoice not created.")
        except Exception as e:
            messages.error(request, f"sorry the following error has occured  {e}.")
        return render(request, self.template_name, self.context)
    

class InvoiceVisualizationView(LoginrequireSuperuserMixin, View):
    """ma vue pour visualiser une facture"""
    template_name = 'invoice.html'

    def get(self, request, *args, **kwargs):
       pk =kwargs.get('pk')
       context = get_invoice(pk)
       return render(request, self.template_name, context)
    
"""
def get_invoice_pdf(request, *args, **kwargs):
    #generation du fichier html from html file
    pk = kwargs.get('pk')
    context = get_invoice(pk)
    context['date'] = datetime.datetime.today()
    #afficher le fichier html
    template = get_template('invoice_pdf.html')
    #render html witj context variables
    html = template.render(context)
    #option of pdf format
    options = { 
        'page-size':'Letter',
        'encoding':'UTF-8',
        'enable-local-file-access': ""
    }

    #generate pdf
    pdf = pdfkit.from_string(html, False, options)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition']="attachement"
    return response
    """
@superuser_required
def get_invoice_pdf(request, *args, **kwargs):
    # Récupérer l'ID de la facture à partir des arguments
    pk = kwargs.get('pk')
    context = get_invoice(pk)
    context['date'] = datetime.datetime.today()

    # Charger le template HTML
    template = get_template('invoice_pdf.html')

    # Rendre le template avec le contexte
    html = template.render(context)

    # Options pour le format PDF
    options = { 
        'page-size': 'Letter',
        'encoding': 'UTF-8',
        'enable-local-file-access': ""
    }

    # Chemin vers wkhtmltopdf (mettre à jour ce chemin selon l'emplacement réel de wkhtmltopdf.exe)
    path_wkhtmltopdf = 'C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

    # Générer le PDF à partir du HTML
    pdf = pdfkit.from_string(html, False, options=options, configuration=config)

    # Créer la réponse HTTP avec le PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice_{}.pdf"'.format(pk)
    
    return response
