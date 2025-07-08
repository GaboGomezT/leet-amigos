from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from datetime import datetime, timedelta
from typing import List, Optional
import os
import csv
import io

from models import (
    User, Problem, UserProgress, DifficultyEnum,
    UserCreate, UserLogin, ProblemCreate, ProgressUpdate
)
from database import get_session, init_db
from auth import (
    authenticate_user, create_access_token, get_current_user,
    get_current_admin_user, get_password_hash, get_current_user_optional
)

app = FastAPI(title="LeetCode Amigos", description="Monthly LeetCode Leaderboard")

# Initialize database
init_db()

# Templates and static files
templates = Jinja2Templates(directory="templates")
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Utility functions
def get_current_month_year() -> str:
    """Get current month in YYYY-MM format"""
    return datetime.utcnow().strftime("%Y-%m")


def get_current_month_name() -> str:
    """Get current month name in Spanish"""
    months = {
        "01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril",
        "05": "Mayo", "06": "Junio", "07": "Julio", "08": "Agosto", 
        "09": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"
    }
    current_date = datetime.utcnow()
    month_key = current_date.strftime("%m")
    year = current_date.strftime("%Y")
    return f"{months[month_key]} {year}"


def get_user_points(user: User, session: Session, month_year: str = None) -> int:
    """Get user points for a specific month (default: current month)"""
    if month_year is None:
        month_year = get_current_month_year()
    
    statement = select(UserProgress, Problem).join(Problem).where(
        UserProgress.user_id == user.id,
        UserProgress.is_solved == True,
        UserProgress.month_year == month_year
    )
    results = session.exec(statement).all()
    
    total_points = 0
    for progress, problem in results:
        if problem.difficulty == DifficultyEnum.EASY:
            total_points += 1
        elif problem.difficulty == DifficultyEnum.MEDIUM:
            total_points += 2
        elif problem.difficulty == DifficultyEnum.HARD:
            total_points += 3
    
    return total_points


def get_user_solved_count(user: User, session: Session, month_year: str = None) -> int:
    """Get count of solved problems for a specific month (default: current month)"""
    if month_year is None:
        month_year = get_current_month_year()
    
    statement = select(UserProgress).join(Problem).where(
        UserProgress.user_id == user.id,
        UserProgress.is_solved == True,
        UserProgress.month_year == month_year
    )
    return len(session.exec(statement).all())


# Web Routes
@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request, 
    session: Session = Depends(get_session),
    difficulty: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None
):
    current_user = get_current_user_from_cookie(request, session)
    
    # Build filtered query for all problems
    statement = select(Problem)
    
    # Apply filters
    if difficulty:
        statement = statement.where(Problem.difficulty == difficulty)
    if category:
        statement = statement.where(Problem.category == category)
    
    statement = statement.order_by(Problem.created_at.desc())
    problems = session.exec(statement).all()
    
    # Get user progress if logged in (for current month)
    user_progress = {}
    if current_user:
        current_month = get_current_month_year()
        statement = select(UserProgress).where(
            UserProgress.user_id == current_user.id,
            UserProgress.month_year == current_month
        )
        progress_list = session.exec(statement).all()
        user_progress = {p.problem_id: p.is_solved for p in progress_list}
        
        # Filter by status if specified
        if status == "solved":
            problems = [p for p in problems if user_progress.get(p.id, False)]
        elif status == "unsolved":
            problems = [p for p in problems if not user_progress.get(p.id, False)]
    
    # Get unique categories for filter dropdown
    all_problems = session.exec(select(Problem)).all()
    categories = sorted(set(p.category for p in all_problems if p.category))
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "problems": problems,
        "current_user": current_user,
        "user_progress": user_progress,
        "categories": categories,
        "selected_difficulty": difficulty,
        "selected_category": category,
        "selected_status": status,
        "current_month_name": get_current_month_name()
    })


@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    user = authenticate_user(session, username, password)
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Usuario o contraseña incorrectos"
        })
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response


@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    # Check if user exists
    statement = select(User).where(User.username == username)
    existing_user = session.exec(statement).first()
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "El usuario ya existe"
        })
    
    # Create new user
    user = User(
        username=username,
        password_hash=get_password_hash(password),
        is_admin=False
    )
    session.add(user)
    session.commit()
    
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response


def get_current_user_from_cookie(request: Request, session: Session) -> Optional[User]:
    try:
        token = request.cookies.get("access_token")
        if token and token.startswith("Bearer "):
            from fastapi.security import HTTPAuthorizationCredentials
            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token[7:])
            return get_current_user_optional(session=session, credentials=credentials)
    except:
        pass
    return None


