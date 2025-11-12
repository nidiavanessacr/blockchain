from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from algosdk.v2client import algod, indexer
from algosdk import account, transaction, mnemonic
from .models import Wallet, Alumno, User, Actividad, Transaccion, ActividadAsignada
from .forms import ActividadForm
import base64
import time

# =========================
# CONFIGURACIÓN ALGOD
# =========================
ALGOD_CLIENT = algod.AlgodClient("", "https://testnet-api.algonode.cloud")


# =========================
# HELPERS
# =========================
def _to_private_key(stored_key):
    """Convierte el valor almacenado en la BD a la private key que .sign() acepta."""
    if stored_key is None:
        raise ValueError("No private key provided")

    if isinstance(stored_key, (bytes, bytearray)):
        return stored_key

    if isinstance(stored_key, str):
        # mnemonic de 25 palabras
        if len(stored_key.split()) == 25:
            try:
                return mnemonic.to_private_key(stored_key)
            except Exception:
                pass

        # base64
        try:
            decoded = base64.b64decode(stored_key)
            if decoded:
                return decoded
        except Exception:
            pass

        # raw
        return stored_key.encode()

    raise ValueError("Formato de private_key no soportado")


def wait_for_confirmation(client, txid, timeout=20):
    """Espera la confirmación de la transacción en la blockchain."""
    start = time.time()
    while True:
        try:
            pt = client.pending_transaction_info(txid)
        except Exception as e:
            raise e

        if pt.get("confirmed-round", 0) > 0:
            return pt

        if time.time() - start > timeout:
            raise TimeoutError("Timeout esperando confirmación")

        time.sleep(1)


