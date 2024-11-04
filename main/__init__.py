import logging
from flask import Flask
import os
from app.config import config
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry._logs import set_logger_provider
from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter

logger_provider = LoggerProvider()
set_logger_provider(logger_provider)
exporter = AzureMonitorLogExporter(connection_string=os.getenv('CONNECTION_STRING'))
logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))

# Configuración del manejador de registros y configuración del nivel de registro
handler = LoggingHandler()
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.NOTSET)

def create_app() -> None:
    app_context = os.getenv('FLASK_CONTEXT')
    app = Flask(__name__)
    f = config.factory(app_context if app_context else 'development')
    app.config.from_object(f)
    
    exporter.from_connection_string(app.config['CONNECTION_STRING'])

    # Configuración del proveedor de trazas para OpenTelemetry
    tracer_provider = TracerProvider(
        resource=Resource.create({SERVICE_NAME: app.config['OTEL_SERVICE_NAME']})
    )
    trace.set_tracer_provider(tracer_provider)

    # Habilitar la instrumentación de trazas para la biblioteca Flask
    FlaskInstrumentor().instrument_app(app)

    RequestsInstrumentor().instrument()

    trace_exporter = AzureMonitorTraceExporter(connection_string=app.config['CONNECTION_STRING'])
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(trace_exporter)
    )

    from app.resources import home_bp, home_resource  # Ajustar según tu estructura de carpetas

    app.register_blueprint(home_bp, url_prefix='/api/v1')

    @app.shell_context_processor    
    def ctx():
        return {"app": app}
    
    return app
