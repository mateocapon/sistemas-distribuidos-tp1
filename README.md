# sistemas-distribuidos-tp1

## TODO
Crear script que cree el docker compose con la cantidad de ciudades y los path de los archivos.

## Consideraciones
1. Meti al cliente en una sola computadora que envia los archivos y una vez que deja de enviar, pide los resultados. Pero es solo uno el cliente, por mas que levante algunos procesos.
2. No separo el send y la lectura del archivo en el cliente en procesos separados, porque suponiendo un esquema en el que el cliente se encuentra fisicamente separado del servidor, el tiempo en leer del archivo sera muy seguramente al menos un orden de magnitud mas rapido que lo que puede demorar en enviar un paquete a traves de la red. 

3. El server esta acoplado con el cliente en el sentido de que sabe que no le abriran demasiadas conexiones en un principio.

Preguntas

1. Es valido suponer que la cantidad de clientes no va a ser lo suficientemente grande para que haya problemas de fd. Es decir, el server mantiene a la cantidad de clientes siempre activos. No hace falta ir abriendo y cerrando conexiones con los clientes.

Esto se puede simplificar en la pregunta: cuantas ciudades tenemos que suponer que envian datos a traves de la red? 
2. 