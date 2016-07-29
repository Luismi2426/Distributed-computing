# -*- coding: utf-8 -*-
"""
PROGRAMACION PARALELA 14/15

@author: LUIS MIGUEL BARBERO JUVERA

SERVIDOR

Cuando un cliente se conecta al servidor, se le asigna un equipo.
Se envian al cliente el equipo al que pertenece y el tablero.

- Politica de acceso al tablero

El acceso al tablero esta gestionado mediante condiciones y un turno.
El turno nos indica a que equipo le toca jugar.
Cuando un jugador entra en el tablero no se permite que entre otro (acquire).
Si no es el turno del jugador, este pasa a esperar (wait) y se permite que
entre otro.
Si es el turno del jugador, se evalua la jugada y se realiza.
Una vez acabada la jugada, se cambia el turno y se permite nuevamente el acceso
al tablero (notify_all, release).
Cuando el tablero se completa, el turno deja de tener efecto.

-Ventajas

Hay igualdad entre ambos equipos ya que podran realizar el mismo numero de 
jugadas.

- Inconvenientes

Si hay un equipo (por ejemplo el [0]) en el que todos los jugadores han cerrado
la conexion y es su turno, el otro equipo ([1]) no podra mover hasta que se
conecten nuevos jugadores y hagan algun movimiento.

Dentro de un mismo equipo puede haber un jugador que sea el que siempre mueva.

Algunas posibles soluciones a estos inconvenientes podrian ser introducir 
condiciones que limiten en el tiempo los turnos o eliminar de los equipos a los
jugadores que se han desconectado.

"""

from multiprocessing.connection import Listener
from multiprocessing import Process
from multiprocessing.connection import AuthenticationError
from multiprocessing import Condition
from multiprocessing import Manager


#Imprime en la terminal el tablero
def print_board(dim_rows, dim_columns, gameboard):
    for i in range(dim_rows):
        print gameboard[i*dim_columns:dim_columns*(i+1)]

#Devuelve un boolean mostrando si el tablero se ha completado o no    
def complete(gameboard):
    i = 0
    cond = True
    while i < (len(gameboard)) and cond:
        if gameboard[i] == -1:
            cond = False
        i = i+1
    return cond
    
#Devuelve en que caso estamos segun el movimiento: (team,(row,col,pos_list))
def event(movement, dim_columns, gameboard):
    row = movement[1][0] 
    col = movement[1][1]
    index = row*dim_columns
    if col < dim_columns:
        pos = index + col
        if complete(gameboard):
            actual = 3      #3: Tablero completo
        elif gameboard[pos] == -1:
            actual = 0      #0: Posicion diponible
        else:
            actual = 1      #1: Posicion ocupada
    else:
        print "Movimiento fuera de rango 1"
        actual = 1          #1: La fila se sale de rango
        
    return actual

#Realiza un movimiento: (team,(row,col,pos_list))
def move(team, movement, dim_columns, gameboard):
    row = movement[1][0] 
    col = movement[1][1]
    index = row*dim_columns
    pos = index + col
    gameboard[pos] = team
    return gameboard
    
#Copia el tablero controlado por el Manager a un [] para poder enviarlo
def copiar(gameboard):
    new_board = []
    for i in range(len(gameboard)):
        new_board.append(gameboard[i])
    return new_board

#Cuenta la cantidad de 0s y 1s en el tablero y muestra quien es el ganador
def winner(gameboard):
    team0 = 0
    team1 = 0
    for i in range (len(gameboard)):
        if gameboard[i] == 0:
            team0 = team0 + 1
        else:
            team1 = team1 + 1 
    if team0 > team1:
        winner = 0      #Ganador: Equipo 0
    elif team1 > team0:
        winner = 1      #Ganador: Equipo 1
    else:
        winner = 2      #Empate
    return winner
    

