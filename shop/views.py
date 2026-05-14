import logging
import requests
import matplotlib.pyplot as plt
import io
import base64
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
from statistics import mode, StatisticsError

from .models import (
    Product, Customer, Order, News, AboutCompany,
    FAQ, Contact, Vacancy, Review, PromoCode, Category, CartItem
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
    # 1. Показатели по сумме продаж
    orders = Order.objects.annotate(total_item_price=F('product__price') * F('quantity'))
    prices = list(orders.values_list('total_item_price', flat=True))

    avg_sales = sum(prices) / len(prices) if prices else 0
    median_sales = sorted(prices)[len(prices) // 2] if prices else 0
    try:
        mode_sales = mode(prices)
    except StatisticsError:
        mode_sales = "Н/Д"

    # 2. Показатели по возрасту клиентов
    ages = list(Customer.objects.values_list('age', flat=True))
    avg_age = sum(ages) / len(ages) if ages else 0
    median_age = sorted(ages)[len(ages) // 2] if ages else 0

    # 3. Самый популярный тип товара (по количеству проданных единиц)
    popular_cat = Category.objects.annotate(sold_count=Sum('products__order__quantity')) \
        .order_by('-sold_count').first()

    # 4. Самый прибыльный тип товара (по сумме выручки)
    profitable_cat = Category.objects.annotate(revenue=Sum(F('products__order__quantity') * F('products__price'))) \
        .order_by('-revenue').first()

    context = {
        'avg_sales': avg_sales,
        'median_sales': median_sales,
        'mode_sales': mode_sales,
        'avg_age': avg_age,
        'median_age': median_age,
        'popular_category': popular_cat,
        'profitable_category': profitable_cat,
    }
    return render(request, 'shop/statistics.html', context)

@user_passes_test(is_employee)
def charts_view(request):
    # График распределения по категориям
    category_data = Category.objects.annotate(total_products=Count('products'))
    labels = [c.name for c in category_data]
    values = [c.total_products for c in category_data]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
    ax.set_title("Распределение товаров по категориям")

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    pie_chart = base64.b64encode(buf.getvalue()).decode('utf-8')

    # Линейный график заказов
    order_stats = Order.objects.values('created_at__date').annotate(count=Count('id')).order_by('created_at__date')
    dates = [str(item['created_at__date']) for item in order_stats]
    counts = [item['count'] for item in order_stats]

    fig2, ax2 = plt.subplots(figsize=(8, 4))
    ax2.plot(dates, counts, marker='o', color='g')
    ax2.set_title("Динамика заказов")
    plt.xticks(rotation=45)
    plt.tight_layout()

    buf2 = io.BytesIO()
    plt.savefig(buf2, format='png')
    plt.close(fig2)
    line_chart = base64.b64encode(buf2.getvalue()).decode('utf-8')

    return render(request, 'shop/charts.html', {
        'pie_chart': pie_chart,
        'line_chart': line_chart
    })


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
            # 1. Сохраняем пользователя.
            # Сигнал post_save автоматически создаст Customer с дефолтными полями.
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # 2. Теперь просто обновляем Customer данными из формы.
            # Благодаря сигналам, email и имя в User обновятся сами,
            # если вы измените их в customer.
            customer = user.customer
            customer.full_name = f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}"
            customer.email = form.cleaned_data['email']
            customer.phone = form.cleaned_data['phone']
            customer.age = form.cleaned_data['age']
            customer.city = form.cleaned_data['city']
            customer.save()

            login(request, user)
            return redirect('index')
    else:
        form = ExtendedRegisterForm()
    return render(request, 'shop/register.html', {'form': form})


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    customer = request.user.customer

    # Получаем количество из POST-запроса.
    # Если это не POST (например, прямой переход по ссылке), ставим 1.
    if request.method == 'POST':
        qty = int(request.POST.get('quantity', 1))
    else:
        qty = 1

    cart_item, created = CartItem.objects.get_or_create(customer=customer, product=product)

    if not created:
        cart_item.quantity += qty  # Прибавляем выбранное количество
    else:
        cart_item.quantity = qty  # Устанавливаем выбранное количество

    cart_item.save()
    messages.success(request, f"Товар {product.title} (x{qty}) добавлен в корзину.")
    return redirect('product_list')


@login_required
def view_cart(request):
    customer = request.user.customer
    cart_items = customer.cart_items.all()
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'shop/cart.html', {'cart_items': cart_items, 'total_price': total_price})


@login_required
def checkout(request):
    customer = request.user.customer
    cart_items = customer.cart_items.all()

    if not cart_items:
        return redirect('product_list')

    if request.method == 'POST':
        promo_text = request.POST.get('promo_code', '').strip()
        promo_obj = None

        # Проверка: существует ли такой код в базе и не в архиве ли он
        if promo_text:
            promo_obj = PromoCode.objects.filter(code=promo_text, is_archived=False).first()

            if promo_text and not promo_obj:
                messages.error(request, f"Промокод '{promo_text}' не найден или недействителен.")
                # Можно прервать оформление или просто проигнорировать код
                # Если хотим дать пользователю шанс исправить — возвращаем на страницу корзины
                return redirect('view_cart')
            elif promo_obj:
                messages.success(request, f"Промокод '{promo_obj.code}' успешно применен!")

        # Создаем заказы
        for item in cart_items:
            Order.objects.create(
                customer=customer,
                product=item.product,
                quantity=item.quantity,
                # Сохраняем текст промокода только если он прошел проверку
                promo_code=promo_obj.code if promo_obj else None,
                delivery_date=timezone.now() + timezone.timedelta(days=3)
            )

        # Очищаем корзину после успешного оформления
        cart_items.delete()
        messages.success(request, "Заказ успешно оформлен!")
        return redirect('product_list')

    return render(request, 'shop/cart.html', {'cart_items': cart_items})

@login_required
def remove_from_cart(request, item_id):
    # Удаляем конкретный товар из корзины текущего пользователя
    cart_item = get_object_or_404(CartItem, id=item_id, customer=request.user.customer)
    product_title = cart_item.product.title
    cart_item.delete()
    messages.success(request, f"Товар {product_title} удален из корзины.")
    return redirect('view_cart')

@login_required
def clear_cart(request):
    # Удаляем все товары из корзины текущего пользователя
    request.user.customer.cart_items.all().delete()
    messages.success(request, "Корзина полностью очищена.")
    return redirect('view_cart')