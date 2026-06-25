import tkinter as tk
import random
import socket
import threading
import time

# ============================================================
# CONFIGURACION DE RED
# ============================================================
# La PC se conecta a la red WiFi de la Pico (Pico_Stranger)
# La Pico tiene IP fija: 192.168.4.1
# ============================================================

PICO_IP = "192.168.4.1"          # IP de la Pico en modo Access Point
PUERTO_ENVIO = 5005              # Puerto para enviar comandos a la Pico
PUERTO_ESCUCHA = 5006            # Puerto para recibir datos de la Pico
LISTA_FRASES = []                # Lista de frases para el modo juego

def enviar_comando(msg):
    """
    Envia un comando a la Pico por UDP
    msg: Comando a enviar (ej: "ASCII_ON", "ASCII_OFF", "A", etc.)
    Retorna: True si se envio correctamente, False si hubo error
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(msg.encode('utf-8'), (PICO_IP, PUERTO_ENVIO))
        s.close()
        return True
    except:
        return False

# ============================================================
# CLASE PRINCIPAL DE LA INTERFAZ
# ============================================================

class InterfazStrangerTec:
    """
    Interfaz grafica para controlar el sistema StrangerTec
    Permite:
    - Modo Prueba: Probar el boton de la maqueta
    - Modo Prueba 2: Enviar palabras aleatorias a la maqueta
    - Transmision Simple: Juego de adivinanza de frases
    - Modo ASCII: Incrementador en 5 con codigo Morse
    """
    
    def __init__(self):
        """Constructor - Inicializa la ventana y los componentes"""
        # Crear la ventana principal
        self.root = tk.Tk()
        self.root.title("Stranger Tec - Sistema Unificado")
        self.root.geometry("700x750")
        self.root.configure(bg="#0a0a0a")
        
        # Contenedor principal
        self.container = tk.Frame(self.root, bg="#0a0a0a")
        self.container.pack(expand=True, fill="both")
        
        # Variables de estado
        self.lbl_feedback = None      # Etiqueta para feedback general
        self.lbl_ascii_info = None    # Etiqueta para informacion del ASCII
        self.modo_actual = "MENU"     # Modo actual de la interfaz
        
        # Iniciar el hilo que escucha los mensajes de la Pico
        self.iniciar_hilo_escucha()
        
        # Mostrar el menu principal
        self.menu_principal()
    
    # ============================================================
    # COMUNICACION CON LA PICO (UDP)
    # ============================================================
    
    def iniciar_hilo_escucha(self):
        """
        Inicia un hilo en segundo plano que escucha los mensajes UDP
        de la Pico en el puerto 5006
        """
        def hilo_escucha():
            try:
                # Crear socket UDP para recibir datos
                udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                udp.bind(('0.0.0.0', PUERTO_ESCUCHA))
                
                while True:
                    try:
                        # Esperar datos de la Pico
                        data, addr = udp.recvfrom(1024)
                        msg = data.decode('utf-8').upper()
                        
                        # ============================================================
                        # PROCESAR MENSAJES ASCII DEL INCREMENTADOR
                        # ============================================================
                        # Formato: ASCII|letra|valor_entrada|bits_entrada|valor_salida|bits_salida|resultado
                        # Ejemplo: ASCII|A|1|0001|6|0110|0110
                        # ============================================================
                        
                        if msg.startswith("ASCII|"):
                            partes = msg.split("|")
                            if len(partes) == 8:
                                # Extraer los datos del mensaje
                                caracter = partes[1]
                                valor_entrada = partes[2]
                                bits_entrada = partes[3]    # Formato: MSB a LSB
                                valor_salida = partes[4]
                                bits_salida = partes[5]     # Formato: MSB a LSB
                                resultado_leido = partes[6] # Formato: MSB a LSB
                                
                                # Actualizar la interfaz con la informacion
                                if self.lbl_ascii_info and self.lbl_ascii_info.winfo_exists():
                                    # Construir el texto a mostrar
                                    texto = "Caracter: " + caracter + "\n"
                                    texto += "ASCII: " + str(ord(caracter)) + "\n"
                                    texto += "Bits entrada: " + bits_entrada + " = " + valor_entrada + "\n"
                                    texto += "+5 = " + valor_salida + "\n"
                                    texto += "Bits salida: " + bits_salida + "\n"
                                    texto += "LEDs leidos: " + resultado_leido
                                    
                                    # Verificar si el resultado coincide con lo esperado
                                    if bits_salida == resultado_leido:
                                        texto += "\n\nESTADO: CORRECTO - Los LEDs coinciden"
                                        color = "#00ff00"  # Verde
                                    else:
                                        texto += "\n\nESTADO: ERROR - Los LEDs NO coinciden"
                                        color = "#ff0000"  # Rojo
                                    
                                    self.lbl_ascii_info.config(text=texto, fg=color)
                    except:
                        pass  # Ignorar errores y continuar escuchando
            except:
                pass  # Si falla el socket, no hacer nada
        
        # Crear y lanzar el hilo como demonio (se cierra al cerrar la app)
        thread = threading.Thread(target=hilo_escucha, daemon=True)
        thread.start()
    
    # ============================================================
    # FUNCIONES DE INTERFAZ
    # ============================================================
    
    def limpiar_pantalla(self):
        """Elimina todos los widgets del contenedor principal"""
        for w in self.container.winfo_children():
            w.destroy()
    
    # ============================================================
    # MENU PRINCIPAL
    # ============================================================
    
    def menu_principal(self):
        """Muestra el menu principal con los botones de navegacion"""
        self.limpiar_pantalla()
        self.modo_actual = "MENU"
        enviar_comando("ASCII_OFF")  # Asegurar que ASCII esta desactivado
        
        # Titulo
        tk.Label(self.container, text="STRANGER TEC", 
                font=("Courier", 35, "bold"), 
                bg="#0a0a0a", fg="#ff0000").pack(pady=80)
        
        # Indicador de conexion
        tk.Label(self.container, text="Conectado a Pico (192.168.4.1)", 
                font=("Arial", 10), 
                bg="#0a0a0a", fg="#00ff00").pack(pady=5)
        
        # Botones del menu
        tk.Button(self.container, text="PRUEBA", 
                 font=("Arial", 14), width=20, pady=10,
                 command=self.ventana_prueba,
                 bg="#333", fg="white").pack(pady=10)
        
        tk.Button(self.container, text="PRUEBA 2", 
                 font=("Arial", 14), width=20, pady=10,
                 command=self.ventana_prueba_2,
                 bg="#333", fg="white").pack(pady=10)
        
        tk.Button(self.container, text="TRANSMISION SIMPLE", 
                 font=("Arial", 14), width=20, pady=10,
                 command=self.ventana_transmision,
                 bg="#333", fg="white").pack(pady=10)
        
        tk.Button(self.container, text="ASCII", 
                 font=("Arial", 14), width=20, pady=10,
                 command=self.ventana_ascii,
                 bg="#333", fg="white").pack(pady=10)
    
    # ============================================================
    # VENTANA: MODO PRUEBA
    # ============================================================
    
    def ventana_prueba(self):
        """Modo prueba - Permite probar el boton de la maqueta"""
        self.limpiar_pantalla()
        self.modo_actual = "PRUEBA"
        enviar_comando("ASCII_OFF")
        
        tk.Label(self.container, text="MODO PRUEBA", 
                font=("Courier", 20), 
                bg="#0a0a0a", fg="#00ff00").pack(pady=40)
        
        self.lbl_feedback = tk.Label(self.container, 
                                    text="Presiona el boton en la maqueta",
                                    font=("Arial", 12),
                                    bg="#0a0a0a", fg="white")
        self.lbl_feedback.pack(pady=20)
        
        tk.Button(self.container, text="VOLVER", 
                 command=self.menu_principal,
                 bg="#444", fg="white", width=15).pack(pady=20)
    
    # ============================================================
    # VENTANA: MODO PRUEBA 2
    # ============================================================
    
    def ventana_prueba_2(self):
        """Modo prueba 2 - Envia palabras aleatorias a la maqueta"""
        self.limpiar_pantalla()
        self.modo_actual = "PRUEBA2"
        enviar_comando("ASCII_OFF")
        
        def enviar_p2():
            """Envia una frase aleatoria a la maqueta con el comando P2:"""
            if LISTA_FRASES:
                frase = random.choice(LISTA_FRASES)
                enviar_comando("P2:" + frase)
        
        def agregar_frase():
            """Agrega una frase a la lista"""
            frase = entry.get().strip().upper()
            if frase and len(LISTA_FRASES) < 10:
                LISTA_FRASES.append(frase)
                entry.delete(0, tk.END)
                actualizar_lista()
        
        def actualizar_lista():
            """Actualiza la visualizacion de la lista de frases"""
            txt = ""
            for i, f in enumerate(LISTA_FRASES):
                txt += str(i+1) + ". " + f + "\n"
            if lbl_lista:
                lbl_lista.config(text=txt)
        
        tk.Label(self.container, text="MODO PRUEBA 2", 
                font=("Courier", 20), 
                bg="#0a0a0a", fg="cyan").pack(pady=40)
        
        # Campo para agregar frases
        frame_input = tk.Frame(self.container, bg="#0a0a0a")
        frame_input.pack(pady=10)
        
        entry = tk.Entry(frame_input, font=("Arial", 12), width=20)
        entry.pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame_input, text="AGREGAR", 
                 command=agregar_frase,
                 bg="#444", fg="white").pack(side=tk.LEFT)
        
        # Lista de frases
        frame_lista = tk.LabelFrame(self.container, text=" FRASES ", 
                                   font=("Arial", 10, "bold"),
                                   bg="#0a0a0a", fg="white", 
                                   padx=20, pady=10)
        frame_lista.pack(pady=10, padx=40, fill="both")
        
        lbl_lista = tk.Label(frame_lista, text="", 
                            font=("Arial", 11), 
                            bg="#0a0a0a", fg="#00ff00", justify="left")
        lbl_lista.pack()
        
        # Botones
        tk.Button(self.container, text="ENVIAR ALEATORIA", 
                 command=enviar_p2,
                 font=("Arial", 12), bg="#005", fg="white",
                 width=20, pady=10).pack(pady=10)
        
        tk.Button(self.container, text="VOLVER", 
                 command=self.menu_principal,
                 bg="#444", fg="white", width=15).pack(pady=20)
        
        actualizar_lista()
    
    # ============================================================
    # VENTANA: TRANSMISION SIMPLE (JUEGO)
    # ============================================================
    
    def ventana_transmision(self):
        """Modo juego - Adivinar frases usando codigo Morse"""
        self.limpiar_pantalla()
        self.modo_actual = "JUEGO"
        enviar_comando("ASCII_OFF")
        
        tk.Label(self.container, text="GESTION DE FRASES", 
                font=("Courier New", 20, "bold"),
                bg="#0a0a0a", fg="#ff0000").pack(pady=20)
        
        # Campo para agregar frases
        frame_input = tk.Frame(self.container, bg="#0a0a0a")
        frame_input.pack(pady=10)
        
        entry = tk.Entry(frame_input, font=("Arial", 12), width=25)
        entry.pack(side=tk.LEFT, padx=10)
        
        def agregar():
            """Agrega una frase a la lista del juego"""
            f = entry.get().strip().upper()
            if f and len(LISTA_FRASES) < 10:
                LISTA_FRASES.append(f)
                entry.delete(0, tk.END)
                actualizar()
        
        def actualizar():
            """Actualiza la lista visual de frases"""
            txt = ""
            for i, f in enumerate(LISTA_FRASES):
                txt += str(i+1) + ". " + f + "\n"
            lbl_lista.config(text=txt)
        
        def jugar():
            """Selecciona una frase aleatoria y la envia a la maqueta"""
            if LISTA_FRASES:
                p = random.choice(LISTA_FRASES)
                self.lbl_feedback.config(text="RETO: " + p, fg="cyan")
                enviar_comando(p)
        
        def validar():
            """Solicita a la Pico validar la frase ingresada por el jugador"""
            enviar_comando("VALIDAR")
        
        # Boton agregar
        tk.Button(frame_input, text="AGREGAR", 
                 command=agregar,
                 bg="#444", fg="white").pack(side=tk.LEFT)
        
        # Lista de frases
        frame_lista = tk.LabelFrame(self.container, text=" LISTA ", 
                                   font=("Arial", 10, "bold"),
                                   bg="#0a0a0a", fg="white", 
                                   padx=20, pady=10)
        frame_lista.pack(pady=10, padx=40, fill="both")
        
        lbl_lista = tk.Label(frame_lista, text="", 
                            font=("Arial", 11), 
                            bg="#0a0a0a", fg="#00ff00", justify="left")
        lbl_lista.pack()
        
        # Feedback
        self.lbl_feedback = tk.Label(self.container, 
                                    text="Haz clic en JUGAR",
                                    font=("Courier", 16, "bold"),
                                    bg="#111", fg="yellow", pady=15)
        self.lbl_feedback.pack(pady=10, fill="x")
        
        # Botones de control
        tk.Button(self.container, text="JUGAR", 
                 command=jugar,
                 bg="#b00", fg="white",
                 font=("Arial", 12, "bold"),
                 pady=10, padx=30).pack(pady=5)
        
        tk.Button(self.container, text="VALIDAR", 
                 command=validar,
                 bg="#008000", fg="white",
                 font=("Arial", 12, "bold"),
                 pady=10, padx=30).pack(pady=5)
        
        tk.Button(self.container, text="VOLVER AL INICIO", 
                 command=self.menu_principal,
                 bg="#0a0a0a", fg="gray",
                 font=("Arial", 9, "underline"),
                 borderwidth=0).pack(pady=10)
        
        actualizar()
    
    # ============================================================
    # VENTANA: MODO ASCII (INCREMENTADOR EN 5)
    # ============================================================
    
    def ventana_ascii(self):
        """
        Modo ASCII - Activa el incrementador en 5
        Al estar en este modo, las letras en Morse activan el incrementador
        """
        self.limpiar_pantalla()
        self.modo_actual = "ASCII"
        
        # Activar el modo ASCII en la Pico
        enviar_comando("ASCII_ON")
        
        # Titulo
        tk.Label(self.container, text="MODO ASCII - INCREMENTADOR EN 5", 
                font=("Courier", 16, "bold"), 
                bg="#0a0a0a", fg="#ff0000").pack(pady=10)
        
        # Indicador de estado
        self.lbl_estado_ascii = tk.Label(self.container, 
                                        text="SWITCH ACTIVADO - Esperando entrada Morse",
                                        font=("Arial", 12),
                                        bg="#0a0a0a", fg="#00ff00")
        self.lbl_estado_ascii.pack(pady=5)
        
        # Panel de informacion del incrementador
        frame_info = tk.LabelFrame(self.container, text=" INFORMACION DEL INCREMENTADOR ", 
                                  font=("Arial", 10, "bold"),
                                  bg="#0a0a0a", fg="white", 
                                  padx=20, pady=10)
        frame_info.pack(pady=10, padx=20, fill="x")
        
        self.lbl_ascii_info = tk.Label(frame_info, 
                                      text="Esperando letra...\nPresiona el boton en Morse",
                                      font=("Courier", 11),
                                      bg="#0a0a0a", fg="#ffff00",
                                      justify="left")
        self.lbl_ascii_info.pack(pady=10)
        
        # Separador
        tk.Frame(self.container, height=2, bg="#333").pack(fill="x", pady=10)
        
        # Tabla de caracteres validos
        tk.Label(self.container, text="CARACTERES VALIDOS (A-Z, 0-9)", 
                font=("Arial", 10, "bold"),
                bg="#0a0a0a", fg="#888").pack(pady=5)
        
        frame_tabla = tk.Frame(self.container, bg="#0a0a0a")
        frame_tabla.pack(pady=5, padx=20, fill="x")
        
        tabla_texto = tk.Text(frame_tabla, font=("Courier", 9), 
                             bg="#111", fg="#00ff00", 
                             height=4, width=60)
        tabla_texto.pack(side=tk.LEFT, fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(frame_tabla, command=tabla_texto.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        tabla_texto.config(yscrollcommand=scrollbar.set)
        
        # Generar tabla de caracteres con sus codigos ASCII
        tabla = ""
        fila = ""
        for i in range(26):
            letra = chr(65 + i)
            fila += letra + ":" + str(ord(letra)) + "  "
            if (i + 1) % 8 == 0:
                tabla += fila + "\n"
                fila = ""
        tabla += fila + "\n"
        
        fila = ""
        for i in range(10):
            num = str(i)
            fila += num + ":" + str(ord(num)) + "  "
            if (i + 1) % 8 == 0:
                tabla += fila + "\n"
                fila = ""
        tabla += fila
        
        tabla_texto.insert("1.0", tabla)
        tabla_texto.config(state="disabled")  # Solo lectura
        
        # Feedback
        self.lbl_feedback = tk.Label(self.container, 
                                    text="Usa el boton de la maqueta para enviar letras en Morse",
                                    font=("Arial", 10),
                                    bg="#0a0a0a", fg="yellow")
        self.lbl_feedback.pack(pady=10)
        
        # Boton para salir
        def salir_ascii():
            """Desactiva el modo ASCII y vuelve al menu"""
            enviar_comando("ASCII_OFF")
            self.menu_principal()
        
        tk.Button(self.container, text="SALIR DE ASCII", 
                 command=salir_ascii,
                 bg="#b00", fg="white",
                 font=("Arial", 12, "bold"),
                 pady=10, padx=30).pack(pady=15)
    
    # ============================================================
    # PUNTO DE ENTRADA DE LA APLICACION
    # ============================================================
    
    def ejecutar(self):
        """Inicia el bucle principal de la interfaz grafica"""
        self.root.mainloop()

# ============================================================
# EJECUTAR LA APLICACION
# ============================================================

if __name__ == "__main__":
    app = InterfazStrangerTec()
    app.ejecutar()