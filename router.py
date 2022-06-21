import sys
import socket
from utilities import *

if __name__ == '__main__':

  # Instanciamos el socket
  conn_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  # Definimos el tamaño de buffer
  buff_size = 1024

  # Parseamos los argumentos
  try:

    if len(sys.argv) == 4:

      router_IP = sys.argv[1]
      router_port = int(sys.argv[2])
      routing_table_file_name = sys.argv[3]

    # Si no se pasan correctamente los argumentos levantamos una exepción
    else:
      raise Exception(f'Expected 3 arguments, {len(sys.argv) - 1} were given')

  except Exception as err:
    print(err)

  # Si no se levanta ningun error proseguimos
  else:

    # Hacemos que el socket escuche de forma no bloqueante en el par (router_IP, router_port)
    conn_socket.bind((router_IP, router_port))

    # Instanciamos una tabla de ruteo de tipo RoundRobinRoutingTable
    round_robin_routing_table = RoundRobinRoutingTable(routing_table_file_name)

    # Recibimos paquetes de forma indefinida
    while True:
      
      # Recibimos un paquete
      ip_header_buffer, _ = conn_socket.recvfrom(buff_size)

      # Parseamos su contenido
      ip_header = parse_ip_header(ip_header_buffer.decode())

      # Si el TTL del paquete es menor o igual a 0, luego ignoramos el paquete y 
      # seguimos a la siguiente iteración (puede ser menor a cero si se inicializa
      # un paquete con un número negativo --lo cual es un error pero lo prevenimos
      # igualmente--)
      if ip_header.ttl <= 0:
        continue

      # Si el mensaje es para este router, imprimimos en pantalla el mensaje
      if ip_header.ip_address == router_IP and ip_header.port == router_port:
        print(ip_header.msg)

      # De lo contrario buscamos como redirigir en la tabla de rutas
      else:

        # Generamos el siguiente salto
        forward_address = next_hop(
          round_robin_routing_table,
          (ip_header.ip_address, ip_header.port)
        )

        # Si el forward adress es None, luego no se encontró como redirigir en la
        # tabla de ruta, e imprimimos un mensaje informando aquello
        if forward_address is None:
          print('No hay rutas hacia', (ip_header.ip_address, ip_header.port), 
                'para paquete', ip_header.ip_address)
        
        # De lo contrario, se encontró una forma de redirigir, e informamos aquello
        else:
          print('redirigiendo paquete', ip_header.ip_address, 'con destino final',
                (ip_header.ip_address, ip_header.port), 'desde', (router_IP, router_port),
                'hacia', forward_address)

          # Decrementamos el TTL
          ip_header.ttl -= 1

          # Para finalmente realizar la redirección
          conn_socket.sendto(ip_header.to_string().encode(), forward_address)




