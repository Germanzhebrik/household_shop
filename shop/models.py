from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
# Create your models here.

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата изменения")

    class Meta:
        abstract = True # Это значит, что таблица в БД для этой модели создана не будет

class Manufacturer(TimeStampedModel):
    name = models.CharField(max_length=100, verbose_name="Название")
    country = models.CharField(max_length=100, verbose_name="Страна")

    class Meta:
        verbose_name = "Производитель"
        verbose_name_plural = "Производители"

    def __str__(self):
        return self.name

class Category(TimeStampedModel):
    name = models.CharField(max_length=100, verbose_name="Категория")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name

class Product(TimeStampedModel):
    title = models.CharField(max_length=200, verbose_name="Название")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    unit = models.CharField(max_length=20, verbose_name="Ед. измерения")  # литры, кг
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"

    def __str__(self):
        return self.title



class Customer(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_regex = RegexValidator(
        regex=r'^\+375 \(\d{2}\) \d{3}-\d{2}-\d{2}$',
        message="Номер телефона должен быть в формате: '+375 (XX) XXX-XX-XX'."
    )

    phone = models.CharField(
        validators=[phone_regex],
        max_length=20,
        verbose_name="Телефон"
    )
    age = models.PositiveIntegerField(validators=[MinValueValidator(18)])

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиент"

    def __str__(self):
        return self.full_name

class CartItem(TimeStampedModel): # Корзина
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзине"

# 5. Заказ (Связь Многие-ко-Многим через таблицу Заказов)
class Order(TimeStampedModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    order_date = models.DateTimeField(auto_now_add=True)
    delivery_date = models.DateTimeField(null=True, blank=True)
    promo_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="Использованный промокод")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Сумма скидки")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ {self.id} от {self.customer.full_name}"

# Пример OneToOne (например, расширенный профиль сотрудника)
class Employee(TimeStampedModel):
    full_name = models.CharField(max_length=255)
    position = models.CharField(max_length=100)
    age = models.PositiveIntegerField(validators=[MinValueValidator(18)])

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"

#Сервисные модели
class AboutCompany(TimeStampedModel):
    title = models.CharField(max_length=200, default="О компании")
    description = models.TextField(verbose_name="Информация о компании")
    history = models.TextField(verbose_name="История по годам", blank=True)
    requisites = models.TextField(verbose_name="Реквизиты", blank=True)
    logo = models.ImageField(upload_to='about/', blank=True, null=True)
    # видео обычно хранят ссылкой на youtube/vimeo
    video_url = models.URLField(blank=True, verbose_name="Ссылка на видео")

    class Meta:
        verbose_name_plural = "О компании"

class News(TimeStampedModel):
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    short_description = models.CharField(max_length=255, verbose_name="Краткое содержание (1 предложение)")
    content = models.TextField(verbose_name="Полная статья")
    image = models.ImageField(upload_to='news/', verbose_name="Картинка")
    publish_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Новости"

class FAQ(TimeStampedModel):
    question = models.CharField(max_length=255, verbose_name="Вопрос")
    answer = models.TextField(verbose_name="Ответ")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        verbose_name_plural = "Словарь терминов и понятий (FAQ)"

class Contact(TimeStampedModel):
    full_name = models.CharField(max_length=255, verbose_name="ФИО сотрудника")
    photo = models.ImageField(upload_to='staff/', verbose_name="Фото")
    job_description = models.TextField(verbose_name="Описание работ")
    phone_regex = RegexValidator(
        regex=r'^\+375 \(\d{2}\) \d{3}-\d{2}-\d{2}$',
        message="Номер телефона должен быть в формате: '+375 (XX) XXX-XX-XX'."
    )
    phone = models.CharField(
        validators=[phone_regex],
        max_length=20,
        verbose_name="Телефон"
    )
    email = models.EmailField(verbose_name="Почта")

    class Meta:
        verbose_name_plural = "Контакты (Сотрудники)"

class Vacancy(TimeStampedModel):
    title = models.CharField(max_length=200, verbose_name="Название вакансии")
    description = models.TextField(verbose_name="Описание")
    is_active = models.BooleanField(default=True, verbose_name="Открыта")

    class Meta:
        verbose_name_plural = "Вакансии"

class Review(TimeStampedModel):
    name = models.CharField(max_length=100, verbose_name="Имя автора")
    text = models.TextField(verbose_name="Текст отзыва")
    rating = models.PositiveIntegerField(
        verbose_name="Оценка",
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата")

    class Meta:
        verbose_name_plural = "Отзывы"

class PromoCode(TimeStampedModel):
    code = models.CharField(max_length=50, unique=True, verbose_name="Промокод")
    description = models.TextField(verbose_name="Описание акции")
    is_archived = models.BooleanField(default=False, verbose_name="В архиве")

    class Meta:
        verbose_name_plural = "Промокоды и купоны"

# Сигналы для автоматического создания Customer
@receiver(post_save, sender=User)
def create_customer_profile(sender, instance, created, **kwargs):
    if created:
        # Создаем профиль клиента.
        # Если это регистрация через форму, данные будут обновлены позже в view.
        # Если через админку — создастся запись с дефолтными значениями.
        Customer.objects.get_or_create(
            user=instance,
            defaults={
                'full_name': instance.get_full_name() or instance.username,
                'email': instance.email or "",
                'city': "",
                'phone': "",
                'age': 18
            }
        )

@receiver(post_save, sender=User)
def save_customer_profile(sender, instance, **kwargs):
    if hasattr(instance, 'customer'):
        instance.customer.save()


@receiver(post_save, sender=User)
def sync_user_with_customer(sender, instance, created, **kwargs):
    if created:
        # Создаем профиль, если пользователя только что зарегистрировали
        Customer.objects.get_or_create(
            user=instance,
            defaults={
                'full_name': f"{instance.first_name} {instance.last_name}".strip() or instance.username,
                'email': instance.email or "не указан",
                'city': "Не указан",
                'phone': "+375 (00) 000-00-00",
                'age': 18
            }
        )
    else:
        # Если пользователя обновили (например, в админке), синхронизируем данные в Customer
        if hasattr(instance, 'customer'):
            customer = instance.customer
            new_full_name = f"{instance.first_name} {instance.last_name}".strip() or instance.username

            # Обновляем, только если данные действительно изменились, чтобы избежать бесконечного цикла
            if customer.full_name != new_full_name or customer.email != instance.email:
                customer.full_name = new_full_name
                customer.email = instance.email
                customer.save()


@receiver(post_save, sender=Customer)
def sync_customer_with_user(sender, instance, created, **kwargs):
    # Если мы обновили данные в модели Customer, нужно обновить их и в User
    if not created:  # При создании пропускаем, чтобы не конфликтовать с сигналом User
        user = instance.user
        name_parts = instance.full_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        if user.first_name != first_name or user.last_name != last_name or user.email != instance.email:
            user.first_name = first_name
            user.last_name = last_name
            user.email = instance.email
            user.save()