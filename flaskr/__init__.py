import os
from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
from werkzeug.utils import secure_filename
from datetime import datetime
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Cargar variables de entorno primero
load_dotenv()

# Inicializar extensiones fuera de create_app
db = SQLAlchemy()
mail = Mail()
jwt = JWTManager()
migrate = Migrate()
api = Api()

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # 1. Configuración crítica para PostgreSQL en Railway
    db_url = os.getenv('DATABASE_URL', '').replace('postgres://', 'postgresql://')
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20,
        'connect_args': {
            'sslmode': 'require',
            'options': '-c statement_timeout=15000'  # 15 segundos timeout
        }
    }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 2. Configuración JWT
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'fallback_secret_key')
    
    # 3. Configuración para subida de archivos
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 4. Configuración de email
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    # 5. Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app)
    api.init_app(app)

    # 6. Registrar rutas
    register_routes(app)

    # 7. Filtro personalizado para templates
    @app.template_filter('format_number')
    def format_number(value):
        if isinstance(value, (int, float)):
            return f"${value:,.0f}".replace(",", ".")
        return value

    # 8. Ruta para archivos subidos
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # 9. Verificar conexión a DB al iniciar
    with app.app_context():
        try:
            db.engine.connect()
            print("✅ Conexión a PostgreSQL exitosa!")
        except Exception as e:
            print(f"❌ Error conectando a PostgreSQL: {str(e)}")

    return app

def register_routes(app):
    """Registra todas las rutas de la API"""
    from .vistas.vistas import (
        VistaUsuario, VistaProductos, VistaProductosBajoStock, 
        VistaActualizarEstadoAdmin, VistaEnviosAdmin, VistaEstadoEnvio,
        VistaPedidosUsuario, VistaUltimaFactura, VistaReportesProductos,
        VistaProducto, VistaTarjeta, VistaPaypal, VistaTransferencia,
        VistaProductosRecomendados, VistaCategorias, VistaCategoria,
        VistaUsuarios, VistaLogin, VistaSignIn, VistaCarrito, VistaCarritos,
        VistaCarritoActivo, VistaRolUsuario, VistaPago, VistaPerfilUsuario,
        VistaFacturas, VistaAjusteStock, VistaHistorialStockGeneral,
        VistaHistorialStockProducto, VistaStockProductos, VistaFactura,
        VistaDetalleFactura, VistaEnvio, VistaCarritoProducto, VistaPagos,
        VistaPagoPaypal, VistaPagoTarjeta, VistaPagoTransferencia
    )

    # Rutas de la API
    api.add_resource(VistaUsuario, '/usuario/<int:id_usuario>')
    api.add_resource(VistaUsuarios, '/usuarios')
    api.add_resource(VistaProducto, '/productos/<int:id_producto>')
    api.add_resource(VistaProductos, '/productos')
    api.add_resource(VistaCategoria, '/categoria/<int:id_categoria>')
    api.add_resource(VistaCategorias, '/categorias')
    api.add_resource(VistaLogin, '/login')
    api.add_resource(VistaSignIn, '/signin')
    api.add_resource(VistaCarritos, '/carritos')
    api.add_resource(VistaCarrito, '/carrito', endpoint='vista_carrito')
    api.add_resource(VistaCarrito, '/carrito/<int:id_carrito>/producto', endpoint='vista_carrito_producto')
    api.add_resource(VistaCarrito, '/carrito/<int:id_carrito>', endpoint='vista_carrito_detalle')
    api.add_resource(VistaPago, '/pago')
    api.add_resource(VistaPagos, '/pagos')
    api.add_resource(VistaTarjeta, '/pago/tarjeta')
    api.add_resource(VistaTransferencia, '/pago/transferencia')
    api.add_resource(VistaPaypal, '/pago/paypal')
    api.add_resource(VistaPerfilUsuario, '/perfil')
    api.add_resource(VistaRolUsuario, '/usuario/rol')
    api.add_resource(VistaCarritoActivo, '/carrito/activo', endpoint='vista_carrito_activo')
    api.add_resource(VistaProductosRecomendados, '/productos/recomendados')
    api.add_resource(VistaFactura, '/factura')
    api.add_resource(VistaDetalleFactura, '/detallefactura', '/detallefactura/<int:id_factura>')
    api.add_resource(VistaEnvio, '/envio')
    api.add_resource(VistaCarritoProducto, '/carrito_producto/<int:id_carrito>')
    api.add_resource(VistaPagoPaypal, '/pago/paypal/<int:id_pago>')
    api.add_resource(VistaPagoTransferencia, '/pago/transferencia/<int:id_pago>')
    api.add_resource(VistaPagoTarjeta, '/pago/tarjeta/<int:id_pago>')
    api.add_resource(VistaFacturas, '/facturas') 
    api.add_resource(VistaAjusteStock, '/productos/<int:id_producto>/ajuste-stock')
    api.add_resource(VistaHistorialStockProducto, '/productos/<int:id_producto>/historial-stock')
    api.add_resource(VistaHistorialStockGeneral, '/historial-stock')
    api.add_resource(VistaStockProductos, '/stock-productos')
    api.add_resource(VistaReportesProductos, '/reportes/productos-mas-vendidos')
    api.add_resource(VistaPedidosUsuario, '/api/mis-pedidos')
    api.add_resource(VistaUltimaFactura, '/factura/ultima')
    api.add_resource(VistaEstadoEnvio, '/api/envios/<int:id_orden>/estado')
    api.add_resource(VistaEnviosAdmin, '/api/admin/envios')
    api.add_resource(VistaActualizarEstadoAdmin, '/api/admin/envios/<int:id_envio>/estado')
    api.add_resource(VistaProductosBajoStock, '/api/productos/bajo-stock')

# Inicialización importante para migraciones
from .modelos import modelo