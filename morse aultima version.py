import network
import socket
from machine import Pin, PWM
import time

# ============================================================
# CONFIGURACION DE RED - MODO ACCESS POINT
# ============================================================
# La Pico crea su propia red WiFi para comunicarse con VS Code
# ============================================================

SSID = "Pico_Stranger"
PASSWORD = "12345678"

def crear_red_wifi():
    """
    Crea un punto de acceso WiFi para que la PC se conecte a la Pico
    Retorna: La IP fija de la Pico (192.168.4.1)
    """
    wlan = network.WLAN(network.AP_IF)  # AP_IF = Access Point mode
    wlan.active(True)
    wlan.config(essid=SSID, password=PASSWORD)
    wlan.ifconfig(('192.168.4.1', '255.255.255.0', '192.168.4.1', '192.168.4.1'))
    
    print("RED WIFI CREADA")
    print("SSID: Pico_Stranger")
    print("PASSWORD: 12345678")
    print("IP: 192.168.4.1")
    return '192.168.4.1'

# ============================================================
# CONFIGURACION HARDWARE - PINES DE LA PICO
# ============================================================
# SER, CLK, FILA1-3: Controlan la matriz de LEDs (display de 13x3)
# BIT0-3: Envían los 4 bits al circuito incrementador (XOR)
# BOTON: Lee el pulsador para código Morse
# BUZZER: Emite sonido mientras se presiona el boton
# LED_RESULTADO0-3: Leen la salida del circuito incrementador
# ============================================================

# Pines para la matriz de LEDs (display)
SER   = Pin(27, Pin.OUT)   # Datos en serie para el shift register
CLK   = Pin(26, Pin.OUT)   # Clock para el shift register
FILA1 = Pin(13, Pin.OUT)   # Control de la fila 1 de la matriz
FILA2 = Pin(14, Pin.OUT)   # Control de la fila 2 de la matriz
FILA3 = Pin(15, Pin.OUT)   # Control de la fila 3 de la matriz

# Pines de salida para el incrementador (van al circuito XOR)
BIT0 = Pin(1, Pin.OUT)     # Bit menos significativo (GP1)
BIT1 = Pin(2, Pin.OUT)     # Bit 1 (GP2)
BIT2 = Pin(3, Pin.OUT)     # Bit 2 (GP3)
BIT3 = Pin(4, Pin.OUT)     # Bit 3 - mas significativo (GP4)

# Boton y Buzzer
BOTON = Pin(16, Pin.IN, Pin.PULL_UP)  # Boton con pull-up interno
BUZZER = PWM(Pin(28))                  # Buzzer con PWM
BUZZER.duty_u16(0)                     # Apagado inicial

# Pines de entrada para leer el resultado del circuito incrementador
LED_RESULTADO0 = Pin(5, Pin.IN)   # Bit 0 de salida del XOR
LED_RESULTADO1 = Pin(6, Pin.IN)   # Bit 1 de salida del XOR
LED_RESULTADO2 = Pin(7, Pin.IN)   # Bit 2 de salida del XOR
LED_RESULTADO3 = Pin(8, Pin.IN)   # Bit 3 de salida del XOR

# ============================================================
# TABLAS DE CONVERSION
# ============================================================
# TABLA_LEDS: Mapea caracteres a su posicion en la matriz (columna, fila)
# MORSE_MAP: Convierte codigo Morse a letras/numeros
# ============================================================

TABLA_LEDS = {
    'A':(1,1), 'C':(2,1), 'E':(3,1), 'G':(4,1), 'I':(5,1), 'K':(6,1), 'M':(7,1), 'O':(8,1), 'Q':(9,1), 'S':(10,1), 'U':(11,1), 'W':(12,1), 'Y':(13,1),
    'B':(1,2), 'D':(2,2), 'F':(3,2), 'H':(4,2), 'J':(5,2), 'L':(6,2), 'N':(7,2), 'P':(8,2), 'R':(9,2), 'T':(10,2), 'V':(11,2), 'X':(12,2), 'Z':(13,2),
    '0':(1,3), '1':(2,3), '2':(3,3), '3':(4,3), '4':(5,3), '5':(6,3), '6':(7,3), '7':(8,3), '8':(9,3), '9':(10,3), ' ':(11,3), '-':(12,3), '+':(13,3)
}

MORSE_MAP = {
    '.-':'A', '-...':'B', '-.-.':'C', '-..':'D', '.':'E', '..-.':'F', '--.':'G', '....':'H', '..':'I', '.---':'J', '-.-':'K', '.-..':'L', '--':'M', '-.':'N', '---':'O', '.--.':'P', '--.-':'Q', '.-.':'R', '...':'S', '-':'T', '..-':'U', '...-':'V', '.--':'W', '-..-':'X', '-.--':'Y', '--..':'Z', 
    '.----':'1', '..---':'2', '...--':'3', '....-':'4', '.....':'5', '-....':'6', '--...':'7', '---..':'8', '----.':'9', '-----':'0'
}

# ============================================================
# FUNCIONES DE LA MATRIZ DE LEDS
# ============================================================

def enviar_16_bits(valor: int):
    """
    Envia 16 bits en serie al shift register (74HC595)
    Los bits determinan que LEDs de la fila se encienden
    """
    for bit in range(15, -1, -1):  # De bit 15 a bit 0
        SER.value((valor >> bit) & 1)  # Enviar el bit
        CLK.high()  # Pulso de clock
        CLK.low()

def apagar_todo():
    """Apaga todos los LEDs de la matriz"""
    FILA1.low()
    FILA2.low()
    FILA3.low()
    enviar_16_bits(0)  # Todos los bits en 0

def mostrar_caracter(caracter, duracion_ms=600):
    """
    Muestra un caracter en la matriz de LEDs
    caracter: Letra o numero a mostrar
    duracion_ms: Tiempo que permanece encendido
    """
    ch = caracter.upper()
    if ch in TABLA_LEDS:
        col, fila = TABLA_LEDS[ch]  # Obtener columna y fila
        apagar_todo()
        enviar_16_bits(1 << (col - 1))  # Encender la columna especifica
        # Activar la fila correspondiente
        FILA1.value(fila == 1)
        FILA2.value(fila == 2)
        FILA3.value(fila == 3)
        if duracion_ms > 0:
            time.sleep_ms(duracion_ms)
            apagar_todo()

# ============================================================
# FUNCIONES DEL INCREMENTADOR EN 5
# ============================================================

def enviar_bits_al_incrementador(bits):
    """
    Envia los 4 bits al circuito incrementador (compuertas XOR)
    bits: Lista de 4 valores [bit0, bit1, bit2, bit3]
    """
    BIT0.value(bits[0])  # GP1 - Bit menos significativo
    BIT1.value(bits[1])  # GP2
    BIT2.value(bits[2])  # GP3
    BIT3.value(bits[3])  # GP4 - Bit mas significativo

def leer_resultado_incrementador():
    """
    Lee los 4 bits de salida del circuito incrementador
    Retorna: Lista de 4 valores [bit0, bit1, bit2, bit3]
    """
    return [
        LED_RESULTADO0.value(),  # Bit 0 de salida
        LED_RESULTADO1.value(),  # Bit 1 de salida
        LED_RESULTADO2.value(),  # Bit 2 de salida
        LED_RESULTADO3.value()   # Bit 3 de salida
    ]

def binario_a_decimal(bits):
    """
    Convierte una lista de 4 bits a su valor decimal
    bits: [bit0, bit1, bit2, bit3] donde bit0 es el LSB
    Ejemplo: [1,0,1,0] = 1 + 0*2 + 1*4 + 0*8 = 5
    """
    return bits[0] + (bits[1] * 2) + (bits[2] * 4) + (bits[3] * 8)

def calcular_incremento_en_5(caracter):
    """
    Funcion principal del incrementador:
    1. Obtiene el codigo ASCII del caracter
    2. Extrae los 4 bits menos significativos
    3. Suma 5 al valor
    4. Retorna los bits de entrada y salida
    
    Retorna: (bits_entrada, bits_salida, valor_entrada, valor_salida)
    """
    ascii_code = ord(caracter)  # Ej: 'A' = 65
    
    # Extraer los 4 bits menos significativos del ASCII
    # Ej: 65 = 0b01000001, los 4 bits menos significativos son 0001
    bits_entrada = [
        (ascii_code >> 0) & 1,  # Bit 0 (LSB)
        (ascii_code >> 1) & 1,  # Bit 1
        (ascii_code >> 2) & 1,  # Bit 2
        (ascii_code >> 3) & 1   # Bit 3
    ]
    
    valor_entrada = binario_a_decimal(bits_entrada)  # 'A' = 1
    valor_salida = valor_entrada + 5                 # 1 + 5 = 6
    
    # Si el resultado es mayor a 15, usar solo 4 bits (mod 16)
    # Ej: 11 + 5 = 16 -> 0 (porque solo tenemos 4 bits)
    if valor_salida > 15:
        valor_salida = valor_salida & 0b1111  # Mantener solo 4 bits
    
    # Convertir el valor de salida a 4 bits
    bits_salida = [
        (valor_salida >> 0) & 1,  # Bit 0 (LSB)
        (valor_salida >> 1) & 1,  # Bit 1
        (valor_salida >> 2) & 1,  # Bit 2
        (valor_salida >> 3) & 1   # Bit 3 (MSB)
    ]
    
    return bits_entrada, bits_salida, valor_entrada, valor_salida

# ============================================================
# FUNCION PRINCIPAL
# ============================================================

