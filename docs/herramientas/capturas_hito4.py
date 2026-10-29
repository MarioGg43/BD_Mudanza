"""Capturas del Hito 4: el proceso completo del pedido (registración, consulta, anulación y comprobante),
más la auditoría y los permisos.

Requiere: pip install playwright (usa el Edge instalado, no descarga navegadores).
Uso, con el sistema levantado: python docs/herramientas/capturas_hito4.py

Recorre el sistema en http://localhost:8002 con Edge sin ventana y guarda una captura de página
completa por paso (y el comprobante en PDF) en Descargas\\Hito4_Mudanzas_Grupo5\\Capturas.
Registra dos pedidos de muestra: uno queda confirmado y reprogramado y el otro anulado.
"""
import pathlib
import re
from datetime import date, timedelta

from playwright.sync_api import sync_playwright

BASE = 'http://localhost:8002'
OUT = pathlib.Path(r'C:\Users\gaboo\Downloads\Hito4_Mudanzas_Grupo5\Capturas')
OUT.mkdir(parents=True, exist_ok=True)


def foto(page, nombre, completa=True):
    # sin foco y con los textos desde el principio, para que nada salga cortado
    page.evaluate("document.activeElement && document.activeElement.blur(); "
                  "document.querySelectorAll('input').forEach(i => i.scrollLeft = 0)")
    page.wait_for_timeout(500)
    destino = OUT / f'{nombre}.png'
    page.screenshot(path=str(destino), full_page=completa)
    print('ok', destino.name)


def entrar(page, usuario, clave):
    page.goto(f'{BASE}/logout/')
    page.fill('[name=usuario]', usuario)
    page.fill('[name=clave]', clave)
    page.click('button[type=submit]')
    page.wait_for_load_state('networkidle')


def abrir_ventana(page):
    page.click('#agregarObjeto')
    page.wait_for_selector('#modalObjeto.show')
    page.wait_for_timeout(300)


def agregar_objeto(page, busqueda, cantidad=1, fragil=False, otro=None):
    """Usa la ventana «Agregar objeto» como una persona: busca, o elige «Otro» y dice qué es."""
    abrir_ventana(page)
    page.fill('#buscarObjeto', busqueda)
    if otro:
        page.click('#sugerencias button:has-text("Otro")')
        page.fill('#queEsOtro', otro)
    page.fill('#cantObjeto', str(cantidad))
    page.dispatch_event('#cantObjeto', 'input')
    if fragil:
        page.check('#fragilObjeto')
    page.wait_for_selector('#guardarObjeto:not([disabled])')
    page.click('#guardarObjeto')
    page.wait_for_selector('#modalObjeto', state='hidden')


def datos_del_pedido(page, fecha, hora, origen, destino, servicio, adicionales=()):
    page.goto(f'{BASE}/pedidos/nuevo/')
    page.fill('[name=fecha_servicio]', fecha.isoformat())
    page.dispatch_event('[name=fecha_servicio]', 'change')
    page.fill('[name=hora_servicio]', hora)
    page.dispatch_event('[name=hora_servicio]', 'change')
    page.fill('[name=origen]', origen)
    page.fill('[name=destino]', destino)
    page.locator('label', has_text=servicio).first.click()
    for a in adicionales:
        page.locator('label', has_text=a).first.click()


def elegir_vehiculo(page, patente):
    page.wait_for_function(f"[...document.querySelectorAll('[name=vehiculo] option')].some(o => o.value === '{patente}')")
    page.select_option('[name=vehiculo]', patente)
    page.dispatch_event('[name=vehiculo]', 'change')


def registrar(page):
    page.click('button:has-text("Registrar pedido")')
    page.wait_for_load_state('networkidle')
    return int(re.search(r'/pedidos/(\d+)/', page.url).group(1))


