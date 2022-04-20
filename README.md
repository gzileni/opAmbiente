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

### Esempi

```
curl --location --request POST '127.0.0.1:5000/ambiente/station' \
--form 'city="Brindisi"' \
--form 'pollution="CO"' \
--form 'days="20"'
```

Per eseguire il _geocoding_ di un luogo o il _reverse geocoding_ di una coordinata si devono eseguire i seguenti endpoint:

```
curl --location --request GET 'http://127.0.0.1:5000/v1/api/geocode/Bari'
curl --location --request GET 'http://127.0.0.1:5000/v1/api/reverse/16.917983/40.802385'
```

I parametri possibili da usare sono consultabili con la documentazione di [OpenPuglia](https://openpuglia.org/api7) e sono i seguenti:

* city = Altamura, Andria, Arnesano, Bari, Barletta, Bitonto, Brindisi, Campi Salentina, Candela, Casamassima, Ceglie Messapica, Cisternino, Foggia, Francavilla Fontana, Galatina, Grottaglie, Guagnano, Lecce, Maglie, Manfredonia, Martina Franca, Massafra, Mesagne, Modugno, Molfetta, Monopoli, Monte Sant Angelo, Palo del Colle, San Pancrazio Salentino, San Pietro Vernotico, San Severo, Statte, Surbo, Taranto, Torchiarolo

* pollution = PM10, PM10 biora, PM10 ENV, PM10 SWAM, PM2.5, PM2.5 SWAM, BLACK CARB, C6H6, CO, H2S, IPA TOT, NO2, O3, SO2

* days = numero che rappresenta il numero di giorni

La risposta sarà la seguente:

```
{
    "type": "FeatureCollection", 
    "features": [
        {
            "id": "0", 
            "type": "Feature", 
            "properties": {
                "Centralina": "Brindisi - Cappuccini", 
                "Comune": "Brindisi", 
                "Data": "14-02-2022", 
                "Inquinante": "CO ", 
                "Provincia": "Brindisi", 
                "Valore": 0.7
            }, 
            "geometry": {
                "type": "Point", 
                "coordinates": [17.688443357842537, 40.63591975]
            }
        }, 
        {
            "id": "1", 
            "type": "Feature", 
            "properties": {
                "Centralina": "Brindisi - Perrino", 
                "Comune": "Brindisi", 
                "Data": "14-02-2022", 
                "Inquinante": "CO ", 
                "Provincia": "Brindisi", 
                "Valore": 0.7
            }, 
            "geometry": {
                "type": "Point", 
                "coordinates": [17.688443357842537, 40.63591975]
            }
        }, 
        
        .....

```

## Configurazione

Con il file pyOpenPuglia.cfg si può impostare la configurazione per un database PostGis con cui fornire servizi WMS/WFS tramite [GeoServer](http://geoserver.org)

```
# OPENPUGLIA
SERVER="https://openpuglia.org/api7/aria/getAria" # !! don't touch
CRS="EPSG:4326"                 # sistema di riferimento per la proiezione delle coordinate

# PostGis
POSTGIS="true"                
USERNAME_PG="docker"
PASSWORD_PG="docker"
POSTGRESQL="127.0.0.1" 
DATABASE="gis"
SCHEMA="public"
CHUNKSIZE=10000
PORT=32767
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