def iniciar_sistema():
    """Bucle principal del sistema"""
    
    # Crear la red WiFi
    ip = crear_red_wifi()
    
    # Crear socket UDP para recibir comandos de VS Code
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind((ip, 5005))          # Puerto 5005 para recibir
    udp.setblocking(False)        # No bloquear si no hay datos
    
    # Variables de estado
    pc_ip = ""                     # IP de la PC
    modo_ascii_activado = False    # Switch del modo ASCII
    codigo_acumulado = ""          # Codigo Morse acumulado (ej: ".-")
    ultima_vez_suelto = time.time()
    procesado = True
    boton_estado_anterior = 1      # 1 = no presionado, 0 = presionado
    
    print("SISTEMA LISTO")
    print("Conectate a la red WiFi: Pico_Stranger")
    print("Esperando comandos...")
    
    while True:
        # ============================================================
        # PARTE 1: RECIBIR COMANDOS DE VS CODE POR UDP
        # ============================================================
        try:
            data, addr = udp.recvfrom(1024)
            pc_ip = addr[0]
            msg = data.decode('utf-8').strip().upper()
            
            if msg == "ASCII_ON":
                modo_ascii_activado = True
                print("ASCII ACTIVADO")
            elif msg == "ASCII_OFF":
                modo_ascii_activado = False
                print("ASCII DESACTIVADO")
                apagar_todo()
                enviar_bits_al_incrementador([0, 0, 0, 0])
        except:
            pass  # No hay datos, continuar
        
        # ============================================================
        # PARTE 2: DETECTAR EL BOTON PARA CODIGO MORSE
        # ============================================================
        estado_boton = BOTON.value()
        
        # Cuando el boton se presiona (borde de bajada: 1 -> 0)
        if estado_boton == 0 and boton_estado_anterior == 1:
            BUZZER.freq(800)
            BUZZER.duty_u16(32768)   # 50% de volumen
            inicio_presion = time.time()
            
        # Cuando el boton se suelta (borde de subida: 0 -> 1)
        elif estado_boton == 1 and boton_estado_anterior == 0:
            BUZZER.duty_u16(0)       # Apagar el buzzer
            
            duracion = time.time() - inicio_presion
            if duracion >= 1.5:
                codigo_acumulado += "-"   # Presion larga = raya
            else:
                codigo_acumulado += "."   # Presion corta = punto
            
            ultima_vez_suelto = time.time()
            procesado = False
            
        boton_estado_anterior = estado_boton
        
        # ============================================================
        # PARTE 3: PROCESAR EL CODIGO MORSE
        # ============================================================
        if not procesado and estado_boton == 1:
            silencio = time.time() - ultima_vez_suelto
            
            # Si hay silencio de 2-4.5 segundos, procesar la letra
            if 2.0 <= silencio < 4.5:
                letra = MORSE_MAP.get(codigo_acumulado, "")
                
                if letra:
                    print("Letra: " + letra)
                    mostrar_caracter(letra, 600)
                    
                    # ============================================================
                    # PARTE 4: INCREMENTADOR EN 5 (SOLO SI ASCII ESTA ACTIVADO)
                    # ============================================================
                    if modo_ascii_activado:
                        # Calcular el incremento en 5
                        bits_entrada, bits_salida, valor_entrada, valor_salida = calcular_incremento_en_5(letra)
                        
                        # Enviar los bits al circuito fisico
                        enviar_bits_al_incrementador(bits_entrada)
                        
                        # Esperar a que el circuito responda
                        time.sleep_ms(50)
                        
                        # Leer el resultado del circuito
                        resultado_leido = leer_resultado_incrementador()
                        
                        # Crear mensaje para VS Code
                        # Formato: ASCII|letra|valor_entrada|bits_entrada|valor_salida|bits_salida|resultado
                        info = "ASCII|" + letra + "|" + str(valor_entrada) + "|"
                        info += str(bits_entrada[3]) + str(bits_entrada[2]) + str(bits_entrada[1]) + str(bits_entrada[0]) + "|"
                        info += str(valor_salida) + "|"
                        info += str(bits_salida[3]) + str(bits_salida[2]) + str(bits_salida[1]) + str(bits_salida[0]) + "|"
                        info += str(resultado_leido[3]) + str(resultado_leido[2]) + str(resultado_leido[1]) + str(resultado_leido[0])
                        
                        # Enviar informacion a VS Code
                        try:
                            udp.sendto(info.encode(), (pc_ip, 5006))
                        except:
                            pass
                
                # Resetear para la siguiente letra
                codigo_acumulado = ""
                procesado = True
                
            # Si hay silencio de 5+ segundos, resetear todo
            elif silencio >= 5.0:
                apagar_todo()
                codigo_acumulado = ""
                procesado = True
        
        # Pequeña pausa para no saturar el CPU
        time.sleep(0.05)

# ============================================================
# PUNTO DE ENTRADA
# ============================================================

if __name__ == '__main__':
    apagar_todo()
    iniciar_sistema()