# LeetCode Amigos - Monthly Leaderboard

🎯 Una aplicación web simple para competir mensualmente resolviendo problemas de LeetCode entre amigos.

## Características

- **Gestión de usuarios**: Registro, login y autenticación
- **Problemas mensuales**: Los admins pueden agregar problemas diarios
- **Progreso personal**: Marcar problemas como resueltos y ver estadísticas
- **Tabla de posiciones**: Ranking basado en sistema de puntos
- **Panel admin**: Gestión de problemas y archivado mensual
- **Sistema de puntos**: Fácil=1, Medio=2, Difícil=3 puntos

## Tecnologías

- **Backend**: FastAPI + SQLModel
- **Base de datos**: SQLite
- **Frontend**: Jinja2 templates + Bootstrap 5
- **Autenticación**: JWT tokens

## Instalación

1. Clona el repositorio:
```bash
git clone <url>
cd leet-amigos
```

2. Instala dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecuta la aplicación:
```bash
python main.py
```

4. Visita `http://localhost:8000`

## Uso

### Admin (Usuario por defecto)
- **Usuario**: `admin`
- **Contraseña**: `admin123`

### Funcionalidades principales

1. **Página principal** (`/`): Lista de problemas activos con checkboxes para marcar progreso
2. **Mi progreso** (`/progreso`): Estadísticas personales y problemas resueltos
3. **Ranking** (`/ranking`): Tabla de posiciones ordenada por puntos
4. **Admin** (`/admin`): Agregar problemas y archivar meses

### Flujo mensual

1. Admin agrega problemas diarios
2. Usuarios marcan su progreso manualmente
3. El ranking se actualiza automáticamente
4. Al final del mes, admin archiva problemas y resetea progreso

## Estructura del proyecto

```
leet-amigos/
├── main.py              # Aplicación FastAPI principal
├── models.py            # Modelos SQLModel
├── auth.py              # Sistema de autenticación
├── database.py          # Configuración de base de datos
├── templates/           # Templates HTML
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── progreso.html
│   ├── ranking.html
│   ├── admin.html
│   └── archivados.html
├── static/
│   └── style.css        # Estilos CSS
└── requirements.txt     # Dependencias
```

## API Endpoints

### Web Routes
- `GET /` - Página principal
- `GET /login` - Formulario de login
- `POST /login` - Autenticación
- `GET /register` - Formulario de registro
- `POST /register` - Crear cuenta
- `GET /progreso` - Progreso personal
- `GET /ranking` - Tabla de posiciones
- `GET /admin` - Panel admin
- `POST /admin/problems` - Agregar problema
- `POST /admin/archive` - Archivar mes
- `GET /admin/archivados` - Ver archivos

### API Routes
- `POST /api/progress` - Actualizar progreso

## Desarrollo

Para desarrollo local:

```bash
# Ejecutar con recarga automática
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la licencia MIT.