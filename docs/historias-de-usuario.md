# Historias de usuario - Biblioteca Aurora

Historias preparadas para importar y organizar en Jira o Azure DevOps. La entrega de esta carpeta aún no crea un tablero remoto; el CSV permite cargar las historias y mantener el texto verificable junto al código.

## US-01 - Inicio de sesión

**Como** persona encargada de mi biblioteca, **quiero** iniciar sesión con mis credenciales, **para** mantener mi colección protegida.

**Criterios de aceptación**

- Con usuario `demo` y contraseña `Selenium123`, se abre la estantería.
- La página muestra la colección y permite cerrar la sesión.
- Al cerrar sesión, la siguiente visita a la estantería pide autenticación.

**Criterios de rechazo**

- Usuario o contraseña incorrectos no crean una sesión y muestran un mensaje entendible.
- Usuario o contraseña vacíos no crean una sesión.
- Una persona sin sesión no puede consultar rutas privadas.

**Escenarios Selenium:** `test_us01_login_*` (camino feliz, rechazo de contraseña y campos vacíos).

## US-02 - Agregar libros

**Como** persona lectora, **quiero** registrar título, autor, género y año, **para** conservar mi catálogo en un solo lugar.

**Criterios de aceptación**

- Título, autor y año se guardan y aparecen en la estantería.
- Género es opcional.
- El título admite hasta 120 caracteres, el autor 80 y el género 40.
- Se aceptan años entre 1450 y 2100, inclusive.

**Criterios de rechazo**

- Título o autor vacío no se guarda y muestra el motivo.
- No se aceptan años fuera del rango ni texto que no represente un año.
- No se permite repetir la misma pareja de título y autor, ignorando mayúsculas.

**Escenarios Selenium:** `test_us02_crear_libro_*` (alta, título vacío, duplicado y límite de longitud/año).

## US-03 - Consultar y buscar

**Como** persona lectora, **quiero** ver y filtrar mi colección, **para** encontrar un libro por título, autor o género.

**Criterios de aceptación**

- La estantería muestra los libros guardados.
- La búsqueda encuentra coincidencias parciales en título, autor y género.
- Limpiar la búsqueda vuelve a mostrar toda la colección.

**Criterios de rechazo**

- Una consulta sin coincidencias muestra un estado vacío claro.
- La consulta está limitada a 100 caracteres.
- La búsqueda no altera ni elimina registros.

**Escenarios Selenium:** `test_us03_busqueda_*` (coincidencia, sin resultados y longitud máxima).

## US-04 - Actualizar libro

**Como** persona lectora, **quiero** corregir los datos de un libro, **para** que mi catálogo se mantenga preciso.

**Criterios de aceptación**

- La acción Editar abre los valores guardados.
- Guardar cambios actualiza el registro existente y confirma el resultado.
- Se admiten años de 1450 a 2100, inclusive.

**Criterios de rechazo**

- Título o autor vacío no sobrescriben los datos y muestran el motivo.
- Datos fuera de los límites permitidos no se guardan.
- Un duplicado de título y autor no se convierte en otro registro.

**Escenarios Selenium:** `test_us04_editar_libro_*` (edición, título vacío y año mínimo).

## US-05 - Eliminar libro

**Como** persona lectora, **quiero** quitar libros de mi colección, **para** mantener una estantería actualizada.

**Criterios de aceptación**

- Eliminar un libro pide confirmación.
- Al confirmar, el libro desaparece y se informa el resultado.
- Eliminar el último registro muestra el estado vacío.

**Criterios de rechazo**

- Cancelar la confirmación conserva el registro.
- Un identificador inexistente informa que el libro ya no está disponible.

**Escenarios Selenium:** `test_us05_*` (eliminación, cancelación y último registro).

## Importación

`historias-jira.csv` contiene los cinco issues en columnas compatibles con la importación CSV de Jira: tipo, resumen, descripción y etiquetas. Los criterios de aceptación y rechazo están incluidos en cada descripción para no depender de campos personalizados.
