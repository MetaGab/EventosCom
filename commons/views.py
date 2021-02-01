from django.shortcuts import render
from django.db import connection
from django.http import HttpResponseRedirect
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import validate_email
from django.template.context_processors import csrf
from django.apps import apps
from django.forms import modelform_factory, SelectDateWidget
from .models import * 
from .forms import * 
from datetime import datetime
def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]
# Create your views here.
def index(request):
    eventos = Evento.objects.raw("SELECT * FROM EVENTOS_DISPONIBLES")
    categorias = Categoria.objects.raw("SELECT * FROM EVENTOS.CATEGORIA WHERE activo=1 AND categoria_padre IS NULL")
    user = request.session.get('user_id', 0)
    if Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE id= %s", [user]):
        user = Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE id= %s", [user])[0]
    return render(request, 'index.html', locals())

def login(request):
    c = {}
    c.update(csrf(request))
    error = {}

    if request.POST:
        try:
            validate_email(request.POST["email"])
        except:
            error["email"] = "Error en formato de email"

        user = None
        if Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE correo=%s", [request.POST["email"]]):
            user = Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE correo=%s", [request.POST["email"]])[0]
            auth = check_password(request.POST["password"], user.contraseña)
            if not auth:
                error["general"] = "Correo o contraseña incorrecto"
        else:
            error["general"] = "Correo o contraseña incorrecto"

        if not error:
            request.session["user_id"] = user.id
            if user.es_admin:
                return HttpResponseRedirect('/crud')
            else:
                return HttpResponseRedirect('/')

    return render(request, 'iniciar-sesion.html', locals())

def signup(request):
    c = {}
    c.update(csrf(request))
    error = {}
    new_user = {}

    if request.POST:
        for field in request.POST:
            new_user[field] = request.POST[field] 
            if field == "":
                error[field] = "Debe ser llenado"
        try:
            validate_email(new_user["email"])
            if Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE correo=%s", [request.POST["email"]]):
                error["email"] = "Correo ya fue utilizado en otra cuenta"
        except:
            error["email"] = "Error en formato de email"

        if new_user["pass"] != new_user["re_pass"]:
            error["re_pass"] = "Repite la contraseña sin cambios"

        if not error:
            new_user["hash_pass"] = make_password(new_user["pass"])
            inserted_user = (new_user["name"], new_user["lname1"], new_user["lname2"], new_user["email"], new_user["hash_pass"])
            with connection.cursor() as cursor:
                cursor.execute("EXECUTE AS USER = 'CLIENTE'")
                cursor.execute("EXEC CREAR_USUARIO %s, %s, %s, %s,  %s", inserted_user)
                cursor.execute("REVERT")
            request.session["user_id"] = Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE contraseña=%s", [new_user["hash_pass"]])[0].id
            return HttpResponseRedirect('/')

    return render(request, 'registro.html', locals())

def logout(request):
    if "user_id" in request.session:
        del request.session["user_id"]
    return HttpResponseRedirect('/')

