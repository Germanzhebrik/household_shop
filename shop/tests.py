from django.test import TestCase
from .models import Product, Category, Customer
from django.contrib.auth.models import User
from django.urls import reverse

class ProductModelTest(TestCase):
    def setUp(self):
        # Создаем данные для теста
        self.category = Category.objects.create(name="Чистящие средства")
        self.product = Product.objects.create(
            title="Мыло",
            price=10.50,
            unit="шт",
            category=self.category
        )

    def test_product_str(self):
        """Проверяем, что __str__ возвращает название товара"""
        self.assertEqual(str(self.product), "Мыло")

    def test_product_price_value(self):
        """Проверяем корректность цены"""
        self.assertEqual(self.product.price, 10.50)

class ProductViewTest(TestCase):
    def setUp(self):
        cat = Category.objects.create(name="Кухня")
        Product.objects.create(title="Средство для плит", price=5, category=cat, unit="шт")
        Product.objects.create(title="Стиральный порошок", price=20, category=cat, unit="кг")

    def test_product_list_status_code(self):
        """Проверяем, что страница товаров доступна"""
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)

    def test_search_functionality(self):
        """Проверяем, что поиск находит нужный товар"""
        # Ищем 'порошок'
        response = self.client.get(reverse('product_list'), {'q': 'порошок'})
        self.assertContains(response, "Стиральный порошок")
        self.assertNotContains(response, "Средство для плит")


class RegistrationTest(TestCase):
    def test_successful_registration(self):
        """Проверка создания User и Customer при заполнении формы"""

        # 1. Подготавливаем данные, которые имитируют ввод пользователя в форму
        # Убедитесь, что имена полей совпадают с теми, что в вашей ExtendedRegisterForm
        form_data = {
            'username': 'ivan_test',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'ivan@example.com',
            'phone': '+375 (29) 123-45-67',  # Соответствует вашему RegexValidator
            'age': 25,
            'city': 'Минск',
            'password': 'SuperPassword123!',
            'password_confirm': 'SuperPassword123!',
        }

        # 2. Отправляем POST-запрос на URL регистрации
        # reverse('register') берет имя из вашего urls.py
        response = self.client.post(reverse('register'), data=form_data)

        # 3. ПРОВЕРКИ

        # Проверяем, что после регистрации произошел редирект (обычно на главную страницу)
        # Код 302 означает "Перенаправление"
        self.assertEqual(response.status_code, 302)

        # Проверяем, создался ли объект системного пользователя User
        self.assertTrue(User.objects.filter(username='ivan_test').exists())
        user = User.objects.get(username='ivan_test')

        # Проверяем, создалась ли запись в вашей модели Customer и привязана ли она к User
        self.assertTrue(Customer.objects.filter(user=user).exists())
        customer = Customer.objects.get(user=user)

        # Проверяем, корректно ли объединились имя и фамилия в full_name (как в вашем views.py)
        self.assertEqual(customer.full_name, "Иван Иванов")

        # Проверяем, что город и возраст сохранились правильно
        self.assertEqual(customer.city, "Минск")
        self.assertEqual(customer.age, 25)

    def test_registration_invalid_age(self):
        """Проверка, что клиент младше 18 лет не сможет зарегистрироваться"""
        form_data = {
            'username': 'young_user',
            'first_name': 'Петр',
            'last_name': 'Петров',
            'email': 'peter@example.com',
            'phone': '+375 (29) 000-00-00',
            'age': 16,  # Меньше 18
            'password': 'Password123!',
        }

        response = self.client.post(reverse('register'), data=form_data)

        # Проверяем, что запись НЕ создалась
        self.assertFalse(User.objects.filter(username='young_user').exists())
        # Обычно при ошибке форма возвращается с кодом 200 (а не 302)
        self.assertEqual(response.status_code, 200)