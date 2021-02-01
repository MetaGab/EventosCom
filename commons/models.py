# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

class TipoBoleto(models.Model):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=50)
    activo = models.SmallIntegerField()

    def __str__(self):
        return self.nombre

    def _do_insert(self, manager, using, fields, update_pk, raw):
        return super(TipoBoleto, self)._do_insert(
            manager, using,
            [f for f in fields if f.attname not in ['id']],
            update_pk, raw)

    class Meta:
        managed = False
        db_table = 'VENTAS].[TIPO_BOLETO'


class Usuario(models.Model):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=50)
    apellido_p = models.CharField(max_length=50, blank=True, null=True)
    apellido_m = models.CharField(max_length=50, blank=True, null=True)
    correo = models.CharField(max_length=50)
    contraseña = models.CharField(max_length=255)
    es_admin = models.SmallIntegerField(blank=True, null=True)
    activo = models.SmallIntegerField()

    def _do_insert(self, manager, using, fields, update_pk, raw):
        return super(Usuario, self)._do_insert(
            manager, using,
            [f for f in fields if f.attname not in ['id']],
            update_pk, raw)
    
    def __str__(self):
        return "%s %s %s" % (self.nombre, self.apellido_p, self.apellido_m)

    class Meta:
        managed = False
        db_table = 'AUTH].[USUARIO'


class Categoria(models.Model):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=50)
    categoria_padre = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, db_column="categoria_padre")
    activo = models.SmallIntegerField()

    def __str__(self):
        return self.nombre

    def _do_insert(self, manager, using, fields, update_pk, raw):
        return super(Categoria, self)._do_insert(
            manager, using,
            [f for f in fields if f.attname not in ['id']],
            update_pk, raw)

    class Meta:
        managed = False
        db_table = 'EVENTOS].[CATEGORIA'


class Artista(models.Model):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=50)
    apellido_p = models.CharField(max_length=50, blank=True, null=True)
    apellido_m = models.CharField(max_length=50, blank=True, null=True)
    descripcion = models.CharField(max_length=1024, blank=True, null=True)
    activo = models.SmallIntegerField()
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)

    def __str__(self):
        return "%s %s %s" % (self.nombre, self.apellido_p, self.apellido_m)

    def _do_insert(self, manager, using, fields, update_pk, raw):
        return super(Artista, self)._do_insert(
            manager, using,
            [f for f in fields if f.attname not in ['id']],
            update_pk, raw)

    class Meta:
        managed = False
        db_table = 'EVENTOS].[ARTISTA'

class Lugar(models.Model):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=1024, blank=True, null=True)
    imagen = models.ImageField(upload_to='uploads/', blank=True, null=True)
    direccion = models.CharField(max_length=1024, blank=True, null=True)
    capacidad = models.IntegerField(blank=True, null=True)
    activo = models.SmallIntegerField()

    def _do_insert(self, manager, using, fields, update_pk, raw):
        return super(Lugar, self)._do_insert(
            manager, using,
            [f for f in fields if f.attname not in ['id']],
            update_pk, raw)

    def __str__(self):
        return self.nombre

    class Meta:
        managed = False
        db_table = 'EVENTOS].[LUGAR'

class Zona(models.Model):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=50)
    cant_filas = models.IntegerField(blank=True, null=True)
    asientos_por_fila = models.IntegerField(blank=True, null=True)
    lugar = models.ForeignKey(Lugar, on_delete=models.CASCADE)
    activo = models.SmallIntegerField()

    def _do_insert(self, manager, using, fields, update_pk, raw):
        return super(Zona, self)._do_insert(
            manager, using,
            [f for f in fields if f.attname not in ['id']],
            update_pk, raw)

    def __str__(self):
        return self.nombre

    class Meta:
        managed = False
        db_table = 'EVENTOS].[ZONA'


class Evento(models.Model):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=1024, blank=True, null=True)
    imagen = models.ImageField(upload_to='uploads/', blank=True, null=True)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    activo = models.SmallIntegerField()
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    lugar = models.ForeignKey(Lugar, on_delete=models.CASCADE)
    artista = models.ForeignKey(Artista, on_delete=models.CASCADE, blank=True, null=True)

    def _do_insert(self, manager, using, fields, update_pk, raw):
        return super(Evento, self)._do_insert(
            manager, using,
            [f for f in fields if f.attname not in ['id']],
            update_pk, raw)

    def __str__(self):
        return self.nombre

    class Meta:
        managed = False
        db_table = 'EVENTOS].[EVENTO'


class InfoPago(models.Model):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    direccion = models.CharField(max_length=255)
    codigo_postal = models.CharField(max_length=5)
    numero_tarjeta = models.CharField(max_length=16)
    numero_seguridad = models.CharField(max_length=3)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    activo = models.SmallIntegerField()

    def _do_insert(self, manager, using, fields, update_pk, raw):
        return super(InfoPago, self)._do_insert(
            manager, using,
            [f for f in fields if f.attname not in ['id']],
            update_pk, raw)

    class Meta:
        managed = False
        db_table = 'AUTH].[INFO_PAGO'

class Boleto(models.Model):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=50)
    costo = models.DecimalField(max_digits=6, decimal_places=2)
    fila = models.CharField(max_length=1)
    asiento = models.IntegerField()
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE)
    zona = models.ForeignKey(Zona, on_delete=models.CASCADE)
    tipo = models.ForeignKey(TipoBoleto, on_delete=models.CASCADE)
    activo = models.SmallIntegerField()

    def _do_insert(self, manager, using, fields, update_pk, raw):
        return super(Boleto, self)._do_insert(
            manager, using,
            [f for f in fields if f.attname not in ['id']],
            update_pk, raw)


    class Meta:
        managed = False
        db_table = 'VENTAS].[BOLETO'

class Funcion(models.Model):
    id = models.IntegerField(primary_key=True)
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE)
    fecha = models.DateTimeField()
    activo = models.SmallIntegerField()

    def _do_insert(self, manager, using, fields, update_pk, raw):
        return super(Funcion, self)._do_insert(
            manager, using,
            [f for f in fields if f.attname not in ['id']],
            update_pk, raw)

    class Meta:
        managed = False
        db_table = 'EVENTOS].[FUNCION'


class Reservacion(models.Model):
    id = models.IntegerField(primary_key=True)
    boleto = models.ForeignKey(Boleto, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    funcion = models.ForeignKey(Funcion, on_delete=models.CASCADE)
    fecha_compra = models.DateTimeField()
    pago = models.ForeignKey(InfoPago, on_delete=models.CASCADE)
    activo = models.SmallIntegerField()

    def _do_insert(self, manager, using, fields, update_pk, raw):
        return super(Reservacion, self)._do_insert(
            manager, using,
            [f for f in fields if f.attname not in ['id']],
            update_pk, raw)

    class Meta:
        managed = False
        db_table = 'VENTAS].[RESERVACION'