# =========================
# AUTENTICACIÓN
# =========================
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            if user.role == 'admin':
                return redirect('dashboard_admin')
            elif user.role == 'docente':
                return redirect('dashboard_docente')
            else:
                return redirect('dashboard_estudiante')
        else:
            return render(request, 'wallet/login.html', {'error': 'Credenciales incorrectas'})

    return render(request, 'wallet/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def registro_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        rol = request.POST.get('rol')

        if not username or not password or not rol:
            return render(request, 'wallet/registro.html', {'error': 'Completa todos los campos'})

        if User.objects.filter(username=username).exists():
            return render(request, 'wallet/registro.html', {'error': 'El usuario ya existe'})

        user = User.objects.create_user(username=username, password=password, role=rol)
        private_key, address = account.generate_account()
        Wallet.objects.create(user=user, address=address, private_key=private_key)

        messages.success(request, "Cuenta creada exitosamente. Inicia sesión para continuar.")
        return redirect('login')

    return render(request, 'wallet/registro.html')


# =========================
# DASHBOARDS
# =========================
@login_required
def dashboard_admin(request):
    docentes = User.objects.filter(role='docente')
    estudiantes = User.objects.filter(role='estudiante')
    actividades = Actividad.objects.all().order_by('-fecha_creacion')

    return render(request, 'wallet/dashboard_admin.html', {
        'user': request.user,
        'docentes': docentes,
        'estudiantes': estudiantes,
        'total_docentes': docentes.count(),
        'total_estudiantes': estudiantes.count(),
        'actividades': actividades,
    })


@login_required
def dashboard_docente(request):
    wallet = getattr(request.user, 'wallet', None)
    alumnos = Alumno.objects.filter(user=request.user)
    actividades = Actividad.objects.filter(docente=request.user)

    return render(request, 'wallet/dashboard_docente.html', {
        'user': request.user,
        'wallet': wallet,
        'alumnos': alumnos,
        'num_alumnos': alumnos.count(),
        'actividades': actividades,
    })


@login_required
def dashboard_estudiante(request):
    wallet = getattr(request.user, 'wallet', None)

    if wallet:
        try:
            account_info = ALGOD_CLIENT.account_info(wallet.address)
            balance = account_info.get('amount', 0) / 1_000_000
            activos = len(account_info.get('assets', []))
        except Exception:
            balance = 0
            activos = 0
    else:
        balance = 0
        activos = 0

    return render(request, 'wallet/dashboard_estudiante.html', {
        'user': request.user,
        'wallet': wallet,
        'balance': balance,
        'activos': activos
    })


# =========================
# PÁGINAS GENERALES
# =========================
def index(request):
    return render(request, 'wallet/index.html')


def envio(request):
    return render(request, 'wallet/envio.html')


def info(request):
    return render(request, 'wallet/info.html')


# =========================
# ALUMNOS
# =========================
@login_required
def alumnos(request):
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        return render(request, "wallet/no_wallet.html")

    alumnos = Alumno.objects.filter(wallet=wallet)
    return render(request, 'wallet/alumno.html', {'alumnos': alumnos})


@login_required
def agregar_alumno(request):
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        return render(request, "wallet/no_wallet.html")

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        matricula = request.POST.get('matricula')
        if nombre and email and matricula:
            Alumno.objects.create(user=request.user, email=email, matricula=matricula, wallet=wallet)
            return redirect('alumnos')
        else:
            return render(request, 'wallet/agregar_alumno.html', {
                'mensaje': 'Completa todos los campos.',
                'wallet_address': wallet.address
            })

    return render(request, 'wallet/agregar_alumno.html', {'wallet_address': wallet.address})


# =========================
# WALLET
# =========================
@login_required
def mi_wallet(request):
    try:
        wallet = Wallet.objects.get(user=request.user)
        account_info = ALGOD_CLIENT.account_info(wallet.address)
    except Wallet.DoesNotExist:
        return render(request, "wallet/no_wallet.html")

    datos = {
        "user": request.user,
        "address": wallet.address,
        "balance": account_info.get('amount', 0) / 1_000_000,
        "txs": len(account_info.get('assets', [])),
    }
    return render(request, "wallet/mi_wallet.html", datos)


@login_required
def registrar_wallet(request):
    if request.method == "POST":
        if Wallet.objects.filter(user=request.user).exists():
            return render(request, "wallet/registrar_wallet.html", {
                "error": "Ya tienes una wallet registrada."
            })

        private_key, address = account.generate_account()
        Wallet.objects.create(user=request.user, address=address, private_key=private_key)
        return redirect("mi_wallet")

    return render(request, "wallet/registrar_wallet.html")


# =========================
# TRANSACCIONES
# =========================
@login_required
def transacciones(request):
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        return render(request, "wallet/no_wallet.html")

    client = indexer.IndexerClient("", "https://testnet-idx.algonode.cloud")
    try:
        response = client.search_transactions_by_address(wallet.address, limit=10)
        txs = response.get("transactions", [])
    except Exception as e:
        return render(request, "wallet/transacciones.html", {"txs": [], "error": str(e)})

    transacciones = []
    for tx in txs:
        tipo = tx.get("tx-type", "desconocido")
        monto = tx.get("payment-transaction", {}).get("amount", 0) / 1_000_000
        receptor = tx.get("payment-transaction", {}).get("receiver", "")
        remitente = tx.get("sender", "")
        fecha = tx.get("round-time", 0)
        transacciones.append({
            "tipo": tipo,
            "monto": monto,
            "receptor": receptor,
            "remitente": remitente,
            "fecha": fecha,
        })

    return render(request, "wallet/transacciones.html", {
        "transacciones": transacciones,
        "address": wallet.address,
    })


@login_required
def get_balance(request):
    address = request.GET.get('address', '')
    if not address:
        return JsonResponse({"error": "Missing address"}, status=400)

    try:
        account_info = ALGOD_CLIENT.account_info(address)
        balance = account_info.get('amount', 0) / 1_000_000
        return JsonResponse({"address": address, "balance": balance})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# =========================
# ACTIVIDADES
# =========================
@login_required
def crear_actividad(request):
    if request.user.role != "admin":
        return redirect('dashboard_admin')

    docentes = User.objects.filter(role="docente")

    if request.method == "POST":
        form = ActividadForm(request.POST)
        docente_id = request.POST.get('asignada_a')

        if form.is_valid():
            actividad = form.save(commit=False)
            actividad.docente = get_object_or_404(User, id=docente_id) if docente_id else request.user
            actividad.save()
            messages.success(request, "✅ Actividad creada correctamente.")
            return redirect('dashboard_admin')
    else:
        form = ActividadForm()

    return render(request, 'wallet/crear_actividad.html', {
        'form': form,
        'docentes': docentes
    })


@login_required
def asignar_actividad(request):
    if request.user.role != "docente":
        messages.error(request, "Solo los docentes pueden asignar actividades.")
        return redirect("dashboard_docente")

    docente = request.user
    actividades = Actividad.objects.filter(docente=docente)
    alumnos = Alumno.objects.all()

    if request.method == "POST":
        actividad_id = request.POST.get("actividad")
        alumno_id = request.POST.get("alumno")
        monto = float(request.POST.get("monto", 0))

        actividad = get_object_or_404(Actividad, id=actividad_id)
        alumno = get_object_or_404(Alumno, id=alumno_id)

        txid = None
        if monto > 0:
            try:
                sender_wallet = Wallet.objects.get(user=docente)
                receiver_wallet = alumno.wallet

                sender_sk = _to_private_key(sender_wallet.private_key)
                params = ALGOD_CLIENT.suggested_params()
                unsigned_txn = transaction.PaymentTxn(
                    sender_wallet.address,
                    params,
                    receiver_wallet.address,
                    int(monto * 1_000_000)
                )
                signed_txn = unsigned_txn.sign(sender_sk)
                txid = ALGOD_CLIENT.send_transaction(signed_txn)
                wait_for_confirmation(ALGOD_CLIENT, txid, 4)

                Transaccion.objects.create(
                    sender=docente.username,
                    receiver=alumno.user.username,
                    amount=monto,
                    txid=txid,
                    tipo="docente_to_alumno",
                    estado="confirmed"
                )
                messages.success(request, f"✅ Actividad asignada y {monto} ALGOs enviados (TxID: {txid[:8]}...)")
            except Exception as e:
                messages.error(request, f"Error al enviar ALGOs: {e}")

        ActividadAsignada.objects.create(
            actividad=actividad,
            docente=docente,
            alumno=alumno.user,
            estado="completada" if txid else "pendiente"
        )

        return redirect("asignar_actividad")

    return render(request, "wallet/asignar_actividad.html", {
        "actividades": actividades,
        "alumnos": alumnos
    })


# =========================
# ENVÍO DE ALGOS (ADMIN → DOCENTE)
# =========================
@login_required
def enviar_algos_admin(request):
    if request.user.role != "admin":
        messages.error(request, "Solo el administrador puede enviar ALGOs.")
        return redirect("dashboard_admin")

    docentes = User.objects.filter(role="docente")

    if request.method == "POST":
        docente_id = request.POST.get("docente")
        monto = float(request.POST.get("monto", 0))

        if not docente_id or monto <= 0:
            messages.error(request, "Selecciona un docente y un monto válido.")
            return redirect("enviar_algos_admin")

        docente = get_object_or_404(User, id=docente_id)
        admin_wallet = Wallet.objects.get(user=request.user)
        docente_wallet = Wallet.objects.get(user=docente)

        try:
            sender_sk = _to_private_key(admin_wallet.private_key)
            params = ALGOD_CLIENT.suggested_params()
            unsigned_txn = transaction.PaymentTxn(
                admin_wallet.address,
                params,
                docente_wallet.address,
                int(monto * 1_000_000)
            )
            signed_txn = unsigned_txn.sign(sender_sk)
            txid = ALGOD_CLIENT.send_transaction(signed_txn)
            wait_for_confirmation(ALGOD_CLIENT, txid, 4)

            Transaccion.objects.create(
                sender=request.user.username,
                receiver=docente.username,
                amount=monto,
                txid=txid,
                tipo="admin_to_docente",
                estado="confirmed"
            )

            messages.success(request, f"✅ {monto} ALGOs enviados a {docente.username} (TxID: {txid[:8]}...)")
        except Exception as e:
            messages.error(request, f"Error al enviar ALGOs: {e}")

        return redirect("enviar_algos_admin")

    return render(request, "wallet/enviar_algos_admin.html", {"docentes": docentes})
