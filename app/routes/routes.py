import logging
from functools import wraps

from flask import render_template, Blueprint, request, jsonify, session, redirect, url_for, make_response, flash, abort
from flask_login import login_user, logout_user, login_required, login_manager

from app.services.PersonaServicioImpl import ElectorServiceImpl
from app.services.EleccionServicioImpl import EleccionServicioImpl
from app.services.EleccionServicioImpl import ListaServicioImpl
from app.services.EleccionServicioImpl import CandidatoServicioImpl
from app.services.EleccionServicioImpl import VotoServicioImpl

from app.models.Elector import Elector
from app.models.Eleccion import Eleccion
from app.models.ListaCandidato import ListaCandidato
from app.models.Candidato import Candidato
from app.services.PersonaServicioImpl import ElectorServiceImpl
from app.services.EleccionServicioImpl import EleccionServicioImpl


from dotenv import load_dotenv
import os

load_dotenv()

import bcrypt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

##REGISTER_TEMPLATE = 'register.html'
LOGIN_ROUTE = 'home_bp.login'

home_bp = Blueprint('home_bp', __name__, template_folder='templates')

elector_service = ElectorServiceImpl()
eleccion_servicio = EleccionServicioImpl()
lista_servicio = ListaServicioImpl()
candidato_servicio = CandidatoServicioImpl()
voto_servicio = VotoServicioImpl()

def admin_required(f):
    @wraps(f)
    def decorated_function_admin(*args, **kwargs):
        logger.info(f"Verificando acceso: sesión actual {session}")
        if not session.get('admin'):
            logger.info(f"Usuario no autorizado, sesión: {session}")
            return render_template("login.html")  # Redirige a la ruta 'index' o la ruta de inicio
        return f(*args, **kwargs)
    return decorated_function_admin

@home_bp.route('/Admins')
@admin_required
def home():
    return render_template('Admin/home.html')


@home_bp.route('/ListaElecciones', methods=['GET'])
def mostrar_elecciones():
    eleccionesf = eleccion_servicio.get_all_eleccion(1)
    eleccionescurso = eleccion_servicio.get_all_eleccion(2)
    eleccionespro = eleccion_servicio.get_all_eleccion(3)
    return render_template('a/elecciones.html', eleccionespro=eleccionespro, eleccionesf=eleccionesf, eleccionescurso=eleccionescurso)


@home_bp.route('/ListasCandidatos', methods=['GET'])
def listar_candidatos():
    listas_json = lista_servicio.obtener_listas()
    return render_template('ListaCandidato/lista_candidatos.html', listas=listas_json)

@home_bp.route('/aprobar_lista/<int:id_lista>', methods=['PUT'])
def aprobar_lista(id_lista):
    try:
        lista_servicio.aprobar_lista(id_lista)
        return jsonify({'message': 'Lista aprobada exitosamente'}), 200
    except Exception as e:
        logger.error(f'Error al aprobar la lista: {str(e)}')
        return jsonify({'message': 'Error al aprobar la lista', 'error': str(e)}), 500

@home_bp.route('/desaprobar_lista/<int:id_lista>', methods=['PUT'])
def desaprobar_lista(id_lista):
    try:
        lista_servicio.desaprobar_lista(id_lista)
        return jsonify({'message': 'Lista desaprobada exitosamente'}), 200
    except Exception as e:
        logger.error(f'Error al desaprobar la lista: {str(e)}')
        return jsonify({'message': 'Error al desaprobar la lista', 'error': str(e)}), 500


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'correo' not in session:
            return redirect(url_for(LOGIN_ROUTE))
        return f(*args, **kwargs)
    return decorated_function


@home_bp.route('/ListasEleccionesVista', methods=['GET'])
def listar_candidatos_elector():
    listas = lista_servicio.obtener_listas_aprobadas()
    return render_template('ListaCandidato/listas_aprobadas.html', listas = listas)



@home_bp.route('/EleccionesActivas', methods=['GET'])
def listar_elecciones():
    elecciones_json = eleccion_servicio.get_all_eleccion(4)
    return render_template('lista_eleccion.html', elecciones = elecciones_json)


@home_bp.route('/candidatos/<int:id>', methods=['GET'])
def ver_lista_candidatos(id):
    listas_candidato = lista_servicio.get_lista_por_eleccion(id)

    if listas_candidato is None:
        abort(404)
    return render_template('ListaCandidato/lista_candidatos.html', listas=listas_candidato)

@home_bp.route('/ListasEleccionesVista', methods=['GET'])
def listas_candidatos_elector():
    listas = lista_servicio.obtener_listas_aprobadas()
    return render_template('ListaCandidato/listas_aprobadas.html', listas = listas)

@home_bp.route('/VerListas', methods=['POST'])
def ver_candidatos():
    id_eleccion = request.form['eleccion_id']
    result = lista_servicio.get_lista_by_eleccion(id_eleccion)
    return render_template("lista_candidatos.html", data = result)


@home_bp.route('/FormularioEleccion', methods=['GET'])
def agregar_eleccion():
    return render_template("ProcesoVotacion/form_eleccion.html")


@home_bp.route('/InsertEleccion', methods=['POST'])
def insert_eleccion():
    fecha = request.form['fecha']
    hora_inicio = request.form['hora_inicio']
    hora_fin = request.form['hora_fin']
    estado = request.form['estado']
    descripcion = request.form['descripcion']
    eleccion = Eleccion(fecha, hora_inicio, hora_fin, estado, descripcion)
    eleccion_servicio.insert_eleccion(eleccion)
    return url_for('home_bp.listar_elecciones')


