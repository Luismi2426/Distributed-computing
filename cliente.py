# -*- coding: utf-8 -*-
"""
PROGRAMACION PARALELA 14/15

@author: LUIS MIGUEL BARBERO JUVERA

CLIENTE
"""

from multiprocessing import Process
from multiprocessing import Queue
from multiprocessing.connection import Client
from multiprocessing.connection import AuthenticationError

from Tkinter import *
import tkFont

#Cuenta la cantidad de 0s y 1s en el tablero y muestra quien es el ganador
def winner (gameboard):
    team0 = 0
    team1 = 0
    for i in range(len(gameboard)):
        if gameboard[i] == 0:
            team0 = team0 + 1
        else:
            team1 = team1 + 1 
    if team0 > team1:
        winner = 0
    elif team1 > team0:
        winner = 1
    else:
        winner = 2
    return winner
    
#Inserta el tablero en la cola 
def show_board(window_queue, gameboard):
    window_queue.put(('board',gameboard))

#Inserta el mensaje para mostrar en la cola 
def show_answer(window_queue, message):
    window_queue.put(('message',message))

#Saca el movimiento de la cola input 
def read_movement(input_queue):
    return eval(input_queue.get())

#Interfaz grafica
def graphical_interface(board_queue, team, input_queue, dim_rows, dim_columns):
    
    #Creamos la ventana
    root = Tk()
    root.title("Luismi Barbero")
    root.resizable(0, 0)
    
    #Colores de fondo
    if team == 0:
        bg_colour = 'light yellow'
    else:
        bg_colour = 'alice blue'
    lb_colour = 'white'
    
    #Tipos de fuente
    title_font = tkFont.Font(size='18', slant='italic')
    board_font = tkFont.Font(size='14')
    
    frame = Frame(root, bg=bg_colour)
    frame.pack()
    
    #Cuadros para mostrar tablero
    team_label = Label(frame, text="Equipo "+str(team), font=title_font, bg=bg_colour, height=2)
    team_label.pack()
    gameboard = []
    for i in range(dim_rows):
        gameboard.append(Entry(frame, width=35, font=board_font, justify=CENTER, bg=lb_colour, bd=0))
        gameboard[i].pack()
    
    #Cuadro para mensajes tipo: juagada valida...
    message_label = Label(frame, text="Mensaje", font=title_font, bg=bg_colour, height=2)
    message_label.pack()
    message = Entry(frame, width=35, justify = CENTER, bg=lb_colour,font=board_font)
    message.pack()
    
    #Cuadro para poner el movimiento
    input_label = Label(frame, text="Movimiento", font=title_font, bg=bg_colour,height=2)
    input_label.pack()
    input_value = StringVar()
    input_data = Entry(frame, width=10,font=board_font, justify=CENTER, textvariable=input_value, bg=lb_colour)
    input_data.pack()
    
    #Boton para enviar movimiento (se introduce en la cola de movimientos)
    def press_button():
            input_queue.put(input_data.get())
            
    input_button = Button(frame, text="Enviar", command=press_button, activebackground='sky blue', bg='light cyan')
    input_button.pack()

    try:
        while 1:
            if not board_queue.empty():
                s = board_queue.get()
                print "Estado:", s
                if s[0] == 'board':
                    for i in range(dim_rows):
                        gameboard[i].delete(0,END)
                        gameboard[i].insert(0,s[1][i*dim_columns:dim_columns*(i+1)])
                elif s[0] == 'message':
                    message.delete(0,END)
                    message.insert(0,s[1])
            root.update() 
    except TclError:
        pass 


#Excepcion si no se introduce el password correcto
try:
    #Inicia el cliente
    print "Conectando al servidor..."
    conn = Client(address=('localhost', 6000), authkey='secret password')
    
    #Recibe y ordena los datos del juego
    game = conn.recv()
    team = game[0]
    dim_rows = game[1][0]
    dim_columns = game[1][1]
    gameboard = game[1][2]
    
    #Crea dos colas: Datos que mostrar y Movimientos que queremos enviar
    window_queue = Queue()
    input_queue = Queue()
    
    #Proceso
    gameboard_window = Process(target=graphical_interface, args=(window_queue,team,input_queue, dim_rows, dim_columns))
    gameboard_window.start()
    
    #Introduce en la cola el tablero que se mostrara por pantalla
    show_board(window_queue, gameboard)
    
    #Si el tablero no esta completo
    tableroCompleto = False
    while not tableroCompleto: 
        
        try:
            
            #Saca el movimiento de la cola y se envia al servidor
            movement = read_movement(input_queue)
            conn.send((team, movement))
            print "Movimiento:", movement
            
            done = False
            while not done:
                
                #Recibe la situacion del movimiento: 0, 1, 2
                answer = conn.recv()
                actual = answer[0]
                gameboard = answer[1][2]
                print "Respuesta: ", answer
                
                #0: Jugada valida
                if actual == 0:
                    message = "Jugada valida"
                    show_answer(window_queue,message)
                    show_board(window_queue, gameboard)
                    done = True
                    
                #1: Jugada no valida
                elif actual == 1:
                    message = "Jugada no valida"
                    show_answer(window_queue,message)
                    show_board(window_queue, gameboard)
                    done = True
                    
                #2: Esperando
                elif actual == 2:
                    message = "Espera"
                    show_answer(window_queue,message)
                    
                #3: Tablero completo
                elif actual == 3:
                    winner_team = winner(gameboard)
                    message = "Tablero completo"
                    show_answer(window_queue,message)
                    show_board(window_queue, gameboard)
                    
                    if winner_team == 2:
                        message = "Ha sido un empate"
                    else:
                        message = "Ha ganado el equipo "+str(winner_team)
                        
                    show_answer(window_queue,message)
                    done = True
                    tableroCompleto = True    
        
        #Excepcion cuando se introduce algo que no es un int o (int,int,...)
        except (SyntaxError, NameError):
            message = "No se ha introducido una tupla de int"
            show_answer(window_queue,message)
        
        #Excepcion si hay algun error en la conexion con el servidor
        except:
            message = "Error en la conexion con el servidor"
            show_answer(window_queue,message)
            done = True
            tableroCompleto = True
            

    #Cierra la interfaz
    #gameboard_window.terminate()    
    
except AuthenticationError:
    print "El cliente no ha puesto correctamente el authkey"
  
print "Saliendo..."
conn.close()
