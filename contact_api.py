"""
Sistema de Gestão de Contatos - API Principal
Requisitos: pip install fastapi uvicorn pandas openpyxl dnspython email-validator python-multipart redis
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import pandas as pd
import uuid
import os
from datetime import datetime
import json

app = FastAPI(
    title="Sistema de Gestão de Contatos",
    description="Upload, validação, categorização e exportação de contatos",
    version="1.0.0",
)

# CORS para frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Armazenamento em memória (em produção usar Redis/PostgreSQL)

def load_jobs_from_disk():
    """Recarrega Jobs do diretório results/"""
    loaded = 0
    if os.path.exists(RESULTS_DIR):
        for filename in os.listdir(RESULTS_DIR):
            if filename.endswith('_processed.json'):
                job_id = filename.replace('_processed.json', '')
                
                # Verificar se já existe
                if job_id in JOBS:
                    continue
                
                # Carregar arquivo para obter total_rows
                json_path = os.path.join(RESULTS_DIR, filename)
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        total_rows = len(data)
                    
                    # Adicionar ao dicionário JOBS
                    JOBS[job_id] = {
                        "status": "done",
                        "progress": 100,
                        "total_rows": total_rows,
                        "message": "Carregado do disco"
                    }
                    loaded += 1
                    print(f"✅ Job carregado: {job_id} ({total_rows} linhas)")
                except Exception as e:
                    print(f"⚠️ Erro ao carregar {job_id}: {e}")
    
    print(f"📊 Total de Jobs recarregados: {loaded}")
    return loaded


JOBS = {}
UPLOAD_DIR = "uploads"
RESULTS_DIR = "results"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# ===== MODELS =====
class JobStatus(BaseModel):
    job_id: str
    status: str  # processing, done, error
    progress: int
    total_rows: int
    created_at: str
    completed_at: Optional[str]
    error_message: Optional[str]

class CategorizeRequest(BaseModel):
    by: str  # "cargo", "empresa", "pais", "custom"
    rules: Optional[Dict[str, Any]] = None

class FilterRequest(BaseModel):
    email_valid: Optional[bool] = None
    categoria: Optional[str] = None
    empresa: Optional[str] = None
    limit: int = 100
    offset: int = 0

# ===== ENDPOINTS =====

@app.get("/")
async def root():
    return {
        "message": "Sistema de Gestão de Contatos API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /upload",
            "status": "GET /jobs/{job_id}",
            "results": "GET /results/{job_id}",
            "categorize": "POST /actions/{job_id}/categorize",
            "download": "GET /download/{job_id}"
        }
    }

@app.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload de arquivo Excel com contatos
    """
    # Validar tipo de arquivo
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(400, "Formato inválido. Use Excel (.xlsx, .xls) ou CSV")
    
    # Criar job
    job_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{job_id}_{file.filename}")
    
    # Salvar arquivo
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Inicializar job
    JOBS[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "progress": 0,
        "total_rows": 0,
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "error_message": None,
        "file_path": file_path,
        "filename": file.filename
    }
    
    # Processar em background
    background_tasks.add_task(process_file, job_id, file_path)
    
    return {"job_id": job_id, "status": "processing", "message": "Processamento iniciado"}

