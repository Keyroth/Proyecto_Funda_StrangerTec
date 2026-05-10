import tkinter as tk
import random
import socket
import threading

# --- CONFIGURACIÓN ---
PICO_IP = "172.18.236.76" 
PUERTO_ENVIO = 5005
PUERTO_ESCUCHA = 5006
LISTA_FRASES = []

def enviar_comando(msg):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(msg.encode('utf-8'), (PICO_IP, PUERTO_ENVIO))
    except: pass

def mostrar_interfaz():
    root = tk.Tk()
    root.title("Stranger Tec - Sistema Unificado")
    root.geometry("600x700")
    root.configure(bg="#0a0a0a")

    container = tk.Frame(root, bg="#0a0a0a")
    container.pack(expand=True, fill="both")

    global lbl_feedback
    lbl_feedback = None

    def hilo_escucha():
        global lbl_feedback
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            udp.bind(('0.0.0.0', PUERTO_ESCUCHA))
        except: return
        
        while True:
            try:
                data, addr = udp.recvfrom(1024)
                msg = data.decode('utf-8').upper()
                if lbl_feedback and lbl_feedback.winfo_exists():
                    color = "#00ff00" if "100" in msg or "EXITO" in msg else "#ffaa00"
                    if "0 PUNTOS" in msg: color = "#ff0000"
                    lbl_feedback.config(text=msg, fg=color)
            except: pass

    threading.Thread(target=hilo_escucha, daemon=True).start()

    def limpiar_pantalla():
        for w in container.winfo_children(): w.destroy()

    def menu_principal():
        limpiar_pantalla()
        tk.Label(container, text="STRANGER TEC", font=("Courier", 35, "bold"), bg="#0a0a0a", fg="#ff0000").pack(pady=80)
        tk.Button(container, text="PRUEBA", font=("Arial", 14), width=20, pady=10, command=ventana_prueba).pack(pady=10)
        tk.Button(container, text="PRUEBA 2", font=("Arial", 14), width=20, pady=10, command=ventana_prueba_2).pack(pady=10)
        tk.Button(container, text="TRANSMISIÓN SIMPLE", font=("Arial", 14), width=20, pady=10, command=ventana_transmision).pack(pady=10)

    def ventana_prueba():
        global lbl_feedback
        limpiar_pantalla()
        enviar_comando("MODO_PRUEBA")
        tk.Label(container, text="MODO PRUEBA 1", font=("Courier", 20), bg="#0a0a0a", fg="#00ff00").pack(pady=40)
        lbl_feedback = tk.Label(container, text="Prueba el botón en la maqueta", font=("Arial", 12), bg="#0a0a0a", fg="white")
        lbl_feedback.pack(pady=20)
        tk.Button(container, text="VOLVER", command=menu_principal, bg="#444", fg="white", width=15).pack(pady=20)

    def ventana_prueba_2():
        limpiar_pantalla()
        tk.Label(container, text="MODO PRUEBA 2", font=("Courier", 20), bg="#0a0a0a", fg="cyan").pack(pady=40)
        def enviar_p2():
            if LISTA_FRASES:
                enviar_comando(f"P2:{random.choice(LISTA_FRASES)}")
        tk.Button(container, text="ENVIAR ALEATORIA", command=enviar_p2, font=("Arial", 12), bg="#005", fg="white", width=20, pady=10).pack(pady=10)
        tk.Button(container, text="VOLVER", command=menu_principal, bg="#444", fg="white", width=15).pack(pady=20)

    def ventana_transmision():
        global lbl_feedback
        limpiar_pantalla()
        enviar_comando("MODO_JUEGO")
        tk.Label(container, text="GESTIÓN DE FRASES", font=("Courier New", 20, "bold"), bg="#0a0a0a", fg="#ff0000").pack(pady=20)
        
        frame_input = tk.Frame(container, bg="#0a0a0a")
        frame_input.pack(pady=10)
        entry = tk.Entry(frame_input, font=("Arial", 12), width=25)
        entry.pack(side=tk.LEFT, padx=10)

        frame_lista = tk.LabelFrame(container, text=" LISTA ", font=("Arial", 10, "bold"), bg="#0a0a0a", fg="white", padx=20, pady=10)
        frame_lista.pack(pady=10, padx=40, fill="both")
        lbl_lista = tk.Label(frame_lista, text="", font=("Arial", 11), bg="#0a0a0a", fg="#00ff00", justify="left")
        lbl_lista.pack()

        lbl_feedback = tk.Label(container, text="Haz clic en JUGAR", font=("Courier", 16, "bold"), bg="#111", fg="yellow", pady=15)
        lbl_feedback.pack(pady=10, fill="x")

        def refrescar():
            txt = "\n".join([f"{i+1}. {f}" for i,f in enumerate(LISTA_FRASES)])
            lbl_lista.config(text=txt)

        def add():
            f = entry.get().strip().upper()
            if f and len(LISTA_FRASES) < 10:
                LISTA_FRASES.append(f); refrescar(); entry.delete(0, tk.END)

        def jugar():
            if LISTA_FRASES:
                p = random.choice(LISTA_FRASES)
                lbl_feedback.config(text=f"RETO: {p}", fg="cyan")
                enviar_comando(p)

        def validar():
            enviar_comando("VALIDAR")

        tk.Button(frame_input, text="AGREGAR", command=add, bg="#444", fg="white").pack(side=tk.LEFT)
        tk.Button(container, text="JUGAR", command=jugar, bg="#b00", fg="white", font=("Arial", 12, "bold"), pady=10, padx=30).pack(pady=5)
        tk.Button(container, text="VALIDAR", command=validar, bg="#008000", fg="white", font=("Arial", 12, "bold"), pady=10, padx=30).pack(pady=5)
        tk.Button(container, text="VOLVER AL INICIO", command=menu_principal, bg="#0a0a0a", fg="gray", font=("Arial", 9, "underline"), borderwidth=0).pack(pady=10)
        refrescar()

    menu_principal()
    root.mainloop()

if __name__ == "__main__":
    mostrar_interfaz()