@app.get("/progreso", response_class=HTMLResponse)
async def progress(request: Request, session: Session = Depends(get_session)):
    current_user = get_current_user_from_cookie(request, session)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Get user's solved problems for current month
    current_month = get_current_month_year()
    statement = select(UserProgress, Problem).join(Problem).where(
        UserProgress.user_id == current_user.id,
        UserProgress.month_year == current_month
    )
    results = session.exec(statement).all()
    
    solved_problems = []
    total_points = 0
    
    for progress, problem in results:
        if progress.is_solved:
            points = 1 if problem.difficulty == DifficultyEnum.EASY else 2 if problem.difficulty == DifficultyEnum.MEDIUM else 3
            total_points += points
            solved_problems.append({
                "problem": problem,
                "points": points,
                "solved_at": progress.solved_at
            })
    
    return templates.TemplateResponse("progreso.html", {
        "request": request,
        "current_user": current_user,
        "solved_problems": solved_problems,
        "total_points": total_points,
        "total_solved": len(solved_problems)
    })


@app.get("/ranking", response_class=HTMLResponse)
async def ranking(
    request: Request, 
    session: Session = Depends(get_session),
    mode: Optional[str] = None
):
    current_user = get_current_user_from_cookie(request, session)
    
    # Default to points mode if not specified
    if mode not in ["points", "problems"]:
        mode = "points"
    
    # Get all users with their points
    statement = select(User).where(User.is_admin == False)
    users = session.exec(statement).all()
    
    user_stats = []
    for user in users:
        points = get_user_points(user, session)
        solved_count = get_user_solved_count(user, session)
        user_stats.append({
            "user": user,
            "points": points,
            "solved_count": solved_count
        })
    
    # Sort based on selected mode
    if mode == "problems":
        user_stats.sort(key=lambda x: x["solved_count"], reverse=True)
    else:  # default to points
        user_stats.sort(key=lambda x: x["points"], reverse=True)
    
    return templates.TemplateResponse("ranking.html", {
        "request": request,
        "current_user": current_user,
        "user_stats": user_stats,
        "current_mode": mode,
        "current_month_name": get_current_month_name()
    })


# API Routes
# Admin Routes
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, session: Session = Depends(get_session)):
    current_user = get_current_user_from_cookie(request, session)
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Get all problems
    statement = select(Problem).order_by(Problem.created_at.desc())
    problems = session.exec(statement).all()
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "current_user": current_user,
        "admin_user": current_user,
        "problems": problems
    })


@app.post("/admin/problems")
async def add_problem(
    request: Request,
    title: str = Form(...),
    url: str = Form(...),
    solution_url: str = Form(""),
    difficulty: DifficultyEnum = Form(...),
    category: str = Form(...),
    session: Session = Depends(get_session)
):
    current_user = get_current_user_from_cookie(request, session)
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Check for duplicate URL
    existing_problem = session.exec(select(Problem).where(Problem.url == url)).first()
    if existing_problem:
        return templates.TemplateResponse("admin.html", {
            "request": request,
            "current_user": current_user,
            "admin_user": current_user,
            "problems": session.exec(select(Problem)).all(),
            "error": f"Ya existe un problema con esta URL: {url}"
        })
    
    problem = Problem(
        title=title,
        url=url,
        solution_url=solution_url if solution_url else None,
        difficulty=difficulty,
        category=category if category else None
    )
    session.add(problem)
    session.commit()
    
    return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)