@app.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Consultar status do processamento
    """
    if job_id not in JOBS:
        raise HTTPException(404, "Job não encontrado")
    
    job = JOBS[job_id]
    return {
        "job_id": job_id,
        "status": job.get("status", "unknown"),
        "progress": job.get("progress", 0),
        "total_rows": job.get("total_rows", 0),
        "message": job.get("message", "")
    }

@app.get("/results/{job_id}")
async def get_results(job_id: str, limit: int = 100, offset: int = 0):
    """
    Obter resultados processados com paginação
    """
    if job_id not in JOBS:
        raise HTTPException(404, "Job não encontrado")
    
    job = JOBS[job_id]
    if job["status"] != "done":
        raise HTTPException(400, "Processamento ainda não concluído")
    
    result_path = os.path.join(RESULTS_DIR, f"{job_id}_processed.json")
    if not os.path.exists(result_path):
        raise HTTPException(404, "Resultados não encontrados")
    
    with open(result_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    total = len(data)
    paginated = data[offset:offset + limit]
    
    return {
        "job_id": job_id,
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": paginated
    }

@app.post("/actions/{job_id}/categorize")
async def categorize_contacts(job_id: str, request: CategorizeRequest):
    """
    Aplicar categorização aos contatos
    """
    if job_id not in JOBS:
        raise HTTPException(404, "Job não encontrado")
    
    job = JOBS[job_id]
    if job["status"] != "done":
        raise HTTPException(400, "Processamento ainda não concluído")
    
    result_path = os.path.join(RESULTS_DIR, f"{job_id}_processed.json")
    with open(result_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Aplicar categorização
    from contact_processor import categorize_by_field
    categorized = categorize_by_field(data, request.by, request.rules)
    
    # Salvar resultado categorizado
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(categorized, f, ensure_ascii=False, indent=2)
    
    return {"message": f"Categorização aplicada por '{request.by}'", "total": len(categorized)}



@app.get("/api/download/{job_id}")
async def download_results(job_id: str, format: str = "xlsx"):
    """
    Baixar resultados processados em Excel ou CSV
    """
    if job_id not in JOBS:
        raise HTTPException(404, "Job não encontrado")
    
    job = JOBS[job_id]
    if job["status"] != "done":
        raise HTTPException(400, "Processamento ainda não concluído")
    
    result_path = os.path.join(RESULTS_DIR, f"{job_id}_processed.json")
    with open(result_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    
    if format == "xlsx":
        output_path = os.path.join(RESULTS_DIR, f"{job_id}_export.xlsx")
        df.to_excel(output_path, index=False, engine='openpyxl')
        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"contatos_processados_{job_id}.xlsx"
        )
    elif format == "csv":
        output_path = os.path.join(RESULTS_DIR, f"{job_id}_export.csv")
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        return FileResponse(
            output_path,
            media_type="text/csv",
            filename=f"contatos_processados_{job_id}.csv"
        )
    else:
        raise HTTPException(400, "Formato inválido. Use 'xlsx' ou 'csv'")

# ===== BACKGROUND PROCESSING =====

def process_file(job_id: str, file_path: str):
    """
    Processa arquivo em background
    """
    try:
        from contact_processor import ContactProcessor
        
        processor = ContactProcessor()
        
        # Ler arquivo
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        JOBS[job_id]["total_rows"] = len(df)
        JOBS[job_id]["progress"] = 10
        
        # Processar
        processed_data = processor.process_contacts(df, job_id, JOBS)
        
        # Salvar resultados
        result_path = os.path.join(RESULTS_DIR, f"{job_id}_processed.json")
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=2)
        
        # Atualizar status
        JOBS[job_id]["status"] = "done"
        JOBS[job_id]["progress"] = 100
        JOBS[job_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        JOBS[job_id]["status"] = "error"
        JOBS[job_id]["error_message"] = str(e)
        JOBS[job_id]["completed_at"] = datetime.now().isoformat()


@app.get("/api/download/{job_id}/filtered")
async def download_filtered(
    job_id: str, 
    format: str = "xlsx",
    fields: str = "nome,email",  # Campos para exportar
    valid_only: bool = True  # Apenas e-mails válidos
):
    """
    Baixar apenas campos específicos (nome e email)
    """
    if job_id not in JOBS:
        raise HTTPException(404, "Job não encontrado")
    
    job = JOBS[job_id]
    if job["status"] != "done":
        raise HTTPException(400, "Processamento ainda não concluído")
    
    result_path = os.path.join(RESULTS_DIR, f"{job_id}_processed.json")
    with open(result_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Filtrar apenas campos solicitados
    campos_lista = [c.strip() for c in fields.split(',')]
    
    # Adicionar sempre o status de validação para filtro
    if 'email_validation_status' not in campos_lista:
        campos_lista.append('email_validation_status')
    
    df = pd.DataFrame(data)
    
    # Filtrar apenas e-mails válidos se solicitado
    if valid_only and 'email_validation_status' in df.columns:
        df = df[df['email_validation_status'] == 'valid']
    
    # Selecionar apenas colunas solicitadas
    colunas_disponiveis = [c for c in campos_lista if c in df.columns]
    df_filtered = df[colunas_disponiveis]
    
    # Remover coluna de status se foi adicionada apenas para filtro
    if 'email_validation_status' not in fields.split(','):
        df_filtered = df_filtered.drop('email_validation_status', axis=1, errors='ignore')
    
    # Renomear colunas para português
    df_filtered = df_filtered.rename(columns={
        'nome': 'Nome',
        'email': 'E-mail',
        'telefone': 'Telefone',
        'empresa': 'Empresa',
        'cargo': 'Cargo'
    })
    
    if format == "xlsx":
        output_path = os.path.join(RESULTS_DIR, f"{job_id}_filtered.xlsx")
        df_filtered.to_excel(output_path, index=False, engine='openpyxl')
        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"contatos_nome_email_{job_id}.xlsx"
        )
    elif format == "csv":
        output_path = os.path.join(RESULTS_DIR, f"{job_id}_filtered.csv")
        df_filtered.to_csv(output_path, index=False, encoding="utf-8-sig")
        return FileResponse(
            output_path,
            media_type="text/csv",
            filename=f"contatos_nome_email_{job_id}.csv"
        )
    else:
        raise HTTPException(400, "Formato inválido")



@app.on_event("startup")
async def startup_event():
    """Executado ao iniciar a API"""
    print("🚀 Iniciando API...")
    load_jobs_from_disk()
    print("✅ API pronta!")


# Incluir router com prefixo /api
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)