with sync_playwright() as p:
    nav = p.chromium.launch(channel='msedge', headless=True)
    page = nav.new_page(viewport={'width': 1366, 'height': 900}, device_scale_factor=1.5, locale='es-AR')
    hoy = date.today()

    # 1. Portada, ingreso y alta de cliente
    page.goto(f'{BASE}/logout/')
    page.goto(f'{BASE}/')
    foto(page, '01-portada-servicios-y-precios')
    page.goto(f'{BASE}/login/')
    foto(page, '02-login')
    page.goto(f'{BASE}/registro/')
    foto(page, '03-crear-cuenta')

    # 2. Registración (clienta gomezm): datos, servicio con adicional y objetos con la ventana guiada
    entrar(page, 'gomezm', 'Cliente123!')
    datos_del_pedido(page, hoy + timedelta(days=20), '08:30', 'Av. Belgrano 1250, Salta', 'Los Ceibos 340, Cerrillos',
                     'Mudanza local', ['Embalaje'])
    agregar_objeto(page, 'heladera', 1, fragil=True)
    abrir_ventana(page)
    page.fill('#buscarObjeto', 'silla')
    page.fill('#cantObjeto', '6')
    page.dispatch_event('#cantObjeto', 'input')
    foto(page, '04-ventana-objeto-ya-en-la-lista', completa=False)
    page.click('#guardarObjeto')
    page.wait_for_selector('#modalObjeto', state='hidden')
    abrir_ventana(page)
    page.fill('#buscarObjeto', 'sillas')
    foto(page, '05-ventana-objeto-repetido', completa=False)
    page.click('#modalObjeto button:has-text("Cancelar")')
    page.wait_for_selector('#modalObjeto', state='hidden')
    abrir_ventana(page)
    page.fill('#buscarObjeto', 'piano')
    page.click('#sugerencias button:has-text("Otro")')
    page.fill('#queEsOtro', 'Piano vertical')
    page.check('#fragilObjeto')
    page.wait_for_selector('#guardarObjeto:not([disabled])')
    foto(page, '06-ventana-otro-que-es', completa=False)
    page.click('#guardarObjeto')
    page.wait_for_selector('#modalObjeto', state='hidden')
    agregar_objeto(page, 'cajas', 15)
    elegir_vehiculo(page, 'AE-123-CD')  # camión grande: +50 % sobre el servicio principal
    foto(page, '07-registrar-pedido-formulario-completo')
    pedido_a = registrar(page)
    foto(page, '08-pedido-registrado')

    datos_del_pedido(page, hoy + timedelta(days=21), '02:00', 'Caseros 500, Salta (centro)', 'Av. Bolivia 4000, Salta',
                     'Flete urbano')
    agregar_objeto(page, 'sillón', 1)
    agregar_objeto(page, 'mesa', 1)
    elegir_vehiculo(page, 'AD-321-JK')
    pedido_b = registrar(page)
    page.goto(f'{BASE}/pedidos/')
    foto(page, '09-mis-pedidos-cliente')

    # 3. Consulta y gestión (administrador)
    entrar(page, 'sarmientoc', 'Admin123!')
    page.goto(f'{BASE}/pedidos/')
    foto(page, '10-consulta-todos-los-pedidos-con-avisos')
    cliente = page.eval_on_selector('[name=cliente]', "s => [...s.options].find(o => o.text.includes('Gómez')).value")
    page.goto(f'{BASE}/pedidos/?desde={hoy.isoformat()}&hasta={(hoy + timedelta(days=30)).isoformat()}'
              f'&estado=Pendiente&cliente={cliente}')
    foto(page, '11-consulta-filtrada-fechas-estado-cliente')
    page.goto(f'{BASE}/pedidos/{pedido_a}/')
    foto(page, '12-detalle-admin-con-acciones')
    page.goto(f'{BASE}/pedidos/{pedido_a}/asignar/')
    page.select_option('[name=chofer]', label='Fernandez, Luciana')
    page.locator('label', has_text='Romero, Lucas').first.click()
    foto(page, '13-asignar-chofer-y-ayudante')
    page.click('button:has-text("Guardar")')
    page.wait_for_load_state('networkidle')
    page.click('button:has-text("Confirmar")')
    page.wait_for_load_state('networkidle')
    foto(page, '14-pedido-confirmado')

    # 4. Reprogramar (cambio de horario con motivo, historial y aviso por WhatsApp)
    page.goto(f'{BASE}/pedidos/{pedido_a}/reprogramar/')
    page.fill('[name=hora_servicio]', '10:00')
    page.select_option('[name=motivo]', 'Clima')
    page.fill('[name=observacion]', 'Pronóstico de lluvia fuerte a la mañana')
    foto(page, '15-reprogramar-formulario')
    page.click('button:has-text("Reprogramar")')
    page.wait_for_load_state('networkidle')
    foto(page, '16-reprogramado-historial-y-whatsapp')

    # 5. Anulación
    page.goto(f'{BASE}/pedidos/{pedido_b}/anular/')
    page.fill('[name=motivo]', 'El cliente consiguió quien le haga el flete')
    foto(page, '17-anular-pedido-motivo')
    page.click('button:has-text("Anular pedido")')
    page.wait_for_load_state('networkidle')
    foto(page, '18-pedido-anulado')

    # 6. Comprobantes (pantalla, anulado y PDF)
    page.goto(f'{BASE}/pedidos/{pedido_a}/comprobante/')
    foto(page, '19-comprobante')
    page.goto(f'{BASE}/pedidos/{pedido_b}/comprobante/')
    foto(page, '20-comprobante-anulado')
    pdf = page.request.get(f'{BASE}/pedidos/{pedido_a}/comprobante/pdf/')
    (OUT / f'21-comprobante-pedido-{pedido_a}.pdf').write_bytes(pdf.body())
    print('ok', f'21-comprobante-pedido-{pedido_a}.pdf')

    # 7. Log de auditoría
    page.goto(f'{BASE}/auditoria/?tabla=PEDIDOS')
    foto(page, '22-auditoria-pedidos')
    page.goto(f'{BASE}/auditoria/?accion=Anulación')
    foto(page, '23-auditoria-anulaciones')

    # 8. Tablas maestras
    page.goto(f'{BASE}/servicios/')
    foto(page, '24-abm-servicios')
    page.goto(f'{BASE}/objetos/')
    foto(page, '25-abm-objetos')
    page.goto(f'{BASE}/vehiculos/')
    foto(page, '26-abm-vehiculos')

    # 9. Permisos: el cliente ve su pedido sin acciones de gestión y no puede anular
    entrar(page, 'gomezm', 'Cliente123!')
    page.goto(f'{BASE}/pedidos/{pedido_a}/')
    foto(page, '27-detalle-cliente-sin-anular-y-aviso-de-cambio')
    page.goto(f'{BASE}/pedidos/{pedido_a}/anular/')
    foto(page, '28-cliente-sin-permiso-para-anular')

    nav.close()
    print('pedidos de muestra:', pedido_a, pedido_b)