@app.post("/admin/upload-csv")
async def upload_problems_csv(
    request: Request,
    csv_file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    current_user = get_current_user_from_cookie(request, session)
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    if not csv_file.filename.endswith('.csv'):
        return templates.TemplateResponse("admin.html", {
            "request": request,
            "current_user": current_user,
            "admin_user": current_user,
            "problems": session.exec(select(Problem)).all(),
            "error": "El archivo debe ser un CSV"
        })
    
    try:
        # Read CSV content
        content = await csv_file.read()
        csv_content = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        
        added_count = 0
        skipped_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 because row 1 is headers
            try:
                # Map CSV columns to our fields
                name = row.get('Name', '').strip()
                link = row.get('Link', '').strip()
                difficulty = row.get('Difficulty', '').strip().lower()
                category = row.get('Category', '').strip()
                
                if not all([name, link, difficulty]):
                    errors.append(f"Fila {row_num}: Faltan campos requeridos (Name, Link, Difficulty)")
                    continue
                
                # Validate difficulty
                if difficulty not in ['easy', 'medium', 'hard']:
                    errors.append(f"Fila {row_num}: Dificultad inválida '{difficulty}'. Debe ser: easy, medium, hard")
                    continue
                
                # Check for duplicate URL
                existing_problem = session.exec(select(Problem).where(Problem.url == link)).first()
                if existing_problem:
                    skipped_count += 1
                    continue
                
                # Create new problem
                problem = Problem(
                    title=name,
                    url=link,
                    solution_url=None,
                    difficulty=DifficultyEnum(difficulty),
                    category=category
                )
                session.add(problem)
                added_count += 1
                
            except Exception as e:
                errors.append(f"Fila {row_num}: Error procesando - {str(e)}")
        
        session.commit()
        
        # Prepare success message
        message = f"CSV procesado: {added_count} problemas agregados, {skipped_count} duplicados omitidos"
        if errors:
            message += f". {len(errors)} errores encontrados."
        
        return templates.TemplateResponse("admin.html", {
            "request": request,
            "current_user": current_user,
            "admin_user": current_user,
            "problems": session.exec(select(Problem)).all(),
            "success": message,
            "csv_errors": errors if errors else None
        })
        
    except Exception as e:
        return templates.TemplateResponse("admin.html", {
            "request": request,
            "current_user": current_user,
            "admin_user": current_user,
            "problems": session.exec(select(Problem)).all(),
            "error": f"Error procesando CSV: {str(e)}"
        })




@app.get("/admin/history", response_class=HTMLResponse)
async def monthly_history(request: Request, session: Session = Depends(get_session)):
    current_user = get_current_user_from_cookie(request, session)
    if not current_user or not current_user.is_admin:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Get all unique months from user progress
    statement = select(UserProgress.month_year).distinct()
    months = session.exec(statement).all()
    
    # Get statistics for each month
    monthly_stats = []
    for month in sorted(months, reverse=True):
        # Get users who participated in this month
        statement = select(UserProgress).where(
            UserProgress.month_year == month,
            UserProgress.is_solved == True
        )
        progress_records = session.exec(statement).all()
        
        user_stats = {}
        for progress in progress_records:
            if progress.user_id not in user_stats:
                user_stats[progress.user_id] = {"solved": 0, "points": 0}
            user_stats[progress.user_id]["solved"] += 1
            
            # Get problem difficulty for points
            problem = session.exec(select(Problem).where(Problem.id == progress.problem_id)).first()
            if problem:
                points = 1 if problem.difficulty == DifficultyEnum.EASY else 2 if problem.difficulty == DifficultyEnum.MEDIUM else 3
                user_stats[progress.user_id]["points"] += points
        
        # Get usernames
        users_data = []
        for user_id, stats in user_stats.items():
            user = session.exec(select(User).where(User.id == user_id)).first()
            if user:
                users_data.append({
                    "username": user.username,
                    "solved": stats["solved"],
                    "points": stats["points"]
                })
        
        users_data.sort(key=lambda x: x["points"], reverse=True)
        
        monthly_stats.append({
            "month": month,
            "users": users_data,
            "total_participants": len(users_data)
        })
    
    return templates.TemplateResponse("history.html", {
        "request": request,
        "current_user": current_user,
        "admin_user": current_user,
        "monthly_stats": monthly_stats
    })


@app.post("/api/solve-problem/{problem_id}")
async def solve_problem(
    problem_id: int,
    request: Request,
    session: Session = Depends(get_session)
):
    current_user = get_current_user_from_cookie(request, session)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if problem exists
    problem = session.exec(select(Problem).where(Problem.id == problem_id)).first()
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    
    # Check if progress exists for current month
    current_month = get_current_month_year()
    statement = select(UserProgress).where(
        UserProgress.user_id == current_user.id,
        UserProgress.problem_id == problem_id,
        UserProgress.month_year == current_month
    )
    existing_progress = session.exec(statement).first()
    
    if existing_progress:
        if existing_progress.is_solved:
            return {"message": "Problema ya resuelto", "already_solved": True}
        existing_progress.is_solved = True
        existing_progress.solved_at = datetime.utcnow()
    else:
        new_progress = UserProgress(
            user_id=current_user.id,
            problem_id=problem_id,
            is_solved=True,
            solved_at=datetime.utcnow(),
            month_year=current_month
        )
        session.add(new_progress)
    
    session.commit()
    return {"message": "¡Problema resuelto exitosamente!", "solved": True}


@app.post("/api/progress")
async def update_progress(
    request: Request,
    progress_data: ProgressUpdate,
    session: Session = Depends(get_session)
):
    current_user = get_current_user_from_cookie(request, session)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if progress exists
    statement = select(UserProgress).where(
        UserProgress.user_id == current_user.id,
        UserProgress.problem_id == progress_data.problem_id
    )
    existing_progress = session.exec(statement).first()
    
    if existing_progress:
        existing_progress.is_solved = progress_data.is_solved
        existing_progress.solved_at = datetime.utcnow() if progress_data.is_solved else None
    else:
        new_progress = UserProgress(
            user_id=current_user.id,
            problem_id=progress_data.problem_id,
            is_solved=progress_data.is_solved,
            solved_at=datetime.utcnow() if progress_data.is_solved else None
        )
        session.add(new_progress)
    
    session.commit()
    return {"message": "Progreso actualizado"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)