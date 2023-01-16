# Creación de demos técnica y documentación asociada, para la detección/clasificación de materiales, utilizando un sensor radar a 60GHz
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/f4d5c40178834f66895745e58be4e64f)](https://www.codacy.com/gh/mecyc/TFG_RADAR_60GHZ/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=mecyc/TFG_RADAR_60GHZ&amp;utm_campaign=Badge_Grade)
<p>TFG realizado en la Universidad de Burgos del desarrollo de un aplicativo para el uso de un Radar de 60 GHz de la marca Acconeer.</p>
<h1>RadarWave - Herramienta para el uso del radar Acconeer de 60GHz</h1>
<h2>Descripción</h2>
<p>En el presente proyecto se ha documentado, implementado y demostrado el uso de un radar de 60 GHz fabricado por Acconeer, para el reconocimiento de diferentes materiales u objetos. Mediante el uso de métodos de aprendizaje, se obtendrán diferentes características de tres tipos de materiales, que permitirán clasificarlos de forma automática.</p>
<p>Este proyecto se centra en el desarrollo de una aplicación de escritorio para el uso de un radar capaz de comparar tres tipos de materiales (cartón, cristal y plástico). Para ello, se han comparado varios modelos clasificadores entrenados a partir de una serie de lecturas, obtenidas de un total de 30 objetos mediante un radar de 60 GHz.</p>

## Aplicación *RadarWave*

La aplicación generada para el proyecto ha sido llamada **RadarWave**, debe su nombre a las ondas generadas por los radares.
Mediante esta aplicación podemos realizar distintas lecturas de objetos para identificar el material que los componen. Se puede realizar nuevas lecturas desde el radar, guardar las lecturas y clasificar lecturas guardadas anteriormente en nuestro equipo.

![](https://github.com/mecyc/TFG_RADAR_60GHZ/blob/main/Latex/img/radarwaveWindows.PNG?raw=true)
> RadarWave

## Cubículo de lectura
<p>Espacio o cubículo empleado para la lectura de objetos. Las dimensiones del cubículo son de 30 x 22 x 25 cm (ancho, largo y alto), con una incisión en la parte superior, en el medio, del tamaño del sensor. El sensor fue bloqueado a su posición solamente colocándole en la posición de la incisión y sujetado con cinta adhesiva. Esta caja de madera se utiliza poniendo la abertura en la parte lateral, mirando al operario que hace uso del radar.</p>

![](https://github.com/mecyc/TFG_RADAR_60GHZ/blob/main/Latex/img/prototipo.png?raw=true)
> Prototipo empleado para realizar las lecturas de los distinto materiales

## Componentes del radar

Los creadores de *Acconner* han elaborado un vídeo ([EVK 2](https://www.youtube.com/watch?v=0uKrm_RAV_c "EVK 2")) con las instrucciones del montaje del sensor. En él se detallan los diferentes componentes y el montaje de hardware a la *Raspberry Pi 4*.

![](https://github.com/mecyc/TFG_RADAR_60GHZ/blob/main/Latex/img/componentes_radar.jpeg?raw=true)
> Hardware

1. Radar A111 de Acconeer
2. Raspberry Pi 4
3. Placa XR112
4. Cable flexible para XR112

![](https://github.com/mecyc/TFG_RADAR_60GHZ/blob/main/Latex/img/componentes_conectados.jpeg?raw=true)
> Componentes en conexión

<h2>Modelos clasificadores comparados</h2>

| Modelo      | Tasa de acierto (%) |
| --------- | -----:|
| Random Forest  | 86.33|
| k-NN     |   87.67 |
| SVM      |    84.67 |
| auto-sklearn      |    88 |
| TabPFN      |   90 |

## Clasificador *k-NN*

Se ha decidido optar por *k-NN* para generar el modelo que utilizará la interfaz desarrollada. Esta decisión se debe a la falta de compatibilidad de *auto-sklearn* y *TabPFN* (basado en *auto-sklearn*) con el sistema operativo *Windows*.  El desarrollo creado se utilizar tanto en *Windows* como en *Linux*.

Matriz de confusión obtenida con el clasificador *k-NN* para 1 vecino:

![](https://github.com/mecyc/TFG_RADAR_60GHZ/blob/main/Latex/img/matrizconfusion_KNN.png?raw=true)
> Matriz de confusión

<p>
Evolución del clasificador en el rango de 1 a 26 vecinos:
</p>

![](https://github.com/mecyc/TFG_RADAR_60GHZ/blob/main/Latex/img/grafica_KNN.PNG?raw=true)
> Matriz de confusión

## Instalación
### *Windows*
Para la instalación en *Windows* consultar el documento de anexos el apartado *E - Documentación de instalación*.
### *Ubuntu (Linux)*
El sistema operativo que utilizamos es *Ubuntu*, una distribución *Linux*, por lo que *Python* está integrado por defecto y no hace falta su instalación. Se recomienda tener actualizado *Python* a la última versión.

Antes de instalar las librerías necesarias instalamos *pip*, es un sistema de gestión de paquetes que nos ayuda a instalar las librerías, y *setuptools*, facilita el empaquetado de proyectos de *Python*.

`$ sudo apt install python3-pip`
`$ pip3 install setuptools-rust`

Una vez terminada la instalación procedemos a descargar y descomprimir
el fichero *RadarWave_v1.0.zip*.

A continuación se debe instalar las librerías que usa la interfaz desarrollada. Indicar que para ejecutar el siguiente comando nos debemos situar en la dirección o PATH donde se encuentra el archivo *requirements.txt*, lo encontramos dentro del fichero que acabamos de descomprimir.

El comando sería el siguiente:

`$ pip3 install -r requirements.txt`

Si existiera algún problema al instalar la librería de *Tkinter (tk)* se deben lanzar los siguientes comandos:

`$ sudo apt-get install python3-tk`
`$ sudo apt-get install python3-pil python3-pil.imagetk`

Finalmente se debe instalar la librería de *Acconeer*, para ello descargamos del repositorio la carpeta *acconer-python-exploration*. Una vez descargada abrimos el terminal dentro de la carpeta y ejecutamos la siguiente orden.

`$ python3 setup.py install`

Si queremos ejecutar *RadarWave* en *Ubuntu* deber ser lanzando el siguiente comando en la misma ruta del archivo *RadarWave.py*.

`$ python3 RadarWave.py`

## Manual de uso

El uso de la aplicación es muy sencillo, tenemos cuatro botones en la parte superior, de izquierda a derecha son:

1. Abrir archivo de lectura
2. Iniciar lectura por radar
3. Clasificar la lectura
4. Guardar datos de lectura.

![](https://github.com/mecyc/TFG_RADAR_60GHZ/blob/main/Latex/img/radarwave_manual.PNG?raw=true)
> Interfaz

Si pulsamos en el botón 1 se abre el explorador de archivos para seleccionar una lectura a clasificar.

Abrimos el fichero y ya tenemos los datos dentro de la aplicación, para clasificaros pulsamos el botón 3. Si lo que queremos el guardarlos pulsamos en el botón 4.

Para realizar una lectura por radar necesitamos iniciar la Raspberry junto con el radar 20 segundos antes de lanzar la lectura, una vez hecho esto pulsamos en el botón 2. Tras esto se iluminan los botones 3 y 4. Para clasificaros pulsamos el botón 3. Si lo que queremos el guardarlos pulsamos en el botón 4.

## Autor
<ul>
<li>Martín Encabo Contreras</li>
</ul>

## Tutores
<ul>
<li>José Francisco Díez Pastor</li>
<li>Pedro Latorre Carmona</li>
</ul>
<br/>
<p align="center"><b>Primera versión:</b> Enero 2023 (v1.0)</p>
