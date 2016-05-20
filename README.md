## Remind Me Latr

The code behind http://www.remindmelatr.com.


## Motivation

Remind Me Later lets you create reminders for yourself using natural language e.g.

* "Hairdresser 7pm"
* "Pick up laundry 10am tomorrow"
* "Get the kids from school 3pm"
* "Mow the lawn Saturday 14:00"
* "Ten am Friday call Grandma"
* "Dance lessons midnight Sunday"
* "Meet Bob midday Wednesday"
* "Have something to eat lunchtime today"
    
At the specified time the user receives an email/desktop alert and is able to snooze, pause or complete the reminder.


## Installation

##### Get a copy of the code

```
wget https://github.com/niross/remindmelatr/archive/master.zip
unzip master.zip
cd remindmelatr-master
```

##### Setup the environment
```
mkdir ~/.venvs
virtualenv ~/.venvs/remindmelatr

export PYTHONPATH=$(pwd)
echo "!!" >> ~/.venvs/remindmelatr/bin/activate

export DJANGO_SETTINGS_MODULE="settings.development"
echo "!!" >> ~/.venvs/remindmelatr/bin/activate

export DATABASE_URL="sqlite:///$(pwd)/db/development.sqlite3"
echo "!!" >> ~/.venvs/remindmelatr/bin/activate

export FROM_EMAIL="test@test.com"
echo "!!" >> ~/.venvs/remindmelatr/bin/activate

export DJANGO_SECRET_KEY='XXXXXX' # Generate your own key at http://www.miniwebtool.com/django-secret-key-generator/
echo "!!" >> ~/.venvs/remindmelatr/bin/activate

export AWS_ACCESS_KEY_ID="XXXXXX" # Optional - For use with Amazon SES
echo "!!" >> ~/.venvs/remindmelatr/bin/activate

export AWS_SECRET_ACCESS_KEY="XXXXXX" # Optional - For use with Amazon SES
echo "!!" >> ~/.venvs/remindmelatr/bin/activate
```

##### Install the requirements
```
source ~/.venvs/remindmelatr/bin/activate
pip install -r requirements/local.txt
```

##### Create and populate the database
```
django-admin migrate
django-admin create_timezones
django-admin create_remindats
django-admin create_remindons
django-admin loaddata apps/accounts/fixtures/socialapp.json
```

##### Start it up
```
django-admin runserver

# Run celery in a new terminal window

cd <path to remindmelatr repo>
source ~/.venvs/remindmelatr/bin/activate
django-admin celeryd -B
```

##### Next steps

1. Visit http://localhost:8000
2. Create an account
3. Confirm your email (in the console you will find an email containing a verification link)
4. Login and start creating reminders


## Tests

`django-admin.py test --settings settings.test`


## Contributors

[Nick Ross](https://github.com/niross)