def crud(request, model=None, id=None):
    modelos = ["Artista", "Categoria", "Lugar", "TipoBoleto", "Zona", "Evento", "Funcion", "Boleto"]
    reportes = [
        {'name':"Evento Mayor Ganancia", 'link': "EventoMayorGanancia"}, 
        {'name':"Evento Menor Ganancia", 'link': "EventoMenorGanancia"}, 
        {'name':'Eventos Mayor al Promedio','link':'EventosMayoralPromedio'},
        {'name':"Ganancias por evento", 'link':'Gananciasporevento'},
        {'name':"Ganancias por mes", 'link':'Gananciaspormes'},
        {'name':"Ganancias por artista", 'link':'Gananciasporartista'},
        {'name':"Ganancias por lugar", 'link': "Gananciasporlugar"}]
    user = request.session.get('user_id', False)
    modo = None
    if Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE id= %s", [user]):
        user = Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE id= %s", [user])[0]
        if not user.es_admin:
            return HttpResponseRedirect('/')
        elif user.nombre == "EVENTOS":
            modelos = ["Artista", "Categoria", "Lugar", "Zona", "Evento", "Funcion"]
            modo = "eventos_user"
        elif user.nombre == "VENTAS":
            modelos = ["TipoBoleto", "Boleto"]
            modo = "ventas_user"
        elif user.nombre == "AUTH":
            modelos = ["Usuario"]
    else:
        return HttpResponseRedirect('/')

    if model is None or model not in modelos:
        if user.nombre == "VENTAS":
            return HttpResponseRedirect('/crud/TipoBoleto')
        elif user.nombre == "AUTH":
            return HttpResponseRedirect('/crud/Usuario')
        else:
            return HttpResponseRedirect('/crud/Artista')
    c = {}
    c.update(csrf(request))

    modelo = apps.get_model("commons", model)
    instance = None
    if id and modelo.objects.raw("SELECT * FROM ["+modelo._meta.db_table+"] WHERE id=%s", [id]):
        instance = modelo.objects.raw("SELECT * FROM ["+modelo._meta.db_table+"] WHERE id=%s", [id])[0]  
        
    items = {}
    fields = modelo._meta.get_fields()
    for item in modelo.objects.raw("SELECT * FROM ["+modelo._meta.db_table+"] WHERE activo=1"):
        items[item.id] = {}
        if model == 'Usuario':
            items[item.id]['id'] = item.id
            items[item.id]['correo'] = item.correo
            items[item.id]['es_admin'] = item.es_admin 
        else:
            for f in fields:
                if hasattr(item, f.name):
                    items[item.id][f.name] = getattr(item, f.name)

    columns = []
    try:
        first = next(iter(items))
        for f in items[first]:
            columns.append(f)
    except:
        pass
    
    FormClass = modelform_factory(modelo, exclude=('id','activo',))
    if model == "Evento":
        FormClass = modelform_factory(modelo, exclude=('id','activo',), widgets={"fecha_inicio": SelectDateWidget(), "fecha_fin":SelectDateWidget()})
    elif model == "Funcion":
        FormClass = FuncionForm
    elif model == "Boleto":
        FormClass = modelform_factory(modelo, exclude=('id','activo','asiento','fila','nombre'))
    elif model == "Usuario":
        FormClass = modelform_factory(modelo, fields=('es_admin',))

    if request.POST:
        if "del" in request.POST:
            if id:
                with connection.cursor() as cursor:
                    if modo:
                        cursor.execute("EXECUTE AS USER = %s", [modo] )
                    cursor.execute("EXECUTE DESACTIVAR %s, %s", [id,"["+modelo._meta.db_table+"]"])
                    cursor.execute("REVERT")
                return HttpResponseRedirect('/crud/%s/#' % (model))
            else:
                for id in request.POST.getlist('options'):
                    with connection.cursor() as cursor:
                        if modo:
                            cursor.execute("EXECUTE AS USER = %s", [modo] )
                        cursor.execute("EXECUTE DESACTIVAR %s, %s", [id,"["+modelo._meta.db_table+"]"])
                        cursor.execute("REVERT")
                return HttpResponseRedirect('/crud/%s/#' % (model))
        
        form = FormClass(request.POST, request.FILES, instance=instance)

        if form.is_valid():
            if model != "Boleto":
                forma=form.save(commit=False)
                if forma.id is None:
                    if 'imagen' in request.FILES:
                        with open(forma.imagen.path, 'wb+') as destination:
                            for chunk in request.FILES['imagen'].chunks():
                                destination.write(chunk)
                    with connection.cursor() as cursor:
                        if modo:
                            cursor.execute("EXECUTE AS USER = %s", [modo])
                        if model == "Artista":
                            cursor.execute("EXEC CREAR_ARTISTA %s, %s, %s, %s, %s", [forma.nombre, forma.apellido_p, forma.apellido_m, forma.descripcion, forma.categoria.id if forma.categoria else None])
                        elif model == "Categoria":
                            cursor.execute("EXEC CREAR_CATEGORIA %s,%s",[forma.nombre, forma.categoria_padre.id if forma.categoria_padre else None])
                        elif model == "Lugar":
                            cursor.execute("EXEC CREAR_LUGAR %s, %s, %s, %s, %s",[forma.nombre, forma.descripcion, forma.imagen.name if forma.imagen else None, forma.direccion, forma.capacidad])  
                        elif model == "TipoBoleto":
                            cursor.execute("EXEC CREAR_TIPOBOLETO %s",[forma.nombre])
                        elif model == "Zona":
                            cursor.execute("EXEC CREAR_ZONA %s, %s, %s, %s",[forma.nombre, forma.cant_filas, forma.asientos_por_fila, forma.lugar.id])
                        elif model == "Evento":
                            cursor.execute("EXEC CREAR_EVENTO %s, %s, %s, %s, %s, %s, %s, %s",[forma.nombre, forma.descripcion, forma.imagen.name if forma.imagen else None, forma.fecha_inicio, forma.fecha_fin, forma.categoria.id, forma.lugar.id, forma.artista.id if forma.artista else None])
                        elif model == "Funcion":
                            cursor.execute("EXEC CREAR_FUNCION %s, %s", [forma.fecha, forma.evento.id])
                        cursor.execute("REVERT")
                else:
                    forma.save()
            else:
                forma=form.save(commit=False)
                if forma.id is None:
                    for i in range(forma.zona.cant_filas):
                        for j in range(forma.zona.asientos_por_fila):
                            boleto = Boleto(costo=forma.costo, zona=forma.zona, tipo=forma.tipo, evento=forma.evento, activo=1)
                            boleto.fila = chr(i+65)
                            boleto.asiento = j+1
                            boleto.nombre = "BOLETO %s%s%s" % (boleto.zona, boleto.fila, boleto.asiento)
                            with connection.cursor() as cursor:
                                if modo:
                                    cursor.execute("EXECUTE AS USER = %s", [modo])
                                    cursor.execute("EXECUTE CREAR_BOLETO %s, %s, %s, %s, %s, %s, %s", [boleto.nombre, boleto.costo, boleto.fila, boleto.asiento, boleto.evento.id, boleto.zona.id, boleto.tipo.id])
                                    cursor.execute("REVERT")

            return HttpResponseRedirect('/crud/%s/#' % (model))
    else:
        form = FormClass(instance=instance)

    return render(request, 'crud.html', locals())

