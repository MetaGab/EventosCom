from .views import *

from django.urls import path
from django.conf import settings 
from django.conf.urls.static import static 

urlpatterns = [
    path('', index, name="index"),
    path('login', login, name="login"),
    path('signup', signup, name="signup"),
    path('logout', logout, name="logout"),
    path('crud', crud, name="crud"),
    path('crud/<model>/', crud, name="crud"),
    path('crud/<model>/<id>/', crud, name="crud"),
    path('eventos', eventos, name="eventos"),
    path('eventos/<categoria>/', eventos, name="eventos"),
    path('evento/<id>/', perfil_evento, name="perfil_evento"),
    path('boletos/<id>/', boletos, name="boletos"),
    path('compra/', comprar, name='comprar'),
    path('perfil', perfil, name='perfil'),
    path('perfil/', perfil, name='perfil'),
    path('reportes', reporte, name="reporte"),
    path('reportes/<reporte>', reporte, name="reporte"),
    path('bitacora', bitacora, name="bitacora"),
    path('compras', compras, name="compras")
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)