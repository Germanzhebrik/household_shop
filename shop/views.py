import logging
import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Sum, Count, Max, StdDev, F, Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .forms import ExtendedRegisterForm
from django.contrib import messages
import calendar

from .models import (
    Product, Customer, Order, News, AboutCompany,
    FAQ, Contact, Vacancy, Review, PromoCode, Category
)

# Настройка логирования
logger = logging.getLogger(__name__)


@login_required
def buy_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Пытаемся найти профиль Customer для текущего User
    try:
        customer = request.user.customer
    except Customer.DoesNotExist:
        messages.error(request, "Ваш профиль клиента не найден. Обратитесь к администратору.")
        return redirect('product_list')

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))

        # Создаем заказ в базе данных
        Order.objects.create(
            customer=customer,
            product=product,
            quantity=quantity,
            order_date=timezone.now(),
            delivery_date=timezone.now() + timezone.timedelta(days=3)  # Пример: доставка через 3 дня
        )

        logger.info(f"Клиент {customer.full_name} купил {product.title} (x{quantity})")
        messages.success(request, f"Товар {product.title} успешно заказан!")
        return redirect('product_list')

    return render(request, 'shop/buy_confirm.html', {'product': product})

def is_employee(user):
    return user.is_authenticated and (user.is_staff or user.groups.filter(name='Employees').exists())


### 1. ГЛАВНАЯ СТРАНИЦА И ОБЩИЕ СТРАНИЦЫ ###

def index(request):
    """Главная: Краткая информация о последней новости"""
    latest_news = News.objects.order_by('-publish_date').first()

    # Использование стороннего API 1: Текущее время/Таймзона
    # (Пример: WorldTimeAPI)
    context = {
        'latest_news': latest_news,
        'now_local': timezone.localtime(timezone.now()),
        'calendar_text': calendar.TextCalendar().formatmonth(2026, 5),  # Текстовый календарь
    }
    return render(request, 'shop/index.html', context)


def about(request):
    """О компании"""
    info = AboutCompany.objects.first()
    return render(request, 'shop/about.html', {'info': info})


def news_list(request):
    """Список новостей"""
    news = News.objects.all().order_by('-publish_date')
    return render(request, 'shop/news.html', {'news': news})


def faq_list(request):
    """Словарь терминов / FAQ"""
    faqs = FAQ.objects.all()
    return render(request, 'shop/faq.html', {'faqs': faqs})


#2. Статистика и поиск(Для Админа/Сотрудника)

@user_passes_test(is_employee)
def statistics_view(request):
    """Статистические показатели по предметной области"""

    # 1. Клиенты
    # Средний возраст
    avg_age = Customer.objects.aggregate(Avg('age'))['age__avg']

    # Медиана возраста (считаем на уровне Python, так как в ORM нет встроенной медианы)
    ages = list(Customer.objects.values_list('age', flat=True).order_by('age'))
    median_age = 0
    if ages:
        mid = len(ages) // 2
        median_age = (ages[mid] + ages[mid - 1]) / 2 if len(ages) % 2 == 0 else ages[mid]

    # 2. продажи (суммы)
    # Общая сумма продаж (Цена * Количество)
    total_sales = Order.objects.aggregate(
        total=Sum(F('product__price') * F('quantity'))
    )['total'] or 0

    #3. Товары и категории
    # Самый популярный товар (по количеству проданных единиц)
    popular_product = Product.objects.annotate(
        total_sold=Sum('order__quantity')
    ).order_by('-total_sold').first()

    # Товар, не пользующийся спросом (ни одного заказа) - из таблицы требований
    unpopular_products = Product.objects.filter(order__isnull=True)

    # Какой тип товаров (категория) наиболее популярен? (по количеству продаж)
    popular_category = Category.objects.annotate(
        total_sold=Sum('products__order__quantity')
    ).order_by('-total_sold').first()

    # Какой тип товаров приносит наибольшую прибыль? (Цена * Количество в заказах)
    category_profit = Category.objects.annotate(
        profit=Sum(F('products__order__quantity') * F('products__price'))
    ).order_by('-profit')

    context = {
        'avg_age': round(avg_age, 1) if avg_age else 0,
        'median_age': median_age,
        'total_sales': total_sales,
        'popular_product': popular_product,
        'unpopular_products': unpopular_products,
        'popular_category': popular_category,
        'category_profit': category_profit,
    }
    return render(request, 'shop/statistics.html', context)


