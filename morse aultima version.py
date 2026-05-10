import network
import socket
from machine import Pin, PWM
import time

# --- CONFIGURACIÓN DE RED ---
SSID = "Keyroth"
PASSWORD = "keyroth22"

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        time.sleep(1)
    print("Conectado. IP:", wlan.ifconfig()[0])
    return wlan.ifconfig()[0]

# --- CONFIGURACIÓN HARDWARE ---
SER   = Pin(27, Pin.OUT)
CLK   = Pin(26, Pin.OUT)
FILA1 = Pin(13, Pin.OUT)
FILA2 = Pin(14, Pin.OUT)
FILA3 = Pin(15, Pin.OUT)
BOTON = Pin(16, Pin.IN, Pin.PULL_UP)
BUZZER = PWM(Pin(28))
BUZZER.duty_u16(0)

TABLA_LEDS = {
    'A':(1,1), 'C':(2,1), 'E':(3,1), 'G':(4,1), 'I':(5,1), 'K':(6,1), 'M':(7,1), 'O':(8,1), 'Q':(9,1), 'S':(10,1), 'U':(11,1), 'W':(12,1), 'Y':(13,1),
    'B':(1,2), 'D':(2,2), 'F':(3,2), 'H':(4,2), 'J':(5,2), 'L':(6,2), 'N':(7,2), 'P':(8,2), 'R':(9,2), 'T':(10,2), 'V':(11,2), 'X':(12,2), 'Z':(13,2),
    '0':(1,3), '1':(2,3), '2':(3,3), '3':(4,3), '4':(5,3), '5':(6,3), '6':(7,3), '7':(8,3), '8':(9,3), '9':(10,3), ' ':(11,3), '-':(12,3), '+':(13,3)
}

MORSE_MAP = {
    '.-':'A', '-...':'B', '-.-.':'C', '-..':'D', '.':'E', '..-.':'F', '--.':'G', '....':'H', '..':'I', '.---':'J', '-.-':'K', '.-..':'L', '--':'M', '-.':'N', '---':'O', '.--.':'P', '--.-':'Q', '.-.':'R', '...':'S', '-':'T', '..-':'U', '...-':'V', '.--':'W', '-..-':'X', '-.--':'Y', '--..':'Z', 
    '.----':'1', '..---':'2', '...--':'3', '....-':'4', '.....':'5', '-....':'6', '--...':'7', '---..':'8', '----.':'9', '-----':'0','-....-':'-', '.-.-.':'+'
}

def enviar_16_bits(valor: int):
    for bit in range(15, -1, -1):
        SER.value((valor >> bit) & 1)
        CLK.high(); CLK.low()

def apagar_todo():
    FILA1.low(); FILA2.low(); FILA3.low()
    enviar_16_bits(0)

def mostrar_caracter(caracter, duracion_ms=600):
    ch = caracter.upper()
    if ch in TABLA_LEDS:
        col, fila = TABLA_LEDS[ch]
        apagar_todo()
        enviar_16_bits(1 << (col - 1))
        FILA1.value(fila == 1); FILA2.value(fila == 2); FILA3.value(fila == 3)
        if duracion_ms > 0:
            time.sleep_ms(duracion_ms)
            apagar_todo()

def calcular_puntos(objetivo, usuario):
    if not objetivo: return "SIN OBJETIVO"
    coincidencias = 0
    min_len = min(len(objetivo), len(usuario))
    for i in range(min_len):
        if objetivo[i] == usuario[i]:
            coincidencias += 1
    puntos = int((coincidencias / len(objetivo)) * 100)
    return f"{puntos} PUNTOS"

def iniciar_maqueta():
    ip = conectar_wifi()
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind((ip, 5005))
    udp.setblocking(False)

    modo = "JUEGO"
    codigo_acumulado = ""
    frase_usuario = ""
    palabra_objetivo = ""
    pc_ip = ""
    ultima_vez_suelto = time.time()
    procesado = True

    while True:
        try:
            data, addr = udp.recvfrom(1024)
            pc_ip = addr[0]
            msg = data.decode('utf-8').strip().upper()
            
            if msg == "MODO_PRUEBA":
                modo = "PRUEBA"
            elif msg == "MODO_JUEGO":
                modo = "JUEGO"
            elif msg == "VALIDAR":
                res = calcular_puntos(palabra_objetivo, frase_usuario)
                udp.sendto(res.encode(), (pc_ip, 5006))
                palabra_objetivo = ""
                frase_usuario = ""
            elif msg.startswith("P2:"):
                palabra = msg.replace("P2:", "")
                for letra in palabra:
                    mostrar_caracter(letra, 600)
                    time.sleep_ms(200)
            else:
                palabra_objetivo = msg
                frase_usuario = ""
                print("Reto:", palabra_objetivo)
        except: pass

        if modo in ["JUEGO", "PRUEBA"]:
            if BOTON.value() == 0:
                BUZZER.freq(800); BUZZER.duty_u16(32768)
                inicio = time.time()
                while BOTON.value() == 0: time.sleep(0.05)
                BUZZER.duty_u16(0)
                codigo_acumulado += "-" if (time.time() - inicio) >= 1.5 else "."
                ultima_vez_suelto = time.time()
                procesado = False

            if not procesado:
                silencio = time.time() - ultima_vez_suelto
                if 2.0 <= silencio < 4.5:
                    letra = MORSE_MAP.get(codigo_acumulado, "")
                    if letra:
                        mostrar_caracter(letra, 600)
                        frase_usuario += letra
                        print("Frase actual:", frase_usuario)
                    codigo_acumulado = ""
                    procesado = True
                elif silencio >= 5.0:
                    apagar_todo()
                    procesado = True
        
        time.sleep(0.1)

if __name__ == '__main__':
    apagar_todo()
    iniciar_maqueta()