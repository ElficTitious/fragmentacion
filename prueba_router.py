import sys
import socket

if __name__ == '__main__':

  # Instanciamos el socket
  conn_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

  # Parseamos los argumentos
  try:

    if len(sys.argv) == 4:
      
      headers = sys.argv[1]
      initial_router_IP = sys.argv[2]
      initial_router_port = int(sys.argv[3])

    # Si no se pasan correctamente los argumentos levantamos una exepción
    else:
      raise Exception(f'Expected 3 arguments, {len(sys.argv) - 1} were given')

  except Exception as err:
    print(err)

  # Si no se levanta ningun error proseguimos
  else:

    # Abrimos el archivo y leemos sus lineas
    test_file = open('test_file.txt', 'r')
    test_file_lines = test_file.readlines()

    # Iteramos sobre las lineas
    for line in test_file_lines:

      # Generamos el header completo
      ip_header = f'{headers},{line}'

      # Lo enviamos al router escuchando en la dirección inicial
      conn_socket.sendto(
        ip_header.encode(), 
        (initial_router_IP, initial_router_port)
      )

    # Cerramos el archivo
    test_file.close()






