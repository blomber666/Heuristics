import numpy as np
import requests
import json 
import openpyxl as xl
import folium
import webbrowser as wb
import random as r
from copy import deepcopy
from time import time 
import os

dist=np.loadtxt('distanze.txt', dtype=int).reshape((34,34))

with open("InputCompleto.json") as js:
    f=json.load(js)

nome_attr=[]
Grad_pond=[]
Grad_pond.insert(0,0)

for p in f["attrazioni"]: 
        nome_attr.append(p["nome"])
        Grad_pond.append(np.average(list(p["gradimento"].values()), weights=list(f["utente"]["gradimento"].values())))

def dist_home(): #utilizzo iniziale solo per calcolare le distanze albergo-attrazione

    try:
        with open("API_orienteering-fe.txt","r") as api:
            api_key=api.read()

        home=f["utente"]
        start=str(home["x"])+", "+str(home["y"])
        url="https://maps.googleapis.com/maps/api/distancematrix/json?"

        for j in range(len(f["attrazioni"])):
            dest=f["attrazioni"][j]["nome"]+", Ferrara, Italia"
            r=requests.get(url + "&origins=" + start + "&destinations=" + dest + "&mode=walking" + "&transit_routing_preference=less_walking" + "&language=ita" + "&key=" + api_key)
            dist[0,j+1] = dist[j+1,0]= round(r.json()["rows"][0]["elements"][0]["duration"]["value"]/60)
        
        return 1

    except:
        return 0

def open_attr(node, time): #verifico che una determinata attrazione sia aperta
    if ( node==0 or (f["utente"]["t_inf"] + time) >= f["attrazioni"][node-1]["tw"]["t_inf"]  and  (f["utente"]["t_inf"] + time) <= f["attrazioni"][node-1]["tw"]["t_sup"] ):
        return 1
    else:
        return 0

def end_tour(time,a,b): #calcolo se rimane tempo per visitare l'attrazione e tornare all'albergo
    
    t_tot=f["utente"]["t_sup"]-f["utente"]["t_inf"]
    t_pass= time + (dist[a,b] + dist[b,0])/60
    #tempo.passato = tempo.posti.già.visitati + (tempo.pross.attrazione + tempo.ritorno.albergo)
    if( t_tot >= t_pass):
        return 0
    else:
        return 1

def wexcel(tour, fun_name, iteration): #scrivo il risultato su un file excel

    try:
        sheet=xl.Workbook()
        ricerca=sheet.get_sheet_by_name('Sheet')
        
        ricerca['A1']='Num nodi visitati'
        ricerca['A1'].value
        ricerca['A2']=len(tour[0])-1
        ricerca['A2'].value

        ricerca['B1']="Gradimento:"
        ricerca['B1'].value
        ricerca['B2']=tour[1]
        ricerca['B2'].value

        ricerca['C1']='Tempo trascorso:'
        ricerca['C1'].value
        ricerca['C2']=tour[2]
        ricerca['C2'].value
        
        ricerca['E1']='Nodi visitati:'
        ricerca['E1'].value

        for i in range(len(tour[0])):    
            ricerca['E'+str(i+2)]=tour[0][i]
            ricerca['E'+str(i+2)].value
        
        sheet.save('Solutions\\ricerca_'+fun_name+'_'+str(iteration)+'.xlsx')
        return 1

    except:
        return 0    

def write_res(tour, fun_name, iteration): #scrivo i risultati su un file excel e creo una mappa per ogni soluzione possibile trovata

    map=folium.Map(location=[44.83895673644131, 11.614725304456822], zoom_start=14)

    folium.Marker(location=[f["utente"]["x"],f["utente"]["y"]],popup="Albergo", tooltip=0, icon=folium.Icon(color="lightgreen",icon="home", prefix="fa")).add_to(map)
    
    for i in range(len(f["attrazioni"])):
        folium.Marker(
            location=[f["attrazioni"][i]["x"],f["attrazioni"][i]["y"]],
            popup=f["attrazioni"][i]["nome"],
            icon=folium.Icon(color="darkred", icon="map", prefix="fa")
            ).add_to(map)

    wexcel(tour, fun_name, iteration)
    route(tour)

    folium.GeoJson("percorso.geojson", name=fun_name).add_to(map)
    folium.LayerControl().add_to(map)
    
    for k in tour[0][1:-1]:
        folium.Marker(
            location=[f["attrazioni"][(k-1)]["x"],f["attrazioni"][(k-1)]["y"]],
            popup= f["attrazioni"][(k-1)]["nome"], 
            tooltip= tour[0].index(k),
            icon= folium.Icon(color="darkpurple", icon="map", prefix="fa")
            ).add_to(map)

    map.save("C:\\Users\\luk8_\\Desktop\\MAGISTRALE\\Ricerca Operativa\\Progetto\\Solutions\\"+fun_name+"_"+str(iteration)+".html")
    #wb.open("C:\\Users\\luk8_\\Desktop\\MAGISTRALE\\Ricerca Operativa\\Progetto\\Solutions\\"+fun_name+"_"+str(iteration)+".html")
    del(map)

def route(tour): #scrivo le coordinate dei luoghi su un file geojson per poi creare la mappa
    
    clear_route()

    try:
        with open("percorso.geojson") as js:
            g=json.load(js)

        for i in tour[0][1:-1]:
            attr=[f["attrazioni"][(i-1)]["y"],f["attrazioni"][(i-1)]["x"]]
            g["features"][0]["geometry"]["coordinates"].append(attr)

        with open("percorso.geojson", "w") as js:
            json.dump(g, js, indent=4)

        return 1

    except:
        return 0

def clear_route(): #ripulisco il file geojson contenente il percorso della soluzione predcedente
    
    r_default={
        "type": "FeatureCollection",
        "features": [
        {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "LineString",
                "coordinates": [
                ]
            }
        }
        ]
    }
    
    r_default["features"][0]["geometry"]["coordinates"].append([f["utente"]["y"],f["utente"]["x"]])


    with open("percorso.geojson", "w") as js:
        json.dump(r_default, js, indent=4)
    
    return 1