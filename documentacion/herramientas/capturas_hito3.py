"""Capturas del Hito 3: registración, consulta, anulación y comprobante.

Requiere: pip install playwright (usa el Edge instalado, no descarga navegadores).
Uso, con el sistema levantado: python documentacion/herramientas/capturas_hito3.py

Recorre el sistema en http://localhost:8002 con Edge sin ventana y guarda una
captura de página completa por paso en Descargas\\Capturas Hito3.
"""
import pathlib
import re
from datetime import date, timedelta

from playwright.sync_api import sync_playwright

BASE = 'http://localhost:8002'
OUT = pathlib.Path(r'C:\Users\gaboo\Downloads\Capturas Hito3')
OUT.mkdir(parents=True, exist_ok=True)


def foto(page, nombre):
    # sin foco y con los textos desde el principio, para que nada salga cortado
    page.evaluate("document.activeElement && document.activeElement.blur(); "
                  "document.querySelectorAll('input').forEach(i => i.scrollLeft = 0)")
    page.wait_for_timeout(400)
    destino = OUT / f'{nombre}.png'
    page.screenshot(path=str(destino), full_page=True)
    print('ok', destino.name)


def entrar(page, usuario, clave):
    page.goto(f'{BASE}/logout/')
    page.fill('[name=usuario]', usuario)
    page.fill('[name=clave]', clave)
    page.click('button[type=submit]')
    page.wait_for_load_state('networkidle')


def completar_pedido(page, fecha, hora, origen, destino, servicio, objetos, preferida):
    page.goto(f'{BASE}/pedidos/nuevo/')
    page.fill('[name=fecha_servicio]', fecha.isoformat())
    page.dispatch_event('[name=fecha_servicio]', 'change')
    page.fill('[name=hora_servicio]', hora)
    page.fill('[name=origen]', origen)
    page.fill('[name=destino]', destino)
    page.locator('label', has_text=servicio).click()
    for n, (nombre, cantidad, fragil, obs) in enumerate(objetos):
        if n:
            page.click('#agregarFila')
        page.select_option(f'[name="inv-{n}-objeto"]', label=nombre)
        page.fill(f'[name="inv-{n}-cantidad"]', str(cantidad))
        if fragil:
            page.check(f'[name="inv-{n}-fragil"]')
        if obs:
            page.fill(f'[name="inv-{n}-observacion"]', obs)
    page.wait_for_function("document.querySelectorAll('[name=vehiculo] option[value]:not([value=\"\"])').length > 0")
    valores = page.eval_on_selector_all('[name=vehiculo] option', 'os => os.map(o => o.value).filter(Boolean)')
    page.select_option('[name=vehiculo]', preferida if preferida in valores else valores[0])
    page.dispatch_event('[name=hora_servicio]', 'input')


def registrar(page):
    page.click('button:has-text("Registrar pedido")')
    page.wait_for_load_state('networkidle')
    return int(re.search(r'/pedidos/(\d+)/', page.url).group(1))


with sync_playwright() as p:
    nav = p.chromium.launch(channel='msedge', headless=True)
    page = nav.new_page(viewport={'width': 1366, 'height': 900}, device_scale_factor=1.5, locale='es-AR')

    # 1. Ingreso y alta de cliente
    page.goto(f'{BASE}/logout/')
    foto(page, '01-login')
    page.goto(f'{BASE}/registro/')
    foto(page, '02-crear-cuenta')

    # 2. Registración (clienta gomezm)
    entrar(page, 'gomezm', 'Cliente123!')
    hoy = date.today()
    completar_pedido(
        page, hoy + timedelta(days=14), '08:30', 'Av. Belgrano 1250, Salta', 'Los Ceibos 340, Cerrillos',
        'Mudanza local',
        [('Heladera', 1, True, 'Tiene freezer aparte'), ('Cajas', 12, False, ''),
         ('Otro', 1, True, 'Piano vertical: se desarma, va con mantas')],
        'AE-123-CD')
    foto(page, '03-registrar-pedido-formulario')
    pedido_a = registrar(page)
    foto(page, '04-pedido-registrado')

    completar_pedido(
        page, hoy + timedelta(days=16), '02:00', 'Caseros 500, Salta (centro)', 'Av. Bolivia 4000, Salta',
        'Flete urbano', [('Sillón', 1, False, ''), ('Mesa', 1, False, 'Se desarman las patas')], 'AD-321-JK')
    pedido_b = registrar(page)
    page.goto(f'{BASE}/pedidos/')
    foto(page, '05-mis-pedidos-cliente')

    # 3. Consulta y gestión (administrador)
    entrar(page, 'sarmientoc', 'Admin123!')
    page.goto(f'{BASE}/pedidos/')
    foto(page, '06-consulta-todos-los-pedidos')
    page.goto(f'{BASE}/pedidos/?desde={hoy.isoformat()}&estado=Pendiente')
    foto(page, '07-consulta-filtrada-pendientes')
    page.goto(f'{BASE}/pedidos/{pedido_a}/')
    foto(page, '08-detalle-admin-con-acciones')
    page.click('button:has-text("Confirmar")')
    page.wait_for_load_state('networkidle')
    foto(page, '09-pedido-confirmado')

    # 4. Anulación
    page.goto(f'{BASE}/pedidos/{pedido_b}/anular/')
    page.fill('[name=motivo]', 'El cliente reprogramó la mudanza para el mes que viene')
    foto(page, '10-anular-pedido-motivo')
    page.click('button:has-text("Anular pedido")')
    page.wait_for_load_state('networkidle')
    foto(page, '11-pedido-anulado')

    # 5. Comprobantes
    page.goto(f'{BASE}/pedidos/{pedido_a}/comprobante/')
    foto(page, '12-comprobante')
    page.goto(f'{BASE}/pedidos/{pedido_b}/comprobante/')
    foto(page, '13-comprobante-anulado')

    # 6. Tabla maestra y permisos
    page.goto(f'{BASE}/servicios/')
    foto(page, '14-abm-servicios')
    entrar(page, 'gomezm', 'Cliente123!')
    page.goto(f'{BASE}/pedidos/{pedido_a}/')
    foto(page, '15-detalle-cliente-sin-anular')

    nav.close()
    print('pedidos de muestra:', pedido_a, pedido_b)
