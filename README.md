# Sistemas Distribuidos - TP1

## Nombre: Mateo Capon Blanquer
## Padron: 104258

Link Diagramas:
https://drive.google.com/drive/folders/1unfbrE7vnXzQ6SER-qOJV_h9Eut1ku8r

Link Overleaf:
https://www.overleaf.com/project/643d92f189dac2cf352c5ba9


## Build
Cambiar las variables de configuracion en el archivo `config.txt`. Ejecutar el script `create-docker-compose.sh`.

```bash
sh create-docker-compose.sh
```

Ejecutar al sistema con:

```bash
make docker-compose-up
```

Ver logs con:


```bash
make docker-compose-logs
```

Para frenar al sistema, ejecutar:

```bash
make docker-compose-down
```