#Proceso
def servir(c, conn, id, team, dim_rows, dim_columns, gameboard, turno):
    
    #Excepcion si falla la comunicacion con el cliente
    try:
        #Envia al cliente (equipo, (row,col,pos_list))
        send_board = copiar(gameboard)
        conn.send((team,(dim_rows, dim_columns, send_board)))
        conexion = True
    except:
        print "Error en la conexion 1"
        conexion = False
    
    #Si hay conexion con el cliente:
    while conexion:
               
        #Excepcion si falla la comunicacion con el cliente
        try:             
            movement = conn.recv()
            print id, "quiere:", movement
        except:
            print "Error en la conexion 2"
            conexion = False
            break
        
        #Gestion de la entrada al tablero de juego:
        c.acquire()
        
        try:
            #Si no es el turno del jugador y el tablero no esta completo tiene que esperar
            while (turno[0] != team) and not complete(gameboard):
                print id, "ESPERA..."
                actual = 2     
                conn.send((actual,(dim_rows, dim_columns, send_board)))
                c.wait()
                
            print id, "intenta:", movement
             
            #Si es el turno del jugador, evalua la situacion
            actual = event(movement, dim_columns, gameboard)  
          
        #Excepcion si el movimiento se sale del tablero
        except IndexError:
            print "Movimiento fuera de rango 2"
            if complete(gameboard):
                actual = 3
            else:
                actual = 1
                
        #Excepcion si el movimiento recibido no se acoge al protocolo
        except TypeError:
            print "Movimiento no se acoge al protocolo"
            if complete(gameboard):
                actual = 3
            else:
                actual = 1
        
        #Excepcion si pasa algo extraño con la comunicacion con el cliente
        except:
            print "Error en la conexion 3"
            if complete(gameboard):
                actual = 3
            else:
                #No hago break por el acquire, notify, release...
                actual = 4     #Ha habido algun error (no se envia al cliente)
                conexion = False

        #Resolucion de la jugada segun la situacion 
                
        #Si la jugada es valida, modificamos el tablero
        if actual == 0:                
            print "Jugada valida"
            move(team, movement, dim_columns, gameboard)
            
        #Si la casilla esta ocupada o el movimiento no se ajusta al protocolo
        elif actual == 1:
            print "Jugada no valida"
        
        #Si el tablero esta completo
        elif actual == 3:
            winner_team = winner(gameboard)
            print "Tablero completo"
            print_board(dim_rows, dim_columns, gameboard) 
            if winner_team == 2:
                print "Empate"
            else:
                print "Ha ganado el equipo", winner_team
            conexion = False
                 
        #Excepcion si falla la comunicacion con el cliente
        try:
            send_board = copiar(gameboard)
            conn.send((actual,(dim_rows, dim_columns, send_board)))
        except:
            print "Error en la conexion 4"
        
        #Si el tablero no esta completo, cambia el turno
        if not complete(gameboard):
            if team == 0:
                turno[0] = 1
            else:
                turno[0] = 0
            print_board(dim_rows, dim_columns, gameboard)                
            print "Turno del equipo", turno[0]
            
        c.notify_all()
        c.release()
          
    conn.close()
    print id, "Conexion cerrada"


if __name__ == '__main__':
    
    listener = Listener(address=('localhost', 6000), authkey='secret password')
    print 'Iniciando Listener'

    manager = Manager()    
    c = Condition()
    
    team0 = []
    team1 = []
    turno = manager.list([0])
    
    print "Turno del equipo", turno[0]
    
    #Se crea el tablero y se muestra por terminal
    
    gameboard = manager.list([])
    dim_rows = 3
    dim_columns = 5
    
    for k in range(dim_rows*dim_columns):
        gameboard.append(-1)
        
    print_board(dim_rows, dim_columns, gameboard)
    
    
    while True:
        
        #Excepcion si no se introduce el password correcto
        try:
            conn = listener.accept()
        
            #Asignacion de los equipos
            
            if (len(team0) <= len(team1)):
                team0.append(listener.last_accepted)
                team = 0
                print "Nuevo jugador en el equipo 0:", listener.last_accepted  
                
            else:
                team1.append(listener.last_accepted)
                team = 1
                print "Nuevo jugador en el equipo 1:", listener.last_accepted
                
            #Proceso
            atender = Process(target=servir, name="Cliente", args=(c, conn, listener.last_accepted, team, dim_rows, dim_columns, gameboard, turno))
            atender.start()
            
        except AuthenticationError:
            print "El cliente no ha puesto correctamente el authkey"
        
    listener.close()
    print "Fin"