@home_bp.route('/Votos')
def ver_votos():
    votos = voto_servicio.get_cant_votos_by_eleccion()
    return render_template("ProcesoVotacion/votos.html", data = votos)


@home_bp.route('/EleccionVotacion', methods=['GET'])
@login_required
def seleccionar_eleccion_votacion():
    elector = eleccion_servicio.get_elector_by_email(session['correo'])
    voto = voto_servicio.get_voto_by_elector(elector.id)
    if voto:
        return redirect(url_for('home_bp.dashboard'))
    elecciones_abiertas_json = eleccion_servicio.get_all_eleccion_abiertas()
    return render_template('ProcesoVotacion/lista_eleccion_votacion.html', data = elecciones_abiertas_json)


@home_bp.route('/CandidatosVotacion', methods=['POST'])
@login_required
def ver_candidatos_votacion():
    id_eleccion = request.form['voto']
    candidatos = lista_servicio.get_lista_aprobada_by_eleccion(id_eleccion)
    return render_template('ProcesoVotacion/votacion.html', data = candidatos)

@home_bp.route('/Resumen', methods=['POST'])
@login_required
def resumir_votacion():
    id_lista = request.form['id_lista']
    lista = lista_servicio.get_lista_by_id(id_lista)
    return render_template('ProcesoVotacion/resumen.html', data = lista)


@home_bp.route('/Votar', methods=['POST'])
@login_required
def votar():
    id_lista = request.form['id_lista']
    elector = eleccion_servicio.get_elector_by_email(session['correo'])
    voto_servicio.votar(id_lista, elector.id)
    return redirect(url_for('home_bp.dashboard'))


@home_bp.route('/')
def index():
    return render_template('index.html')

@home_bp.route('/register', methods=['GET','POST'])
def register():
    REGISTER_HTML = 'register.html'
    try:
        if request.method == 'POST':
            data = request.form
            elector = Elector(
                nombres=data.get('nombres'),
                apellido_paterno=data.get('apellido_paterno'),
                apellido_materno=data.get('apellido_materno'),
                fecha_nacimiento=data.get('fecha_nacimiento'),
                usuario=data.get('usuario'),
                contrasena=data.get('contrasena'),
                correo=data.get('correo')
            )

            elector_service.create_elector(elector,data.get('contrasena'))
            mensaje = 'Elector creado correctamente'
            return render_template(REGISTER_HTML, mensaje=mensaje)

        return render_template(REGISTER_HTML)
    except Exception as e:
        mensaje_error = f"Error al crear el elector: {str(e)}"
        logger.error(mensaje_error)
        return render_template(REGISTER_HTML, mensaje=mensaje_error)


@home_bp.route('/login', methods=['GET','POST'])
def login():
    LOGIN_HTML = 'login.html'
    try:
        if request.method == 'POST':
            data = request.form
            correo = data.get('correo')
            contrasena = data.get('contrasena')
            admin_email = os.getenv('ADMIN_EMAIL')
            admin_password = os.getenv('ADMIN_PASSWORD')
            if correo == admin_email and bcrypt.checkpw(contrasena.encode('utf-8'), admin_password.encode('utf-8')):
                session['correo'] = admin_email
                session['admin'] = True
                return render_template('Admin/home.html')
            elector = Elector.query.filter_by(correo=correo).first()
            if elector is None:
                mensaje = 'Correo o contraseña incorrectos'
                return render_template(LOGIN_HTML, mensaje=mensaje)
            voto = voto_servicio.get_voto_by_elector(elector.id)
            if elector and elector.revisar_contrasena(contrasena):
                session['correo'] = elector.correo
                logger.info(f'El elector {elector.nombres} ha iniciado sesión')
                return render_template('dashboard.html', elector=elector, voto=voto)
            else:
                mensaje = 'Correo o contraseña incorrectos'
                return render_template(LOGIN_HTML, mensaje=mensaje)
        return render_template(LOGIN_HTML)
    except Exception as e:
        mensaje_error = f"Error al iniciar sesión: {str(e)}"
        logger.error(mensaje_error)
        return render_template(LOGIN_HTML, mensaje=mensaje_error)


@home_bp.route('/dashboard')
@login_required
def dashboard():
    if 'correo' in session:
        elector = eleccion_servicio.get_elector_by_email(session['correo'])
        voto = voto_servicio.get_voto_by_elector(elector.id)
        response = make_response(render_template('dashboard.html', elector=elector, voto=voto))
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Pragma'] = 'no-cache'
        return response
    logger.warning('El usuario no ha iniciado sesión')
    return redirect(url_for(LOGIN_ROUTE))


@home_bp.route('/logout')
def logout():
    if 'correo' in session:
        logger.info(f'El elector {session["correo"]} ha cerrado sesión')
        session.pop('correo', None)
        session.clear()
    return redirect(url_for(LOGIN_ROUTE))


@home_bp.route('/electores/<int:id>', methods=['GET'])
def get_elector(id):
    return


@home_bp.route('/electores/<int:id>', methods=['PUT'])
def actualizar_elector(id):
    return


@home_bp.route('/electores/<int:id>', methods=['DELETE'])
def eliminar_elector(id):
    return


@home_bp.route('/candidatos')
def mostrar_candidatos():
    candidatos_inscritos = candidato_servicio.get_candidatos_inscritos()

    return render_template(
        'a/candidatos.html',
        candidatos_inscritos=candidatos_inscritos
    )
