from django.urls import path, re_path
from . import views

urlpatterns = [
    re_path(r'^$', views.index, name='index'),
    re_path(r'^products/$', views.product_list, name='product_list'),
    re_path(r'^statistics/$', views.statistics_view, name='statistics'),
    re_path(r'^charts/$', views.charts_view, name='charts'),
    re_path(r'^about/$', views.about, name='about'),
    re_path(r'^news/$', views.news_list, name='news_list'),
    re_path(r'^faq/$', views.faq_list, name='faq_list'),
    re_path(r'^report/$', views.customer_report, name='customer_report'),
    re_path(r'^promo/$', views.promo_codes, name='promo_codes'),
    re_path(r'^reviews/$', views.add_review, name='reviews'),
    re_path(r'^weather/$', views.weather_data, name='weather_data'),
    re_path(r'^contacts/$', views.contact_list, name='contact_list'),
    re_path(r'^vacancies/$', views.vacancy_list, name='vacancy_list'),
    re_path(r'^privacy/$', views.privacy_policy, name='privacy_policy'),
    re_path(r'^register/$', views.register, name='register'),
    re_path(r'^buy/(?P<product_id>\d+)/$', views.buy_product, name='buy_product'),
    re_path(r'^cart/$', views.view_cart, name='view_cart'),
    re_path(r'^cart/add/(?P<product_id>\d+)/$', views.add_to_cart, name='add_to_cart'),
    re_path(r'^cart/checkout/$', views.checkout, name='checkout'),
    re_path(r'^cart/remove/(?P<item_id>\d+)/$', views.remove_from_cart, name='remove_from_cart'),
    re_path(r'^cart/clear/$', views.clear_cart, name='clear_cart'),
]