def eventos(request, categoria=None):
    eventos = Evento.objects.raw("SELECT * FROM EVENTOS_DISPONIBLES WHERE activo=1")
    categorias = Categoria.objects.raw("SELECT * FROM EVENTOS.CATEGORIA WHERE activo=1 AND categoria_padre IS NULL")
    user = request.session.get('user_id', False)
    if Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE id= %s", [user]):
        user = Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE id= %s", [user])[0]

    cat = None
    if categoria:
        cat = Categoria.objects.raw("SELECT * FROM EVENTOS.CATEGORIA WHERE nombre=%s", [categoria])[0]
        eventos = Evento.objects.raw("SELECT * FROM EVENTOS_DISPONIBLES WHERE activo=1 AND categoria_id=%s", [cat.id])

    if request.GET.get("cat_search", None):
        cat = Categoria.objects.raw("SELECT * FROM EVENTOS.CATEGORIA WHERE id=%s",[request.GET["cat_search"]])[0]
        categoria = cat.nombre
        if request.GET.get("query", None):
            query = request.GET.get("query", None)
            eventos = Evento.objects.raw("EXEC BUSQUEDA_EVENTO %s, %s", [query, cat.id])

    return render(request, "eventos.html", locals())

def perfil_evento(request, id=None):
    categorias = Categoria.objects.raw("SELECT * FROM EVENTOS.CATEGORIA WHERE activo=1 AND categoria_padre IS NULL")
    user = request.session.get('user_id', False)
    if Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE id= %s", [user]):
        user = Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE id= %s", [user])[0]
    if id is None:
        return HttpResponseRedirect("/eventos")
    
    evento = Evento.objects.raw("SELECT * FROM EVENTOS.EVENTO WHERE activo=1 AND id=%s", [id])[0]
    funciones = Funcion.objects.raw("EXEC FUNCIONES_VALIDAS %s" % [evento.id])

    return render(request, "info-evento.html", locals())

