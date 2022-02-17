#!/usr/bin/env python
# coding: utf-8

# In[73]:


'''RadarWave: Reconocimiento de materiales'''
__author__ = 'Martín Encabo Contreras'
__title__= 'RadarWave'
__date__ = ''
__version__ = '1.0.0'
__license__ = ''


# In[78]:


import os, sys, platform
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox as mb
from tkinter import *
import numpy as np
import pandas as pd
from cmath import phase
import joblib #from sklearn.externals 
from acconeer.exptool import *
from tkinter import filedialog as fd 

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

import socket
import paramiko #conda install -c anaconda paramiko


# In[85]:


class RadarWave():
        
    
    def __init__(self,iconos):
        
        self.iconos = iconos
        
        #Cargar modelo RandomForest
        self.modelo = joblib.load('modeloRandomForest.pkl')

        #DICCIONARIO
        self.diccionario = { 
            'carton': 'CARTON',
            'plastico': 'PLASTICO',
            'cristal': 'CRISTAL' 
        }
        
        self.contador = 0

        #Inicializar GUI
        self.app=tk.Tk()
        self.app.geometry('800x600')
        self.app.title('RadarWave')
        self.app.iconbitmap(self.iconos[0])   # Asignar icono
        self.app.configure(background='lavender') #CDCDCD
        
        
        #------- Barra de herramientas
        
        barramenu = Menu(self.app)
        self.app['menu'] = barramenu

        # DEFINIR SUBMENÚS

        self.menu1 = Menu(barramenu) #BARRA HERRAMIENTAS
        menu2 = Menu(barramenu) #BOTONES
        barramenu.add_cascade(menu=self.menu1, label='Lectura')
        barramenu.add_cascade(menu=menu2, label='Ayuda')
        
        # Seccion 'Lectura':
        self.menu1.add_command(label="Leer archivo", command=self.carga_datos)
        self.menu1.add_separator() #separador
        self.menu1.add_command(label="Iniciar radar", command=self.carga_acconeer)
        self.menu1.add_separator() #separador
        self.menu1.add_command(label="Verificar lectura", state=DISABLED, command=lambda: self.clasificar())
        self.menu1.add_separator() #separador
        self.menu1.add_command(label="Guardar lectura", state=DISABLED, command=lambda: self.guardar_datos())
        
        
        # Seccion 'Ayuda':
        self.icono_acercade = PhotoImage(file=self.iconos[1])
        menu2.add_command(label="Acerca de", command=self.createAboutUs)
        
        #Barra de botones
        self.icono1 = PhotoImage(file=self.iconos[2])
        self.icono2 = PhotoImage(file=self.iconos[3])
        self.icono3 = PhotoImage(file=self.iconos[4])
        self.icono4 = PhotoImage(file=self.iconos[5])

        barraherr = Frame(self.app, relief=RAISED, bd=2, bg="#E5E5E5")
        bot1 = Button(barraherr, image=self.icono1,command=self.carga_datos)
        bot1.pack(side=LEFT, padx=1, pady=1)
        bot2 = Button(barraherr, image=self.icono2,command=self.carga_acconeer)
        bot2.pack(side=LEFT, padx=1, pady=1)
        self.bot3 = Button(barraherr, image=self.icono3, state=DISABLED, command=lambda: self.clasificar())
        self.bot3.pack(side=LEFT, padx=1, pady=1)
        self.bot4 = Button(barraherr, image=self.icono4, state=DISABLED, command=lambda: self.guardar_datos())
        self.bot4.pack(side=LEFT, padx=1, pady=1)
        barraherr.pack(side=TOP, fill=X)
        
        #------- Barra de estado
        
        info1 = platform.system()
        info2 = platform.node()
        info3 = platform.machine()

        mensaje = " " + info1+ ": "+info2+" - "+info3
        self.statusbar = Label(self.app, text=mensaje,bd=1, relief=SUNKEN, anchor=W)
        self.statusbar.pack(side=BOTTOM, fill=X)
        
        #------ Cabecera
        heading = Label(self.app, text="Clasificador de materiales", font=('arial',20,'bold'))
        heading.configure(background='lavender',foreground='#364156')
        heading.pack(side=TOP,fill=X,expand=True)

        #------- Sección Gráficos

        self.centro=Label(self.app,background='lavender', font=('arial',15,'bold'))

        framegraficos = Frame(bg="#949292", width="500", height="620")
        framegraficos.pack(side="top",padx=10,pady=5)

        #Gráfico 
        #valores iniciales para el gráfico de barras:
        Data1 = {'Materiales': ['CARTON','CRISTAL','PLASTICO'], 'Probabilidad': [0,0,0]}
        df1 = pd.DataFrame(Data1, columns= ['Materiales', 'Probabilidad'])
        df1 = df1[['Materiales', 'Probabilidad']].groupby('Materiales').sum()

        #Crear Gráfico de barras:
        grafico1 = plt.Figure(figsize=(6,6), dpi=70)
        self.barras = grafico1.add_subplot(111)
        self.bar1 = FigureCanvasTkAgg(grafico1, framegraficos)
        self.bar1.get_tk_widget().pack()
        #df1.xticks(rotation='horizontal')
        df1.plot(kind='bar', legend=True, ax=self.barras,rot=0)

        self.barras.set_title('Probabilidad de pertenencia')

        self.centro.pack(side=TOP,expand=True)

        self.app.mainloop()
        
        
        
    '''
    Una función que a partir del nombre del fichero npy carge los datos, los redimensione y los devuelva. 
    Al estilo de la función get_data(). Devuelve "datos_bruto". 

    Los test de esta función:   comprobar que devuelve un array 2D, 
                                comprobar que la segunda dimensión tiene tamaño 291, 
                                comprobar que la matriz tiene una parte real 
                                y que tiene una parte imaginaria.
    '''

    def get_data(self, url):
        self.diccionario = np.load(url, allow_pickle=True).item()
        self.data = self.diccionario.get('sweep_data').get('data')
        self.data = self.data.reshape(self.data.shape[0],self.data.shape[2])
        return self.data

    
    
    '''
    Una función get_modulo_fase() que a partir del array 2D anterior, obtenga un array 2D, con el doble de anchura. 
    Por ejemplo, si "datos_bruto" es de 300x291, "modulo_fase" será de 600x291. 
    Esa función obtendrá el módulo del número complejo y la fase del número complejo. 
        Módulo será una matriz de 300x291 y fase también. 
    Será necesario concatenarlas "horizontalmente". 
    Los test comprobarán las dimensiones y tamaños.
    '''

    def get_modulo_fase(self):
        modulo = abs(self.data)
        fase = []
        for i in self.data:
            fila = []
            for j in i:
                fila.append(phase(j)) #Fase
            fase.append(fila)
        fase = np.asarray(fase)
        modulo_fase = np.concatenate((modulo, fase), axis=0)
        return np.asarray(modulo_fase)
    
    
    '''
    Una función que a partir de los datos "modulo_fase" devuelva la media. 
    La comprobación sería que devuelva un array de 1 dimensión de tamaño 582 (291 x 2).
    '''
    def get_media(self,modulo_fase):
        traspuesta = np.transpose(modulo_fase) #Obtenemos la matriz traspuesta(291x600) de modulo_fase(600x291)

        #Separamos la traspuesta en modulo y fase
        t_modulo = traspuesta[:,:int(traspuesta.shape[1]/2)]
        t_fase = traspuesta[:,int(traspuesta.shape[1]/2):]

        media = []
        for i in t_modulo:
            media.append(i.mean())
        for j in t_fase:
            media.append(j.mean())

        return np.asarray(media) #Devuelve medias modulo y fase
    
    def carga_datos(self):
        try:  
            self.datos = []
            self.data = []

            url = fd.askopenfilename(initialdir = "./Materiales",title = "Abrir archivo",
                                filetypes = (("npy files","*.npy"),("all files","*.*")))
            try:
                self.data = self.get_data(url) #lectura de archivos generados por GUIACCONEER
            except:
                self.data = np.load(url) #lectura de archivos leidos por RadarWave
            modulofase = self.get_modulo_fase()
            media = self.get_media(modulofase)

            self.datos.append(media)
            
            self.centro.configure(text='')
            self.mostrar_btnlectura()
            self.mostrar_btnguardar()
        except:
            pass

    def guardar_datos(self):
        try:
            os.makedirs('./Materiales', exist_ok=True)
            url = fd.asksaveasfilename(initialdir = "./Materiales",title = "Gurardar lectura",
                                         filetypes = [("npy files","*.npy")])
            if url!='':
                archi1=open(url, "wb")
                np.save(archi1,self.data)
                archi1.close()
                mb.showinfo("Información", "Los datos fueron guardados en el archivo.")
        except:
            pass
            
    def carga_acconeer(self):
        try:
            ip = socket.gethostbyname('RadarAcconeer')

            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(ip, 22, 'pi', 'raspberry')
            
            
            #Ejecutar servicio radar
            if self.contador == 0:
                ssh_client.exec_command('Downloads/rpi_xc112/utils/acc_streaming_server_rpi_xc112_r2b_xr112_r2b_a111_r2c')
                self.contador+=1
            
            #Parámetros del radar
            iq = configs.IQServiceConfig()
            envelope = configs.EnvelopeServiceConfig()
            iq.range_interval=[0.10, 0.24]
            envelope.range_interval=[0.10, 0.24]
            raspi = clients.SocketClient(ip)
            raspi.connect()
            raspi.start_session(iq)
            
            self.data = []

            for i in range(300):
                self.data.append(raspi.get_next()[-1])
            
            #raspi.close()
            
            ssh_client.close()
            
            self.data = np.asarray(self.data)

            modulofase = self.get_modulo_fase()
            media = self.get_media(modulofase)

            self.datos = []
            self.datos.append(media)
            self.centro.configure(text='')

            self.mostrar_btnlectura()
            self.mostrar_btnguardar()
            
        except:
            mb.showerror("Error", "No hay conexión con el radar.")
            pass


    def mostrar_btnlectura(self):
        self.bot3['state'] = NORMAL
        self.menu1.entryconfig("Verificar lectura",state = NORMAL)
    
    def mostrar_btnguardar(self):
        self.bot4['state'] = NORMAL
        self.menu1.entryconfig("Guardar lectura",state = NORMAL)
    
    def clasificar(self):
        global label_packed
        pred = self.modelo.predict(self.datos)[0]
        #print(pred)
        #salida = self.diccionario[pred]
        self.centro.configure(foreground='#011638', text=pred.upper()) 
        porcentajes = self.modelo.predict_proba(self.datos)[0]
        self.actualizarGrafico(porcentajes)
        
        self.bot3['state'] = DISABLED
        self.bot4['state'] = DISABLED
            
        self.menu1.entryconfig("Verificar lectura",state = DISABLED)
        self.menu1.entryconfig("Guardar lectura",state = DISABLED)
        

    def actualizarGrafico(self,porcentajes):
        #global barras
        self.barras.clear()
        #crear dataframe
        Data1 = {'Materiales': ['CARTON','CRISTAL','PLASTICO'], 'Probabilidad': porcentajes}
        df1 = pd.DataFrame(Data1, columns= ['Materiales', 'Probabilidad'])
        df1 = df1[['Materiales', 'Probabilidad']].groupby('Materiales').sum()
        #Agregar data al grafico de barras
        df1.plot(kind='bar', legend=True, ax=self.barras, rot=0)
        self.barras.set_title('Probabilidad de pertenencia')
        self.bar1.draw()
        

    def createAboutUs(self):
        acerca = Toplevel()
        acerca.geometry("320x280")
        acerca.resizable(width=False, height=False)
        acerca.title("Acerca de")
        
        marco1 = ttk.Frame(acerca, padding=(10, 10, 10, 10), relief=RAISED)
        marco1.pack(side=TOP, fill=BOTH, expand=True)
        
        etiq1 = Label(marco1, image=self.icono_acercade, relief='raised')
        etiq1.pack(side=TOP, padx=10, pady=10, ipadx=10, ipady=10)
        
        etiq2 = Label(marco1, text="RadarWave "+__version__, foreground='blue') #font=self.fuente
        etiq2.pack(side=TOP, padx=10)
        
        etiq3 = Label(marco1, text="Clasificador de materiales")
        etiq3.pack(side=TOP, padx=30)
        
        boton1 = Button(marco1, text="Salir",command=acerca.destroy)
        boton1.pack(side=TOP, padx=30, pady=10)
        boton1.focus_set()
        
        acerca.transient(self.app)
        self.app.wait_window(acerca)
    
    
    


# In[ ]:


def f_verificar_iconos(iconos):
    ''' Verifica existencia de iconos

    iconos -- Lista de iconos '''        

    for icono in iconos:
        if not os.path.exists(icono):
            print('Icono no encontrado: ' + icono)
            return(1)
    return(0)


def main():
    ''' Iniciar aplicación '''

    app_carpeta = os.getcwd()
    img_carpeta = app_carpeta + os.sep + "iconos" + os.sep
    # DECLARAR Y VERIFICAR ICONOS DE LA APLICACIÓN:

    iconos = (img_carpeta + "icono.ico",
              img_carpeta + "acercade.png",
              img_carpeta + "documento.png",
              img_carpeta + "radar.png",
              img_carpeta + "tick.png",
              img_carpeta + "guardar.png")
    error1 = f_verificar_iconos(iconos)

    if not error1:
        mi_app = RadarWave(iconos)
    return(0)

if __name__ == '__main__':
    main()


# In[31]:





# In[ ]:




