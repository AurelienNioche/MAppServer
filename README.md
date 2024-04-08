# MAppServer

Server part for the Active Teaching project. 

Instructions are given for MacOS (unless specified otherwise), using homebrew package manager (https://brew.sh/).

## Websocket URL

`wss://samoa.dcs.gla.ac.uk/mapp/ws`

## Dependencies

#### Python

    brew install python3

Version used:
- Python 3.9.13

#### Python libraries

    pip3 install -r requirements.txt


#### PostgreSQL (MacOS)

(Skip this if you are on GNU/Linux)

Install postgresql

    brew install postgresql
    
Run pgsql server (to have launchd start postgresql now and restart at login): 

    brew services start postgresql

OR if you don't want/need a background service:

    pg_ctl -D /usr/local/var/postgres start


## Configuration

#### Django

Move to the directory where are the settings

    cd <path to the parent folder>/MAppServer
    
Create a "credential.py" script

    nano ActiveTeachingServer/credentials.py

It should look like:
    
    SECRET_KEY = '<one arbirary combinaton of characters>'

    DB_NAME = 'MAppServer'
    DB_USER = 'postgres'
    DB_PASSWORD = ''
    
    EMAIL_HOST_USER = ''
    EMAIL_HOST_PASSWORD = ''


#### Sending mail with Gmail

Mail => Settings => Allow IMAP

Google Account => Security => Activate 2 Steps

Then at the bottom, create an `App Password`



#### PostgreSQL

Make sure posgresql is running. If necessary:
    
    brew services start postgresql

Create user 'postgres' if it doesn't exist
    
    createuser -s postgres

Run the script to create the database

    python3 db_create_db.py

   
## Run

Run Django server using the Django command

    python3 manage.py runserver

## Extra information


### Manipulations of DB

Remove the db
    
    dropdb <db name>


## Server Deployment

* Clone repository in `<dedicated folder>`

* Give permissions to read/write/execute to the dedicated folder:

        
        sudo chmod -R o+rwx <dedicated folder>
    
* Change the initial values of file permissions for new files 
(useful when using `git pull`)
        
        
        umask 0022
 
* Create a virtual environment


        sudo apt-get install virtualenv
        cd /var/www/html/ActiveTeachingServer
        virtualenv -p python3 venv
        source venv/bin/activate
        pip install -r requirements.txt

* Create the database and make the migrations


        createdb <db name> --owner postgres
        python manage.py makemigrations
        python manage.py migrate

* 'Collect' the static files

    
    python manage.py collectstatic

    
* Create Daphne daemon file `/etc/systemd/system/daphne.service`

    * HTTPS config:
      

        [Unit]
        Description=ActiveTeaching Daphne Service
        After=network.target
        
        [Service]
        Type=simple
        User=www-data
        WorkingDirectory=/var/www/html/ActiveTeachingServer
        Environment=DJANGO_SETTINGS_MODULE=ActiveTeachingServer.settings
        ExecStart=/var/www/html/ActiveTeachingServer/venv/bin/python /var/www/html/ActiveTeachingServer/venv/bin/daphne -e ssl:8001:privateKey=activeteaching.research.comnet.aalto.fi.key:certKey=activeteaching.research.comnet.aalto.fi.crt ActiveTeachingServer.asgi:application
        Restart=on-failure
        
        [Install]
        WantedBy=multi-user.target


* Launch Daphne:
    
    
    sudo systemctl daemon-reload
    sudo systemctl start daphne.service

    
* [Optional] Check that everything is fine for Daphne/Apache: 

    
    sudo systemctl status daphne.service
    sudo systemctl status apache2.service
    
    
### Build Unity

Do a build for Unity:

    Build Settings -> Build -> Save as 'Builds'

Structure is: 

    Builds
    -> Build/
    -> index.html
    -> TemplateData/
    -> UnityLoader.js

Be careful that the address is of the following form (don't include the port):
    
    ws://<domain>/


### In case of accident/misunderstanding/disagreement with Git (don't do this!)

If you accidentally push something you don't want 
(i.e. credentials or sensitive data)

    git reset --hard <ref last correct commit>
    git push --force
    
If you want to pull, but Git doesn't let you do it

    git fetch --all
    git reset --hard origin/master


### Permissions for psql

sudo chmod 700 /var/lib/postgresql/10/main
sudo chown postgres.postgres /var/lib/postgresql/10/main


## Android 

On the device, open the Settings app, select Developer options, and then enable USB debugging

If already on, turn off and on again.

## Assets edition on Inscape

If png, do first: right click, trace bitmap, use "autotrace" option
then for changing colour, use extensions-> color-> replace


## Database size

As a very raw estimate:
https://dba.stackexchange.com/questions/46069/how-to-estimate-predict-data-size-and-index-size-of-a-table-in-mysql

With 1M lines, around 70 MB

## Notes to future me concerning the timestamps

* Android/Java use timestamp in milliseconds
* C# counts in seconds like Python, but since Christ (what an idea)
* Python counts in seconds and uses unix reference)

## If you want to allow backup on Android, add this to the manifest, in the application chevron
        android:allowBackup="true"
        android:dataExtractionRules="@xml/data_extraction_rules"
        android:fullBackupContent="@xml/backup_rules"

E.g

    <application
        android:allowBackup="true"
        android:dataExtractionRules="@xml/data_extraction_rules"
        android:fullBackupContent="@xml/backup_rules"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/AppTheme"
        android:background="#000000"
        tools:targetApi="33"
        >

## Unity as a library

When cleaning the ressources, don't remove the string value for `game_view_content_description`


    <string name="game_view_content_description">Game view</string>


Also, for avoiding to have two icons, cutom manifest -> remove launcher

## Websocket Library for Unity

`https://github.com/endel/NativeWebSocket/tree/master`

## Config for UoG

websocket URL: `wss://samoa.dcs.gla.ac.uk/mapp/ws`

Django logs: `/home/aurelien/DjangoApps/MAppServer/log/asgi.log`

Service logs: `nano /var/log/supervisor/supervisord.log`

Nginx logs: `/var/log/nginx/access.log` and `/var/log/nginx/error.log` 


restart all processes:

    sudo supervisorctl restart all


Create the db:

    sudo -u postgres createdb MAppServer

Add to config file:
    
    ALLOWED_HOSTS = ["*"]
    CSRF_TRUSTED_ORIGINS = ["http://pearse.dcs.gla.ac.uk"]

## TODO (right before launching)

* Check the settings in `src/Config` in the Android project
* Check the settings in the server

## TODO (UX/UI)

* Check for responsiveness

## TO DO (backend features)

* Implement the belief update system
* Implement the update of the challenges (action selection)

## TO DO (Feature = Challenge update)

=> TEST THIS:
  * When a client connects for updating, 
    * Look at the challenges that the client wants to update (because offer accepted, and so on). 
      - Whether the `server_tag` is different or not, then use the client data to update the server data.
      Make sure that this will mean that the challenge is rolled back to the initial state in case 
        the `server_tag` is different. Maybe in the future, add a comment in the db, or a related 
        field with all the update history.
    * Then, look if new activity data. If so:
      * Update the activity data
      * Update the beliefs of the model
      * If so, possibly update the challenges.
          - if a challenge offer window already began, it can not be updated
          - otherwise, update the challenge
          - When updating, update the variables in the `Challenge` class, and generate a new 
            server tag 
              `server_tag`
      * Check which challenges have been updated by comparing the `server_tag` with the 
        `android_tag`. Give the list of challenges to the client.

=> FULL ROLLOUT
  * Test with a virtual user - Step 1 with bullshit steps
  * Test with a virtual user - Step 2 with generative model
  * Using the app

# Extra

* Optional: Give a thought about allowing backup or not (?)

* (Very?) Optional: Put on Google Play
* (Very?) Optional: Check how to access properly the timezone on Android
* (Very?) Optional: Notification ONLY when app is not on focus
* (Very?) Optional: Display to user at what time the reward has been reached
* (Very) Optional: delete step records on phone when sync with server
* (Very?) Optional: Prevent cheating by tracking phoneId
* (Very?) Optional: View a history of the challenges