def boletos(request, id=None):
    c = {}
    c.update(csrf(request))
    categorias = Categoria.objects.raw("SELECT * FROM EVENTOS.CATEGORIA WHERE activo=1 AND categoria_padre IS NULL")
    user = request.session.get('user_id', False)
    if Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE id= %s", [user]):
        user = Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE id= %s", [user])[0]
    else:
        return HttpResponseRedirect("/login")
    if id is None:
        return HttpResponseRedirect("/eventos")
    funcion = Funcion.objects.raw("SELECT * FROM EVENTOS.FUNCION WHERE id=%s", [id])[0]
    tipos = TipoBoleto.objects.raw("SELECT * FROM VENTAS.TIPO_BOLETO WHERE id IN (SELECT tipo_id FROM VENTAS.BOLETO WHERE evento_id=%s)", [funcion.evento.id])
    zonas = Zona.objects.raw("SELECT * FROM EVENTOS.ZONA WHERE id IN (SELECT zona_id FROM VENTAS.BOLETO WHERE evento_id=%s)", [funcion.evento.id])
    boletos = None
    if request.GET.get("qty", None) and request.GET.get("type", None) and request.GET.get("zone", None):
        qty = int(request.GET.get("qty", None))
        tipo = TipoBoleto.objects.raw("SELECT * FROM VENTAS.TIPO_BOLETO WHERE id=%s", [request.GET.get("type", None)])[0]
        zona = Zona.objects.raw("SELECT * FROM EVENTOS.ZONA WHERE id=%s", [request.GET.get("zone", None)])[0]
        boletos = Boleto.objects.raw("SELECT * FROM VENTAS.BOLETO WHERE tipo_id=%s AND zona_id=%s AND evento_id=%s AND activo=1 AND NOT id IN (SELECT boleto_id from VENTAS.RESERVACION WHERE funcion_id=%s AND activo=1) AND dbo.CHECK_LOCK(id,%s,%s)=1",[tipo.id, zona.id, funcion.evento.id, funcion.id, user.id, funcion.id])[:qty]
    if request.GET.get("all", None):
        see_all = True
        boletos = Boleto.objects.raw("SELECT * FROM VENTAS.BOLETO WHERE evento_id=%s AND activo=1 AND NOT id IN (SELECT boleto_id from VENTAS.RESERVACION WHERE funcion_id=%s AND activo=1) AND dbo.CHECK_LOCK(id,%s,%s)=1",[funcion.evento.id, funcion.id, user.id, funcion.id])
    return render(request, "seleccionarboletos.html", locals())

def comprar(request):
    c = {}
    c.update(csrf(request))
    user = request.session.get('user_id', False)
    if Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE id= %s", [user]):
        user = Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE id= %s", [user])[0]
    else:
        return HttpResponseRedirect("/login")
    if request.POST:
        boleto_ids = request.POST.getlist("options")
        funcion = request.POST.get("funcion")
    
        if len(boleto_ids) >5:
            return HttpResponseRedirect("/boletos/%s/?error=1" % funcion)
        
        info_pagos = InfoPago.objects.raw("SELECT * FROM AUTH.INFO_PAGO WHERE usuario_id=%s AND activo=1", [user.id])
        total = 0
        if "confirm" in request.POST:
            insecure_query = "SELECT * FROM VENTAS.BOLETO WHERE id IN (%s) AND dbo.HAS_LOCK(id,%s,%s)=1" % (",".join(boleto_ids), user.id, funcion)
            print(insecure_query)
            boletos = Boleto.objects.raw(insecure_query)
            print(sum(1 for b in boletos))
            if sum(1 for b in boletos) != len(boleto_ids):
                return HttpResponseRedirect('/boletos/%s/?error=2&all=True'%funcion)
            if request.POST.get("pago", None) != '0':
                info_pago = InfoPago.objects.raw("SELECT * FROM AUTH.INFO_PAGO WHERE usuario_id=%s AND activo=1 AND id=%s", [user.id, request.POST.get("pago", None)])[0]
                with connection.cursor() as cursor:
                    for b in boletos:
                        cursor.execute("DELETE FROM LOCK WHERE usuario_id=%s AND boleto_id=%s AND funcion_id=%s",[user.id, b.id, funcion])
                
                for b in boletos:
                    r = Reservacion(boleto=b, usuario=user, funcion_id=funcion, fecha_compra=datetime.now(),pago=info_pago,activo=1)
                    r.save()
                return HttpResponseRedirect('/perfil/?exito=True')
            error = {}
            new_info = {}
            for field in request.POST:
                new_info[field] = request.POST[field] 
                if request.POST[field] == "":
                    error[field] = "Debe ser llenado"

            if not error:
                direccion = new_info["address1"] + new_info["address2"] + new_info["city"] + new_info["state"]
                expira = datetime.strptime('%s 1 %s  12:00AM' % (new_info["month"], new_info["year"]), '%m %d %y %I:%M%p')
                
                with connection.cursor() as cursor:
                    cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                    cursor.execute("EXEC CREAR_INFOPAGO %s, %s, %s, %s, %s, %s, %s, %s",[new_info["firstname"], new_info["lastname"],direccion,new_info["zipcode"],new_info["creditcard"],new_info["cvv"],expira,user.id])
                    for b in boletos:
                        cursor.execute("DELETE FROM LOCK WHERE usuario_id=%s AND boleto_id=%s AND funcion_id=%s",[user.id, b.id, funcion])

                info_pago=InfoPago.objects.raw("SELECT * FROM AUTH.INFO_PAGO WHERE usuario_id=%s AND activo=1 ORDER BY ID DESC", [user.id])[0]
                for b in boletos:
                    r = Reservacion(boleto=b, usuario=user, funcion_id=funcion, fecha_compra=datetime.now(),pago=info_pago,activo=1)
                    r.save()


                return HttpResponseRedirect('/perfil/?exito')
        else:
            insecure_query = "SELECT * FROM VENTAS.BOLETO WHERE id IN (%s) AND dbo.CHECK_LOCK(id,%s,%s)=1" % (",".join(boleto_ids), user.id, funcion)
            boletos = Boleto.objects.raw(insecure_query)
            for b in boletos:
                total += b.costo
            if sum(1 for b in boletos) != len(boleto_ids):
                    return HttpResponseRedirect('/boletos/%s/?error=2&all=True'%funcion)
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                for id in boleto_ids:
                    cursor.execute("EXEC LOCK_TICKET %s, %s, %s", [id, user.id, funcion])
    else:
        return HttpResponseRedirect("/")
    return render(request, "confirmarcompra.html", locals())

