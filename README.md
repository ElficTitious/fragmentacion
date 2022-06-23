# Actividad: Fragmentación

Semana 10-11: Redes IP, Módulo 4: Redes y Ruteo, CC4303-1

## Ejecución

Para ejecutar es necesario correr cada router en una ventana de terminal distinta, y enviar mensajes al router deseado usando `netcat`.
Cada router necesita como argumentos la IP del router y su puerto, sumado al nombre del archivo en que se encuentran sus tablas de ruta.

**Ejecución:**

Para correr cada router se debe pasar la IP del router y su puerto, sumado al nombre del archivo en que se encuentran sus tablas de ruta.

Ejemplo:

```bash
python3 router.py 127.0.0.1 8881 rutas/v1/R1.txt
```

## Funcionamiento

La lógica de un router se encuentra dentro del script `router.py`, y todas las funcionalidades auxiliares dentro de `utilities.py`. Puesto que está todo documentado dentro de los respectivos archivos, se procede solo a explicar el cambio realizado a round robin. Se agrega el MTU a las entradas almacenadas dentro de cada arreglo circular en el diccionario de `RoundRobinRoutingTable`, de esta manera al llamar a `next_hop()`, se retornará la dirección a la cual hacer forward junto con el MTU del enlace.

