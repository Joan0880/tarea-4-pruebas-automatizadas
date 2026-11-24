from __future__ import annotations

import sqlite3

import pytest
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


USERNAME = "demo"
PASSWORD = "Selenium123"


def sign_in(driver, server_url):
    driver.get(server_url + "/login")
    driver.find_element(By.ID, "username").send_keys(USERNAME)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    driver.find_element(By.ID, "login-submit").click()
    assert driver.find_element(By.CSS_SELECTOR, '[data-testid="book-list"]')


def row_for(driver, title):
    def find_matching_row(browser):
        for row in browser.find_elements(By.CSS_SELECTOR, '[data-testid="book-row"]'):
            try:
                if row.find_element(By.CSS_SELECTOR, "[data-testid='row-title']").text == title:
                    return row
            except StaleElementReferenceException:
                continue
        return False

    return WebDriverWait(driver, 5).until(find_matching_row, message=f"No se encontró el libro: {title}")


@pytest.mark.historia
def test_us01_login_camino_feliz(driver, server_url, library):
    """US-01: las credenciales válidas abren la estantería."""
    sign_in(driver, server_url)
    assert "Libros que" in driver.find_element(By.ID, "page-title").text
    assert len(driver.find_elements(By.CSS_SELECTOR, '[data-testid="book-row"]')) == 3


@pytest.mark.historia
def test_us01_cerrar_sesion_protege_estanteria(driver, server_url, library):
    sign_in(driver, server_url)
    driver.find_element(By.CSS_SELECTOR, '[data-testid="logout-button"]').click()
    assert driver.current_url.endswith("/login")
    assert driver.find_element(By.ID, "login-form").is_displayed()
    driver.get(server_url + "/")
    assert driver.current_url.endswith("/login")


@pytest.mark.historia
def test_us01_login_rechaza_contrasena_incorrecta(driver, server_url, library):
    driver.get(server_url + "/login")
    driver.find_element(By.ID, "username").send_keys(USERNAME)
    driver.find_element(By.ID, "password").send_keys("incorrecta")
    driver.find_element(By.ID, "login-submit").click()
    assert "incorrectos" in driver.find_element(By.CSS_SELECTOR, '[data-testid="flash-error"]').text
    assert driver.current_url.endswith("/login")


@pytest.mark.historia
def test_us01_login_limite_campos_vacios(driver, server_url, library):
    driver.get(server_url + "/login")
    driver.execute_script("document.querySelectorAll('#login-form [required]').forEach(e => e.removeAttribute('required'))")
    driver.find_element(By.ID, "login-submit").click()
    assert "Completa el usuario y la contraseña" in driver.find_element(By.CSS_SELECTOR, '[data-testid="flash-error"]').text


@pytest.mark.historia
def test_us02_crear_libro_camino_feliz(driver, server_url, library):
    sign_in(driver, server_url)
    driver.find_element(By.ID, "title").send_keys("El jardín de los senderos que se bifurcan")
    driver.find_element(By.ID, "author").send_keys("Jorge Luis Borges")
    driver.find_element(By.ID, "genre").send_keys("Cuento")
    driver.find_element(By.ID, "year").send_keys("1941")
    driver.find_element(By.ID, "create-book-submit").click()
    assert row_for(driver, "El jardín de los senderos que se bifurcan")
    assert "se agregó" in driver.find_element(By.CSS_SELECTOR, '[data-testid="flash-success"]').text


@pytest.mark.historia
def test_us02_crear_libro_rechaza_titulo_vacio(driver, server_url, library):
    sign_in(driver, server_url)
    driver.find_element(By.ID, "title").click()
    driver.find_element(By.ID, "author").send_keys("Autora de prueba")
    driver.find_element(By.ID, "year").send_keys("2020")
    driver.execute_script("document.querySelectorAll('#create-book-form [required]').forEach(e => e.removeAttribute('required'))")
    driver.find_element(By.ID, "create-book-submit").click()
    assert "título es obligatorio" in driver.find_element(By.CSS_SELECTOR, '[data-testid="flash-error"]').text


@pytest.mark.historia
def test_us02_crear_libro_rechaza_duplicado(driver, server_url, library):
    sign_in(driver, server_url)
    driver.find_element(By.ID, "title").send_keys("Ficciones")
    driver.find_element(By.ID, "author").send_keys("Jorge Luis Borges")
    driver.find_element(By.ID, "year").send_keys("1944")
    driver.find_element(By.ID, "create-book-submit").click()
    assert "Ya existe un libro" in driver.find_element(By.CSS_SELECTOR, '[data-testid="flash-error"]').text
    assert len(driver.find_elements(By.CSS_SELECTOR, '[data-testid="book-row"]')) == 3


@pytest.mark.historia
def test_us02_crear_libro_limite_maximo_admitido(driver, server_url, library):
    sign_in(driver, server_url)
    title = "A" * 120
    driver.find_element(By.ID, "title").send_keys(title)
    driver.find_element(By.ID, "author").send_keys("Autora de prueba")
    driver.find_element(By.ID, "year").send_keys("2100")
    driver.find_element(By.ID, "create-book-submit").click()
    assert row_for(driver, title)