def perfil(request):
    c = {}
    c.update(csrf(request))
    categorias = Categoria.objects.raw("SELECT * FROM EVENTOS.CATEGORIA WHERE activo=1 AND categoria_padre IS NULL")
    user = request.session.get('user_id', False)
    if Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE id= %s", [user]):
        user = Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE id= %s", [user])[0]
    else:
        return HttpResponseRedirect("/login")
    
    reservaciones = Reservacion.objects.raw("EXEC RESERVACIONES_VALIDAS %s", [user.id])

    if request.POST:
        new_user = {}
        error = {}
        for field in request.POST:
            new_user[field] = request.POST[field] 
            if field == "":
                error[field] = "Debe ser llenado"

        if "password" in request.POST:
            if new_user["new_pass"] != new_user["new_repass"]:
                error["new_repass"] = "Repite la contraseña sin cambios"
            elif check_password(new_user["password"], user.contraseña):
                user.password = make_password(new_user["new_pass"])
                user.save()
                return HttpResponseRedirect("/perfil/#")
            else:
                error["password"] = "Contraseña incorrecta"
        else:
            try:
                validate_email(new_user["correo"])
                if Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE correo=%s AND NOT id=%s", [request.POST["correo"], user.id]):
                    error["correo"] = "Correo ya fue utilizado en otra cuenta"
            except:
                error["correo"] = "Error en formato de email"

            if not error:
                user.nombre = new_user["nombre"]
                user.apellido_p = new_user["apellido_p"]
                user.apellido_m = new_user["apellido_m"]
                user.correo = new_user["correo"]
                user.save()
                return HttpResponseRedirect("/perfil/#")

    return render(request, "perfil.html", locals())    

