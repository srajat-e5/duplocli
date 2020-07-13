FROM duplocloud/code-server:v9

RUN apt-get update
RUN apt-get install -y --no-install-recommends libatlas-base-dev gfortran nginx supervisor

COPY supervisor.conf /etc/supervisor/conf.d/
COPY nginx.conf /etc/nginx/nginx.conf
COPY app /flaskapp/app
COPY uwsgi.ini /etc/uwsgi/uwsgi.ini
COPY requirements.txt /flaskapp/requirements.txt
RUN pip install uwsgi
# RUN apt-get install uwsgi-plugin-python

RUN pip install -r /flaskapp/requirements.txt
RUN pip install supervisor

RUN useradd --no-create-home nginx
RUN rm /etc/nginx/sites-enabled/default
RUN mkdir -m 777 -p /flaskapp/flask_cookie

CMD supervisord -n