### 3. РАБОТА С КЛИЕНТАМИ И ТОВАРАМИ (CRUD & Поиск) ###

def product_list(request):
    # 1. Получаем базовый запрос
    products = Product.objects.all()

    # 2. ПОИСК (по названию, категории или производителю)
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(title__icontains=query) |
            Q(category__name__icontains=query) |
            Q(manufacturer__name__icontains=query)
        )

    # 3. СОРТИРОВКА
    sort_by = request.GET.get('sort', 'title')  # По умолчанию сортируем по названию

    # Белый список полей, чтобы пользователь не сломал запрос через URL
    allowed_sort = ['title', '-title', 'price', '-price', 'created_at', '-created_at']
    if sort_by in allowed_sort:
        products = products.order_by(sort_by)

    return render(request, 'shop/product_list.html', {
        'products': products,
        'current_query': query or '',
        'current_sort': sort_by
    })


@login_required
def add_review(request):
    """Добавление отзыва (только для залогиненных)"""
    if request.method == 'POST':
        name = request.POST.get('name')
        text = request.POST.get('text')
        rating = request.POST.get('rating')

        Review.objects.create(name=name, text=text, rating=rating)
        logger.info(f"User {request.user} added a new review.")  # Логирование
        return redirect('reviews')

    return render(request, 'shop/add_review.html')


### 4. СТОРОННИЕ API ###
def weather_data(request):
    """Использование стороннего API 2: Погода (OpenWeatherMap)"""
    city = "Minsk"
    api_key = "91dbede76dee6c0a024ec1fd0b4753e5"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    try:
        response = requests.get(url, timeout=1)
        response.raise_for_status()
        data = response.json()
        temp = data['main']['temp']
    except Exception as e:
        logger.error(f"Ошибка при получении погоды: {str(e)}", exc_info=True)
        temp = "Н/Д"

    return JsonResponse({'city': city, 'temp': temp})


### 5. СТРАНИЦЫ ПО ИНДИВИДУАЛЬНОМУ ЗАДАНИЮ (Вариант 10) ###

@user_passes_test(is_employee)
def customer_report(request):
    """Отчет по клиентам для сотрудников"""
    # Добавляем select_related, чтобы подтянуть данные аккаунтов (User)
    customers = Customer.objects.select_related('user').all()
    return render(request, 'shop/customer_report.html', {'customers': customers})


def promo_codes(request):
    """Список промокодов (действующие и архивные)"""
    active_promos = PromoCode.objects.filter(is_archived=False)
    archived_promos = PromoCode.objects.filter(is_archived=True)
    return render(request, 'shop/promo.html', {
        'active': active_promos,
        'archived': archived_promos
    })

def contact_list(request):
    """Список сотрудников (Контакты)"""
    contacts = Contact.objects.all()
    return render(request, 'shop/contacts.html', {'contacts': contacts})

def vacancy_list(request):
    """Список вакансий"""
    vacancies = Vacancy.objects.filter(is_active=True)
    return render(request, 'shop/vacancies.html', {'vacancies': vacancies})

def privacy_policy(request):
    """Пустая страница политики конфиденциальности"""
    return render(request, 'shop/privacy.html')

@csrf_protect
def register(request):
    if request.method == 'POST':
        form = ExtendedRegisterForm(request.POST)
        if form.is_valid():
            # 1. Создаем системного пользователя (User)
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # 2. Создаем связанную запись в вашей модели Customer
            Customer.objects.create(
                user=user,  # Привязываем к аккаунту
                full_name=f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}",
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                age=form.cleaned_data['age'],
                city=form.cleaned_data['city']
            )

            login(request, user)  # Автоматический вход
            logger.info(f"Новый пользователь зарегистрирован: {user.username}")
            return redirect('index')
    else:
        form = ExtendedRegisterForm()
        logger.warning(f"Ошибка регистрации: {form.errors.as_json()}")
    return render(request, 'registration/register.html', {'form': form})