from django.shortcuts import render, get_object_or_404, redirect
from models import Campanha


def show_mapas(request, campanha_id):
    campanha = get_object_or_404(Campanha, id=campanha_id)

    contex = {}
    return render(request, "global/mapas.html")