def reporte(request, reporte=None):
    modelos = ["Artista", "Categoria", "Lugar", "TipoBoleto", "Zona", "Evento", "Funcion", "Boleto"]
    reportes = [
        {'name':"Evento Mayor Ganancia", 'link': "EventoMayorGanancia"}, 
        {'name':"Evento Menor Ganancia", 'link': "EventoMenorGanancia"}, 
        {'name':'Eventos Mayor al Promedio','link':'EventosMayoralPromedio'},
        {'name':"Ganancias por evento", 'link':'Gananciasporevento'},
        {'name':"Ganancias por mes", 'link':'Gananciaspormes'},
        {'name':"Ganancias por artista", 'link':'Gananciasporartista'},
        {'name':"Ganancias por lugar", 'link': "Gananciasporlugar"}]
    user = request.session.get('user_id', False)
    if Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE id= %s", [user]):
        user = Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE id= %s", [user])[0]
        
        if not user.es_admin:
            return HttpResponseRedirect('/')
        elif user.nombre == "EVENTOS":
            modelos = ["Artista", "Categoria", "Lugar", "Zona", "Evento", "Funcion"]
            modo = "eventos_user"
        elif user.nombre == "VENTAS":
            modelos = ["TipoBoleto", "Boleto"]
            modo = "ventas_user"
        elif user.nombre == "AUTH":
            modelos = ["Usuario"]
    else:
        return HttpResponseRedirect('/')
    tabla = None

    rname = None
    for r in reportes:
        if r['link'] == reporte:
            rname = r['name']
            break
    if rname is None:
        return HttpResponseRedirect('/reportes/EventoMayorGanancia')

    query = "SELECT * FROM %s" % reporte
    if reporte == "Gananciaspormes":
        query += " ORDER BY 'AÑO', 'MES' ASC"
    elif reporte == "Gananciasporevento":
        query += " ORDER BY 'Fecha Inicio' DESC"
    elif reporte == "Gananciasporartista":
        query += " ORDER BY 'GANANCIAS'  DESC"
    elif reporte == "Gananciasporlugar":
        query += " ORDER BY 'GANANCIAS'  DESC"
    with connection.cursor() as cursor:
        cursor.execute(query)
        tabla = dictfetchall(cursor)

    columns = []
    try:
        for f in tabla[0]:
            columns.append(f)
    except:
        pass

    return render(request, "report.html", locals())

def bitacora(request):
    modelos = ["Artista", "Categoria", "Lugar", "TipoBoleto", "Zona", "Evento", "Funcion", "Boleto"]
    reportes = [
        {'name':"Evento Mayor Ganancia", 'link': "EventoMayorGanancia"}, 
        {'name':"Evento Menor Ganancia", 'link': "EventoMenorGanancia"}, 
        {'name':'Eventos Mayor al Promedio','link':'EventosMayoralPromedio'},
        {'name':"Ganancias por evento", 'link':'Gananciasporevento'},
        {'name':"Ganancias por mes", 'link':'Gananciaspormes'},
        {'name':"Ganancias por artista", 'link':'Gananciasporartista'},
        {'name':"Ganancias por lugar", 'link': "Gananciasporlugar"}]
    user = request.session.get('user_id', False)
    if Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE id= %s", [user]):
        user = Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE id= %s", [user])[0]
        if not user.es_admin:
            return HttpResponseRedirect('/')
        elif user.nombre == "EVENTOS":
            modelos = ["Artista", "Categoria", "Lugar", "Zona", "Evento", "Funcion"]
            modo = "eventos_user"
        elif user.nombre == "VENTAS":
            modelos = ["TipoBoleto", "Boleto"]
            modo = "ventas_user"
        elif user.nombre == "AUTH":
            modelos = ["Usuario"]
    else:
        return HttpResponseRedirect('/')
    tabla = {}
    with connection.cursor() as cursor:
        if user.nombre == "EVENTOS":
            cursor.execute("SELECT * FROM EVENTOS.BITACORA ORDER BY fecha DESC")
        elif user.nombre == "VENTAS":
            cursor.execute("SELECT * FROM VENTAS.BITACORA ORDER BY fecha DESC")
        else:
            cursor.execute("SELECT * FROM AUTH.BITACORA UNION SELECT * FROM VENTAS.BITACORA UNION SELECT * FROM EVENTOS.BITACORA ORDER BY fecha DESC")
        
        tabla = dictfetchall(cursor)
    
    return render(request, "bitacora.html", locals())

def compras(request):
    user = request.session.get('user_id', False)
    if Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE id= %s", [user]):
        user = Usuario.objects.raw("SELECT * FROM AUTH.USUARIO WHERE id= %s", [user])[0]
    else:
        return HttpResponseRedirect("/login")

    reservaciones = Reservacion.objects.raw("SELECT * FROM VENTAS.RESERVACION WHERE usuario_id = %s AND activo=1", [user.id])

    return render(request, "compras.html", locals())