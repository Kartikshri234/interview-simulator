# Project Folder Structure

Generated: 2026-04-08 22:23:08

```text
Folder PATH listing for volume Windows
Volume serial number is E44B-A095
C:.
|   .env
|   .env.example
|   .gitignore
|   .python-version
|   build.sh
|   db.sqlite3
|   manage.py
|   nixpacks.toml
|   Procfile
|   README.md
|   render.yaml
|   requirements.txt
|   runtime.txt
|   
+---.vscode
|       settings.json
|       
+---apps
|   |   __init__.py
|   |   
|   +---interview
|   |   |   ai_services.py
|   |   |   api_urls.py
|   |   |   api_views.py
|   |   |   apps.py
|   |   |   models.py
|   |   |   routing.py
|   |   |   urls.py
|   |   |   views.py
|   |   |   __init__.py
|   |   |   
|   |   +---migrations
|   |   |   |   0001_initial.py
|   |   |   |   0002_initial.py
|   |   |   |   0003_new_features.py
|   |   |   |   0004_fix_question_blank.py
|   |   |   |   __init__.py
|   |   |   |   
|   |   |   \---__pycache__
|   |   |           0001_initial.cpython-311.pyc
|   |   |           0002_initial.cpython-311.pyc
|   |   |           0003_new_features.cpython-311.pyc
|   |   |           0004_fix_question_blank.cpython-311.pyc
|   |   |           __init__.cpython-311.pyc
|   |   |           
|   |   \---__pycache__
|   |           ai_services.cpython-311.pyc
|   |           api_urls.cpython-311.pyc
|   |           api_views.cpython-311.pyc
|   |           apps.cpython-311.pyc
|   |           models.cpython-311.pyc
|   |           urls.cpython-311.pyc
|   |           views.cpython-311.pyc
|   |           __init__.cpython-311.pyc
|   |           
|   +---resume_screening
|   |   |   apps.py
|   |   |   services.py
|   |   |   urls.py
|   |   |   views.py
|   |   |   __init__.py
|   |   |   
|   |   +---migrations
|   |   |   |   __init__.py
|   |   |   |   
|   |   |   \---__pycache__
|   |   |           __init__.cpython-311.pyc
|   |   |           
|   |   \---__pycache__
|   |           apps.cpython-311.pyc
|   |           services.cpython-311.pyc
|   |           urls.cpython-311.pyc
|   |           views.cpython-311.pyc
|   |           __init__.cpython-311.pyc
|   |           
|   +---users
|   |   |   admin.py
|   |   |   api_urls.py
|   |   |   api_views.py
|   |   |   apps.py
|   |   |   jwt_utils.py
|   |   |   models.py
|   |   |   urls.py
|   |   |   views.py
|   |   |   __init__.py
|   |   |   
|   |   +---migrations
|   |   |   |   0001_initial.py
|   |   |   |   0002_streak.py
|   |   |   |   __init__.py
|   |   |   |   
|   |   |   \---__pycache__
|   |   |           0001_initial.cpython-311.pyc
|   |   |           0002_streak.cpython-311.pyc
|   |   |           __init__.cpython-311.pyc
|   |   |           
|   |   \---__pycache__
|   |           admin.cpython-311.pyc
|   |           api_urls.cpython-311.pyc
|   |           api_views.cpython-311.pyc
|   |           apps.cpython-311.pyc
|   |           jwt_utils.cpython-311.pyc
|   |           models.cpython-311.pyc
|   |           urls.cpython-311.pyc
|   |           views.cpython-311.pyc
|   |           __init__.cpython-311.pyc
|   |           
|   \---__pycache__
|           __init__.cpython-311.pyc
|           
+---config
|   |   asgi.py
|   |   settings.py
|   |   urls.py
|   |   views.py
|   |   wsgi.py
|   |   __init__.py
|   |   
|   \---__pycache__
|           settings.cpython-311.pyc
|           urls.cpython-311.pyc
|           views.cpython-311.pyc
|           wsgi.cpython-311.pyc
|           __init__.cpython-311.pyc
|           
+---media
|   \---avatars
|           1772389701170.png
|           
+---resume_uploads
+---static
|   +---css
|   |       app.css
|   |       features.css
|   |       
|   \---js
|           common.js
|           dashboard.js
|           history.js
|           interview_room.js
|           new_interview.js
|           profile.js
|           results.js
|           
\---templates
    |   404.html
    |   500.html
    |   base.html
    |   
    +---interview
    |       bookmarks.html
    |       dashboard.html
    |       history.html
    |       new_interview.html
    |       results.html
    |       room.html
    |       
    +---partials
    |       header.html
    |       mobile_drawer.html
    |       
    +---resume_screening
    |       screening.html
    |       
    \---users
            login.html
            profile.html
            register.html
            
```
