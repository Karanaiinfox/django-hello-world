from django.contrib import admin
from django.urls import path,include
from . import views
urlpatterns = [
    path("",views.index),
    path("login",views.login),
    path("callback1",views.callback1),
    path("callback",views.callback),
    path("upload_csv",views.upload_csv),
    path("line_item",views.line_item),
    path("invoices",views.get_invoices),
    path("import_invoices",views.import_invoices),
    path("getitems",views.get_item_info),
    path("import_item",views.import_item),
    path("companyinfo",views.get_company_info)

]