@pytest.mark.historia
def test_us03_busqueda_camino_feliz(driver, server_url, library):
    sign_in(driver, server_url)
    driver.find_element(By.ID, "search-query").send_keys("Borges")
    driver.find_element(By.ID, "search-submit").click()
    WebDriverWait(driver, 5).until(lambda browser: len(browser.find_elements(By.CSS_SELECTOR, '[data-testid="book-row"]')) == 1)
    assert row_for(driver, "Ficciones")


@pytest.mark.historia
def test_us03_busqueda_sin_coincidencias(driver, server_url, library):
    sign_in(driver, server_url)
    driver.find_element(By.ID, "search-query").send_keys("autor que no existe")
    driver.find_element(By.ID, "search-submit").click()
    assert driver.find_element(By.CSS_SELECTOR, '[data-testid="empty-state"]').is_displayed()
    assert "No encontramos coincidencias" in driver.page_source


@pytest.mark.historia
def test_us03_busqueda_limite_cien_caracteres(driver, server_url, library):
    sign_in(driver, server_url)
    query = "x" * 100
    field = driver.find_element(By.ID, "search-query")
    field.send_keys(query)
    assert len(field.get_attribute("value")) == 100
    driver.find_element(By.ID, "search-submit").click()
    assert driver.find_element(By.CSS_SELECTOR, '[data-testid="empty-state"]').is_displayed()


@pytest.mark.historia
def test_us04_editar_libro_camino_feliz(driver, server_url, library):
    sign_in(driver, server_url)
    row = row_for(driver, "Ficciones")
    row.find_element(By.CSS_SELECTOR, "a[data-testid^='edit-book-']").click()
    title = driver.find_element(By.ID, "title")
    title.clear()
    title.send_keys("Ficciones revisadas")
    driver.find_element(By.ID, "save-book").click()
    assert row_for(driver, "Ficciones revisadas")
    assert "se actualizó correctamente" in driver.find_element(By.CSS_SELECTOR, '[data-testid="flash-success"]').text


@pytest.mark.historia
def test_us04_editar_libro_rechaza_titulo_vacio(driver, server_url, library):
    sign_in(driver, server_url)
    row_for(driver, "Ficciones").find_element(By.CSS_SELECTOR, "a[data-testid^='edit-book-']").click()
    title = driver.find_element(By.ID, "title")
    title.clear()
    title.send_keys("   ")
    driver.execute_script("document.querySelectorAll('#edit-book-form [required]').forEach(e => e.removeAttribute('required'))")
    driver.find_element(By.ID, "save-book").click()
    assert "título es obligatorio" in driver.find_element(By.CSS_SELECTOR, '[data-testid="flash-error"]').text
    assert driver.find_element(By.ID, "edit-book-form").is_displayed()


@pytest.mark.historia
def test_us04_editar_libro_limite_inferior_de_anio(driver, server_url, library):
    sign_in(driver, server_url)
    row_for(driver, "Ficciones").find_element(By.CSS_SELECTOR, "a[data-testid^='edit-book-']").click()
    year = driver.find_element(By.ID, "year")
    year.clear()
    year.send_keys("1450")
    driver.find_element(By.ID, "save-book").click()
    assert row_for(driver, "Ficciones")
    assert "1450" in row_for(driver, "Ficciones").text


@pytest.mark.historia
def test_us05_eliminar_libro_camino_feliz(driver, server_url, library):
    sign_in(driver, server_url)
    row = row_for(driver, "Ficciones")
    row.find_element(By.CSS_SELECTOR, "button[data-testid^='delete-book-']").click()
    driver.switch_to.alert.accept()
    WebDriverWait(driver, 5).until(lambda browser: len(browser.find_elements(By.CSS_SELECTOR, '[data-testid="book-row"]')) == 2)


@pytest.mark.historia
def test_us05_eliminar_libro_cancelacion_conserva_registro(driver, server_url, library):
    sign_in(driver, server_url)
    row_for(driver, "Ficciones").find_element(By.CSS_SELECTOR, "button[data-testid^='delete-book-']").click()
    driver.switch_to.alert.dismiss()
    assert row_for(driver, "Ficciones")
    assert len(driver.find_elements(By.CSS_SELECTOR, '[data-testid="book-row"]')) == 3


@pytest.mark.historia
def test_us05_eliminar_ultimo_libro_muestra_estanteria_vacia(driver, server_url, library):
    with sqlite3.connect(library) as db:
        db.execute("DELETE FROM books")
        db.execute("DELETE FROM sqlite_sequence WHERE name = 'books'")
        db.execute(
            "INSERT INTO books (title, author, genre, year) VALUES (?, ?, ?, ?)",
            ("Único ejemplar", "Autora", "Novela", 2024),
        )
    sign_in(driver, server_url)
    row_for(driver, "Único ejemplar").find_element(By.CSS_SELECTOR, "button[data-testid^='delete-book-']").click()
    driver.switch_to.alert.accept()
    assert driver.find_element(By.CSS_SELECTOR, '[data-testid="empty-state"]').is_displayed()
    assert "Tu estantería está lista" in driver.page_source
