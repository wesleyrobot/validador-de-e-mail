import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Gestão de Contatos",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def upload_file(file):
    files = {"file": (file.name, file, file.type)}
    return requests.post(f"{API_URL}/upload", files=files).json()

def get_job_status(job_id):
    return requests.get(f"{API_URL}/jobs/{job_id}").json()

def get_results(job_id, limit=5000):
    return requests.get(f"{API_URL}/results/{job_id}", params={"limit": limit}).json()

st.title("🗄️ Sistema de Gestão de Contatos")
st.markdown("**Validação DNS/MX · Normalização Automática · Exportação Inteligente**")

tab1, tab2, tab3 = st.tabs(["📤 Upload", "📊 Resultados", "⚙️ Config"])

# TAB 1: UPLOAD
with tab1:
    st.header("📤 Upload de Arquivo")
    
    uploaded_file = st.file_uploader(
        "Arraste ou selecione um arquivo",
        type=["xlsx", "xls", "csv"],
        help="Formatos: Excel (.xlsx, .xls) ou CSV"
    )
    
    if uploaded_file:
        st.success(f"✅ {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
    
    if uploaded_file and st.button("🚀 Processar Arquivo", type="primary", use_container_width=True):
        with st.spinner("Processando..."):
            try:
                result = upload_file(uploaded_file)
                st.session_state['job_id'] = result['job_id']
                st.success(f"✅ Job ID: `{result['job_id']}`")
                st.info("💡 Vá para 'Resultados' para acompanhar")
            except Exception as e:
                st.error(f"❌ Erro: {e}")

# TAB 2: RESULTADOS
with tab2:
    st.header("📊 Resultados do Processamento")
    
    job_id = st.text_input(
        "Job ID",
        value=st.session_state.get('job_id', ''),
        placeholder="Cole o Job ID aqui"
    )
    
    if st.button("🔄 Atualizar Status", type="primary", use_container_width=True):
        if not job_id:
            st.warning("⚠️ Digite um Job ID primeiro")
        else:
            try:
                with st.spinner("Buscando dados..."):
                    status = get_job_status(job_id)
                    
                    st.session_state['status_data'] = status
                    st.session_state['last_update'] = datetime.now().strftime("%H:%M:%S")
                    
                    st.success("✅ Dados atualizados!")
            except Exception as e:
                st.error(f"❌ Erro: {e}")
    
    if 'status_data' in st.session_state and job_id:
        status = st.session_state['status_data']
        
        if 'last_update' in st.session_state:
            st.caption(f"⏰ Última atualização: {st.session_state['last_update']}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Status", status.get('status', 'N/A').upper())
        with col2:
            st.metric("⏱️ Progresso", f"{status.get('progress', 0)}%")
        with col3:
            st.metric("📋 Total", status.get('total_rows', 0))
        with col4:
            if status.get('status') == 'done':
                st.success("✅ CONCLUÍDO")
            elif status.get('status') == 'processing':
                st.info("⏳ PROCESSANDO")
            else:
                st.warning("⚠️ AGUARDANDO")
        
        st.progress(status.get('progress', 0) / 100)
        
        if status.get('status') == 'done':
            st.markdown("---")
            
            try:
                results = get_results(job_id, limit=5000)
                
                if not results.get('data'):
                    st.error("❌ Nenhum dado encontrado")
                else:
                    df = pd.DataFrame(results['data'])
                    
                    st.subheader(f"📋 Dados Processados ({len(df)} contatos)")
                    
                    display_cols = ['nome', 'email', 'telefone', 'empresa', 'cargo', 'email_validation_status']
                    display_cols = [c for c in display_cols if c in df.columns]
                    st.dataframe(df[display_cols].head(100), use_container_width=True, height=400)
                    
                    st.markdown("---")
                    st.subheader("📥 Downloads")
                if status.get('status') == 'done':
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### 📋 Download Completo")
                        st.markdown("[⬇️ Baixar Excel](http://SEU_SERVIDOR_AQUI/api/download/" + job_id + "?format=xlsx)")
                        st.markdown("[⬇️ Baixar CSV](http://SEU_SERVIDOR_AQUI/api/download/" + job_id + "?format=csv)")
                    
                    with col2:
                        st.markdown("### 📧 Nome + E-mail")
                        st.markdown("[⬇️ Baixar Excel Filtrado](http://SEU_SERVIDOR_AQUI/api/download/" + job_id + "/filtered?format=xlsx&valid_only=true)")
                        st.markdown("[⬇️ Baixar CSV Filtrado](http://SEU_SERVIDOR_AQUI/api/download/" + job_id + "/filtered?format=csv&valid_only=true)")
                    
                    st.info("💡 Download filtrado contém apenas Nome e E-mail válidos")
            
            except Exception as e:
                st.error(f"❌ Erro ao carregar resultados: {e}")

# TAB 3: CONFIG
with tab3:
    st.header("⚙️ Configurações")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔧 Recursos")
        st.markdown("- ✅ Validação DNS/MX")
        st.markdown("- ✅ Normalização de emails")
        st.markdown("- ✅ Telefones brasileiros")
    
    with col2:
        st.markdown("### 📊 Status")
        try:
            resp = requests.get(f"{API_URL}/", timeout=2)
            if resp.status_code == 200:
                st.success("✅ API Online")
            else:
                st.warning(f"⚠️ API: {resp.status_code}")
        except:
            st.error("❌ API Offline")

# SIDEBAR
with st.sidebar:
    st.markdown('<div style="text-align:center;font-size:60px;">🗄️</div>', unsafe_allow_html=True)
    st.title("Gestão de Contatos")
    st.markdown("---")
    
    st.markdown("### 🚀 Como usar")
    st.markdown("1. **Upload**: Envie arquivo")
    st.markdown("2. **Aguarde**: Sistema processa")
    st.markdown("3. **Resultados**: Veja dados")
    st.markdown("4. **Baixe**: Exporte filtrado")
    
    st.markdown("---")
    
    if st.session_state.get('job_id'):
        st.markdown("### 📋 Job Atual")
        st.code(st.session_state['job_id'], language=None)
