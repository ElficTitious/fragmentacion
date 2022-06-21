from dataclasses import dataclass
import ipaddress

@dataclass
class IPHeader:
  """Data class usada para representar un header IP.

  Attributes:
  -----------
  ip_address (str): Dirección IP donde se encuentra escuchando el router
                    de destino del paquete.
  port (int): Puerto en que se encuentra escuchando el router de destino
              del paquete en la IP ip_address.
  msg (str): Mensaje siendo enviado en el paquete.
  """

  ip_address: str
  port: int
  ttl: int
  msg: str

  def to_string(self) -> str:
    """Método usado para tranformar esta instancia a string (inversa de
    parse_ip_header). Podríamos hacer un override de __str__, pero nos 
    interesa conservar ese comportamiento.

    Returns:
    --------
    (str): Representación del header como str, debe ser la inversa de
           parse_ip_header. Es decir parse_ip_header(s).to_string() == s
           siempre se cumple.
    """
    return f'{self.ip_address},{self.port},{self.ttl},{self.msg}'

@dataclass
class RoutingTableLine:
  """Data class usada para representar una línea de una tabla de ruteo.

  Attributes:
  -----------
  possible_ip_addresses (list[str]): Lista con todas las potenciales direcciones
                                     IP generadas a partir de una red (CIDR).
  initial_port (int): Inicio del rango de puertos.
  final_port (int): Fin del rango de puertos.
  landing_ip (str): Dirección IP donde redirigir dados los valores anteriores
  landing_port (int): Puerto donde redirigir dados los primeros dos valores y la IP 
                      anterior
  """

  possible_ip_addresses: list[str]
  initial_port: int
  final_port: int
  landing_ip: str
  landing_port: int

class CircularArrayWithPointer:
  """Clase usada para representar un arreglo circular, con un puntero indicando
  cual es el proximo elemento solicitable (solo se puede solicitar un solo elemento
  en un determinado momento).

  Methods:
  --------
  next:
    Retorna el próximo elemento solicitable en el arreglo.
  """

  def __init__(self, data: list):
    self.__array = data
    self.__n = len(data)
    self.__pointer = 0

  def next(self):
    """Método usado para solicitar un elemento del arreglo circular. Éste retorna
    los elementos en orden ascendente dentro de l arreglo, pero una vez llega al
    final, vuelve al comienzo. Si el arreglo tiene largo 0, luego retorna None.

    Returns:
    --------
      Elemento en el arreglo dado por el orden anterior en que se han pedido elementos.
    """

    # Si el arreglo no tiene elementos, retornamos None
    if self.__n == 0:
      return None

    # Si el puntero está alfinal del arreglo, vuelve el puntero al comienzo
    # y retorna el último elemento.
    elif self.__pointer == self.__n - 1:
      prev_pointer = self.__pointer
      self.__pointer = 0
      return self.__array[prev_pointer]

    # De lo contrario aumentamos el puntero en uno y retornamos el elemento en que
    # estaba anteriormente el puntero.
    else:
      prev_pointer = self.__pointer
      self.__pointer += 1
      return self.__array[prev_pointer]

def parse_routing_table_line(routing_table_line: str) -> RoutingTableLine:
  """Función que dada una linea de una tabla de ruteo, de la forma
  [Red (CIDR)] [Puerto_Inicial] [Puerto_final] [IP_Para_llegar] [Puerto_para_llegar],
  la parsea retornando una instancia de RoutingTableLine.

  Parameters:
  -----------
  routing_table_line (str): Linea de una tabla de ruteo, la cual debe ser de la forma
                            [Red (CIDR)] [Puerto_Inicial] [Puerto_final] [IP_Para_llegar] [Puerto_para_llegar].
  
  Returns:
  --------
  (RoutingTableLine): Linea de la tabla de ruteo pasada como parametro, pero parseada y empaquetada
                      en una instancia de la data class RoutingTableLine.
  """

  # Comenzamos por extraer el contenido de la línea en una lista
  routing_table_line_contents_list = routing_table_line.split(' ')

  # Guardamos el contenido en variables ad-hoc
  cidr_net = routing_table_line_contents_list[0]
  initial_port = int(routing_table_line_contents_list[1])
  final_port = int(routing_table_line_contents_list[2])
  landing_ip = routing_table_line_contents_list[3]
  landing_port = int(routing_table_line_contents_list[4])

  # Generamos la lista con todas las potenciales direcciones IP generadas 
  # a partir de la red (CIDR) presente en la linea.
  possible_ip_addresses = [str(ip) for ip in ipaddress.IPv4Network(cidr_net)]

  # Retornamos la instancia de RoutingTableLine
  return RoutingTableLine(possible_ip_addresses, initial_port, 
                          final_port, landing_ip, landing_port)

