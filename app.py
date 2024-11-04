from flask import Flask
from healthcheck import HealthCheck, EnvironmentDump

app = Flask(__name__)

health = HealthCheck()
envdump = EnvironmentDump()



def application_data():
    return {
        "maintainer": "Luis Fernando Gomes",
        "git_repo": "https://github.com/ateliedocodigo/py-healthcheck"
    }

envdump.add_section("application", application_data)

# Agrega rutas para el health check y el dump del entorno
app.add_url_rule("/healthcheck", "healthcheck", view_func=lambda: health.run())
app.add_url_rule("/environment", "environment", view_func=lambda: envdump.run())

@app.route('/')
def hello_world():
    return 'Hola Mundooooo!'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
