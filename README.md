# opAmbiente

opProxy è un server proxy per georeferenziare i dati aperti sul monitoraggio ambientale delle centraline ARPA Puglia consultabili attraverso il server REST API di [OpenPuglia](https://openpuglia.org/api7)

## Installazione

```
git clone https://github.com/gzileni/opAmbiente.git
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=opAmbiente
```

nel caso si vuole usare l'ambiente di sviluppo digitare anche:

```
export FLASK_ENV=development
```

infine eseguire il proxy con:

```
flask run -p 5000 -h 0.0.0.0
```

## Configurazione

Con il file opAmbiente.json si può impostare la configurazione per un database PostGis con cui fornire servizi WMS/WFS tramite [GeoServer](http://geoserver.org)

```
{
    "SERVER":"http://openpuglia.org/api7/aria/getAria",
    "CRS": "EPSG:4326",
    "DAYS": 3,
    "USERNAME_PG": "",
    "PASSWORD_PG": "",
    "POSTGRESQL": "", 
    "DATABASE": "",
    "PORT": 5432
}
```

## Python Pip broken with sys.stderr.write(f"ERROR: {exc}")

Per risolvere questo errore è necessario re-installare pip:

```
curl  https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py
python get-pip.py
```

## [NGINX Configuration](https://flask.palletsprojects.com/en/1.1.x/deploying/uwsgi/)

````
uwsgi /home/zileni/pyOpenPuglia/pyopenpuglia.ini --manage-script-name --mount /pyOpenPuglia=pyOpenPuglia:app --virtualenv /home/zileni/pyOpenPuglia/venv --plugin python3
````

## Creazione script di avvio

Creare un ssystemd unit file con l'estensione .service in `/etc/systemd/system`, ad esempio `/etc/systemd/system/opproxy.service, con il seguente contenuto:

```
[Install]
WantedBy=multi-user.target

[Unit]
Description=opProxy startup script

[Service]
ExecStart=/path/to/application/start.sh

[Install]
WantedBy=multi-user.target
```

Per avviare e fermare il servizio:

```
sudo systemctl start my-service / systemctl stop my-service.
```

Per abilitarlo all'avvio del sistema, eseguire:

```
sudo systemctl enable my-service
```
