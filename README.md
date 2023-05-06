# sistemas-distribuidos-tp1

Link Diagramas:
https://drive.google.com/drive/folders/1unfbrE7vnXzQ6SER-qOJV_h9Eut1ku8r

Link Overleaf:
https://www.overleaf.com/project/643d92f189dac2cf352c5ba9


## Build
Cambiar las variables de configuracion en el archivo create-docker-compose.sh (TODO pasarlas a un archivo). Ejecutar el script. Luego correr
```bash
make docker-compose-up
```

Ver logs con 


```bash
make docker-compose-logs

```

## TODO
* Shutdown
* ACKs en queues de weather y stations.