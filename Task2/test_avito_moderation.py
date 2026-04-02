import pytest
import re
from playwright.sync_api import Page, expect

BASE_URL = "https://cerulean-praline-8e5aa6.netlify.app/"

@pytest.fixture(autouse=True)
def setup(page: Page):
    page.goto(BASE_URL)
    # Ожидаем загрузки контента
    page.wait_for_selector("h3", timeout=10000)

def test_price_filter_valid(page: Page):
    """TC-UI-001: Проверка работы фильтра «Диапазон цен» на валидных значениях."""
    min_price = "50000"
    max_price = "60000"
    
    page.get_by_placeholder("От").fill(min_price)
    page.get_by_placeholder("До").fill(max_price)
    page.keyboard.press("Enter")
    
    # Даем время на фильтрацию
    page.wait_for_timeout(2000)
    
    # Проверка сохранения значений в полях (Баг P2 в отчете)
    try:
        expect(page.get_by_placeholder("От")).to_have_value(min_price)
        expect(page.get_by_placeholder("До")).to_have_value(max_price)
    except AssertionError:
        pytest.fail("BUG P2: Значения в полях фильтра цен сбросились после применения")
    
    # Проверка цен в выдаче
    prices = page.locator("p:has-text('₽')").all_inner_texts()
    for price_text in prices:
        # Извлекаем число из строки типа "53 195 ₽"
        price = int(re.sub(r"\D", "", price_text))
        assert int(min_price) <= price <= int(max_price), f"Цена {price} вне диапазона {min_price}-{max_price}"

def test_price_filter_invalid(page: Page):
    """TC-UI-002: Проверка работы фильтра «Диапазон цен» на невалидных значениях."""
    page.get_by_placeholder("От").fill("-1000")
    
    # Проверка, что поле не принимает отрицательные значения
    value = page.get_by_placeholder("От").input_value()
    if "-" in value:
        pytest.fail("BUG P3: Поле 'От' приняло отрицательное значение")

def test_sort_by_price(page: Page):
    """TC-UI-003: Проверка сортировки «По цене»."""
    # Выбираем сортировку по цене
    page.locator("select").nth(0).select_option("Цене")
    # Выбираем порядок по убыванию
    page.locator("select").nth(1).select_option("По убыванию")
    
    page.wait_for_timeout(2000)
    
    prices_text = page.locator("p:has-text('₽')").all_inner_texts()
    prices = [int(re.sub(r"\D", "", p)) for p in prices_text]
    
    # Проверка сортировки (Баг P1 в отчете)
    if prices != sorted(prices, reverse=True):
        pytest.fail("BUG P1: Список не отсортирован по убыванию цены")

def test_category_filter(page: Page):
    """TC-UI-004: Проверка работы фильтра «Категория»."""
    category = "Электроника"
    # Находим селект категорий (он обычно 3-й по счету в фильтрах)
    page.locator("select").nth(2).select_option(category)
    
    page.wait_for_timeout(2000)
    
    # Проверяем категории в карточках (Баг P1 в отчете)
    card_categories = page.locator(".bg-white .text-blue-600").all_inner_texts()
    for cat in card_categories:
        if cat != category:
            pytest.fail(f"BUG P1: Найдено объявление категории {cat}, ожидалось {category}")

def test_urgent_toggle(page: Page):
    """TC-UI-005: Проверка работы тогла «Только срочные»."""
    # Кликаем по тоглу (используем текст рядом с инпутом)
    page.get_by_text("🔥 Только срочные").click()
    page.wait_for_timeout(2000)
    
    # Проверяем наличие бейджа "Срочно" во всех карточках
    cards = page.locator("div.border.rounded-lg").all()
    for card in cards:
        expect(card.get_by_text("Срочно")).to_be_visible()

def test_stats_timer_controls(page: Page):
    """TC-UI-006: Проверка контейнера управления таймером обновления статистики."""
    page.get_by_role("link", name="📊 Статистика").click()
    page.wait_for_url("**/stats")
    
    # Проверка кнопки Обновить
    update_btn = page.locator("button:has-text('Обновить')")
    expect(update_btn).to_be_enabled()
    
    # Проверка паузы таймера
    # Находим кнопку по иконке или тексту
    pause_btn = page.locator("button:has-text('⏸')")
    pause_btn.click()
    
    # После клика кнопка должна смениться на Play
    play_btn = page.locator("button:has-text('▶️')")
    expect(play_btn).to_be_visible()
    
    # Проверка текста "Автообновление выключено"
    expect(page.get_by_text("Автообновление выключено")).to_be_visible()