class RoundRobinRoutingTable:
  """Clase usada para representar tablas de ruteo, añadiendo la funcionalidad
  de alternar forwarding de paquetes cuando existen varias rutas posibles para
  un mismo paquete.
  """

  def __init__(self, routing_table_file_name: str):
    self.__routing_table_file_name = routing_table_file_name
    self.__table = {}

  def __generate_entry(self, destination_address: tuple[str, int]):
    """Método privado usado para generar la entrada asociada a una dirección de
    destino en una instancia de esta clase. Esta entrada sera del tipo
    CircularArrayWithPointer. Notemos que si no se encuentra una forma de hacer
    forward para la dirección de destino, el arreglo circular será vacío, y al hacerle
    next se obtendrá None, que es el comportamiento deseado.

    Parameters:
    -----------
    destination_address (tuple[str, int]): Dirección de destino para la cual generar
                                           la entrada.
    """

    # Desempaquetamos la dirección de destino por facilidad de uso
    destination_ip, destination_port = destination_address

    # Creamos la lista con la cual inicializar la instancia de CircularArrayWithPointer
    forward_adresses_list = []

    # Abrimos el archivo que contiene la tabla de ruteo y leemos sus lineas
    routing_table_file = open(self.__routing_table_file_name, 'r')
    routing_table_lines = routing_table_file.readlines()

    # Iteramos sobre las lineas
    for line in routing_table_lines:

      # Parseamos la línea
      routing_table_line = parse_routing_table_line(line.strip('\n'))

      # Revisamos si en la linea actual se indica como hacer forward para la dirección de destino
      if (destination_ip in routing_table_line.possible_ip_addresses and 
          destination_port in range(routing_table_line.initial_port, routing_table_line.final_port + 1)):
      
        # De ser el caso agregamos la dirección a la cual hacer forward a la lista con la cual inicializar
        # el CircularArrayWithPointer
        next_hop_ip, next_hop_port = (routing_table_line.landing_ip, routing_table_line.landing_port)
        forward_adresses_list.append((next_hop_ip, next_hop_port))

    # Cerramos el archivo con tabla de ruteo
    routing_table_file.close()

    # Finalmente inicializamos la entrada asociada a esta dirección de destino
    self.__table[destination_address] = CircularArrayWithPointer(forward_adresses_list)

  def next_hop(self, destination_address: tuple[str, int]) -> tuple[str, int] | None:
    """Método usado para, dada la lista de ruteo con que se instancia este
    objeto, y la dirección de destino pasada como parámetro, obtener el próximo salto
    en el arreglo circular de posibles formas de hacer forward. Si no existe una entrada
    en el diccionario subyacente, este se genera antes de retornar. Notemos que si no existe
    una forma de hacer forward, por la manera en que está implementado el método encargado
    de generar el arreglo circular, y el comportamiento del arreglo circular al estar vacío,
    se retorna None (que es el comportamiento esperado).

    Parameters:
    -----------
    destination_address (tuple[str, int]): Par (destination_ip, destination_port) para el cual
                                           se busca hacer forward.

    Returns:
    --------
    (tuple[str, int] | None): Próxima manera de hacer forward, donde de existir una se retorna
                              (next_hop_IP, next_hop_port). Ahora, si no existe una forma de
                              hacer forward, el arreglo circular subyacente estará vacio y por
                              ende se retornará None.
    """
    if destination_address in self.__table:
      return self.__table[destination_address].next()
    
    else:
      self.__generate_entry(destination_address)
      return self.__table[destination_address].next()


def parse_ip_header(ip_header: str) -> IPHeader:
  """Función encargada de, dado un header IP representado como
  un string de la forma [Dirección IP],[Puerto],[TTL],[mensaje], retornar
  un objeto de la data class IPHeader.

  Parameters:
  -----------
  ip_header (str): Header IP representado como un string de la forma 
                   [Dirección IP],[Puerto],[TTL],[mensaje]
  
  Returns:
  --------
  (IPHeader): Instancia de la data class representando el mismo header ip
              pasado como parámetro
  """

  # Extraemos el contenido del header
  packet_contents_list = ip_header.split(',')

  # Guardamos el contenido en variables ad-hoc
  ip_address = packet_contents_list[0]
  port = int(packet_contents_list[1])
  ttl = int(packet_contents_list[2])
  msg = packet_contents_list[3]

  # Retornamos el contenido empaquetado en una instancia de IPHeader
  return IPHeader(ip_address, port, ttl, msg)

def next_hop(round_robin_routing_table: RoundRobinRoutingTable, 
             destination_address: tuple[str, int]) -> tuple[str, int] | None:
  """Función que dada una tabla de ruteo de tipo Round Robin, y un par
  (destination_ip, destination_port), retorna la siguiente manera de hacer forward usando la
  tabla de ruteo subyacente a la instancia de RoundRobinRoutingTable pasada como parámetro.
  De encontrar una dirección donde redirigir se retorna dicho par, de lo contrario se retorna None.

  Parameters:
  -----------
  round_robin_routing_table (RoundRobinRoutingTable): Instancia de tipo RoundRobinRoutingTable, la cual
                                                      contiene la tabla de ruteo a ser revisada.
  destination_address (tuple[str, int]): Par (destination_ip, destination_port) a buscar en la
                                         tabla de ruteo.
  
  Returns:
  --------
  (tuple[str, int] | None): De encontrar una o más direcciones donde redirigir, se retorna la siguiente
                            dirección en el arreglo circular subyacente, que será de la forma
                            (next_hop_IP, next_hop_port), pero de recorrer la tabla completa y no encontrar
                            una ruta apropiada, se retorna None.
  """

  return round_robin_routing_table.next_hop(destination_address)
  
