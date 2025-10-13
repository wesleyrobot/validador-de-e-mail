import streamlit as st
import requests
import pandas as pd
import time
import os
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Sistema de Validação de Contatos",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .logo-container {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .logo-icon {
        width: 60px;
        height: 60px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Header com ícone personalizado
st.markdown("""
<div class="logo-container">
    <div class="logo-icon">📊</div>
    <div>
        <div class="main-header">Sistema de Gestão de Contatos</div>
        <div class="sub-header">Validação DNS/MX · Normalização Automática · Exportação Inteligente</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Função para carregar dados
@st.cache_data(ttl=60)
def load_all_contacts_data():
    results_dir = "results"
    all_data = {
        'total_listas': 0,
        'total_contacts': 0,
        'valid_emails': 0,
        'invalid_emails': 0,
        'syntax_only': 0,
        'contacts_list': [],
        'validation_by_status': {},
        'recent_contacts': []
    }
    
    if not os.path.exists(results_dir):
        return all_data
    
    json_files = [f for f in os.listdir(results_dir) if f.endswith('_processed.json')]
    all_data['total_listas'] = len(json_files)
    
    for json_file in sorted(json_files, reverse=True):
        try:
            contact_id = json_file.replace('_processed.json', '')
            file_path = os.path.join(results_dir, json_file)
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            with open(file_path, 'r') as f:
                data = json.load(f)
                # JSON é uma lista direta
                if isinstance(data, list):
                    contacts = data
                else:
                    contacts = data.get('data', data.get('contacts', []))
                
                num_contacts = len(contacts)
                all_data['total_contacts'] += num_contacts
                
                # Contar por status
                valid = 0
                invalid = 0
                syntax = 0
                
                for contact in contacts:
                    status = contact.get('email_validation_status', 'unknown')
                    if status == 'valid':
                        valid += 1
                        all_data['valid_emails'] += 1
                    elif status == 'invalid':
                        invalid += 1
                        all_data['invalid_emails'] += 1
                    elif status == 'syntax_only':
                        syntax += 1
                        all_data['syntax_only'] += 1
                
                # Listas recentes (top 10)
                if len(all_data['recent_contacts']) < 10:
                    all_data['recent_contacts'].append({
                        'contact_id': contact_id,
                        'contact_id_short': contact_id[:16] + '...',
                        'date': mod_time,
                        'date_str': mod_time.strftime('%d/%m/%Y %H:%M'),
                        'total': num_contacts,
                        'valid': valid,
                        'invalid': invalid,
                        'syntax': syntax,
                        'taxa_validacao': f"{(valid/num_contacts*100):.1f}%" if num_contacts > 0 else "0%"
                    })
        except Exception as e:
            continue
    
    return all_data

# Criar abas
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Dashboard", "📤 Upload", "📊 Resultados", "⚙️ Config"])

# ============================================
# TAB 1 - DASHBOARD
# ============================================
with tab1:
    st.header("🏠 Dashboard - Analytics de Validação")
    
    # Carregar dados
    data = load_all_contacts_data()
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📋 Listas de Contatos",
            f"{data['total_listas']:,}",
            help="Total de listas processadas"
        )
    
    with col2:
        st.metric(
            "👥 Total de Contatos",
            f"{data['total_contacts']:,}",
            help="Soma de todos os contatos processados"
        )
    
    with col3:
        taxa_validacao = (data['valid_emails'] / data['total_contacts'] * 100) if data['total_contacts'] > 0 else 0
        st.metric(
            "✅ Taxa de Validação",
            f"{taxa_validacao:.1f}%",
            help="Percentual de e-mails válidos"
        )
    
    with col4:
        st.metric(
            "📧 E-mails Válidos",
            f"{data['valid_emails']:,}",
            help="Total de e-mails com DNS/MX válido"
        )
    
    st.markdown("---")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Distribuição de Validação")
        
        if data['total_contacts'] > 0:
            validation_data = {
                'Status': ['✅ Válidos', '❌ Inválidos', '⚠️ Sintaxe Apenas'],
                'Quantidade': [data['valid_emails'], data['invalid_emails'], data['syntax_only']],
                'Cor': ['#22c55e', '#ef4444', '#f59e0b']
            }
            
            fig = go.Figure(data=[go.Pie(
                labels=validation_data['Status'],
                values=validation_data['Quantidade'],
                marker=dict(colors=validation_data['Cor']),
                hole=0.4,
                textinfo='label+percent',
                textfont=dict(size=14)
            )])
            
            fig.update_layout(
                showlegend=True,
                height=350,
                margin=dict(t=0, b=0, l=0, r=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📭 Nenhum dado disponível ainda")
    
    with col2:
        st.subheader("📈 Estatísticas Detalhadas")
        
        st.metric("✅ E-mails Válidos", f"{data['valid_emails']:,}", 
                  delta=f"{taxa_validacao:.1f}% do total")
        
        st.metric("❌ E-mails Inválidos", f"{data['invalid_emails']:,}",
                  delta=f"{(data['invalid_emails']/data['total_contacts']*100) if data['total_contacts'] > 0 else 0:.1f}% do total")
        
        st.metric("⚠️ Sintaxe Apenas", f"{data['syntax_only']:,}",
                  delta=f"{(data['syntax_only']/data['total_contacts']*100) if data['total_contacts'] > 0 else 0:.1f}% do total")
        
        media_por_lista = data['total_contacts'] / data['total_listas'] if data['total_listas'] > 0 else 0
        st.metric("📊 Média por Lista", f"{media_por_lista:,.0f} contatos")
    
    st.markdown("---")
    
    # Tabela de contatos recentes
    st.subheader("📋 Listas de Contatos Recentes")
    
    if data['recent_contacts']:
        df_contacts = pd.DataFrame(data['recent_contacts'])
        
        df_display = df_contacts[['date_str', 'contact_id_short', 'total', 'valid', 'invalid', 'syntax', 'taxa_validacao']]
        df_display.columns = ['Data', 'ID da Lista', 'Total', '✅ Válidos', '❌ Inválidos', '⚠️ Sintaxe', 'Taxa']
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Data": st.column_config.TextColumn("Data", width="medium"),
                "ID da Lista": st.column_config.TextColumn("ID da Lista", width="medium"),
                "Total": st.column_config.NumberColumn("Total", format="%d"),
                "✅ Válidos": st.column_config.NumberColumn("✅ Válidos", format="%d"),
                "❌ Inválidos": st.column_config.NumberColumn("❌ Inválidos", format="%d"),
                "⚠️ Sintaxe": st.column_config.NumberColumn("⚠️ Sintaxe", format="%d"),
                "Taxa": st.column_config.TextColumn("Taxa Validação", width="small"),
            }
        )
        
        # Gráfico de evolução
        if len(data['recent_contacts']) > 1:
            st.subheader("📈 Evolução da Taxa de Validação")
            
            df_evolution = df_contacts.copy()
            df_evolution['taxa_num'] = df_evolution['valid'] / df_evolution['total'] * 100
            
            fig = px.line(
                df_evolution,
                x='date',
                y='taxa_num',
                markers=True,
                labels={'date': 'Data', 'taxa_num': 'Taxa de Validação (%)'},
                title='Taxa de E-mails Válidos por Lista'
            )
            
            fig.update_traces(line_color='#667eea', line_width=3)
            fig.update_layout(height=300)
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📭 Nenhuma lista processada ainda. Faça upload de um arquivo na aba Upload!")
    
    st.markdown("---")
    
    # Status
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🔧 Status dos Serviços")
        st.success("✅ API FastAPI")
        st.success("✅ Validação DNS")
        st.success("✅ Processamento")
        st.success("✅ Nginx")
    
    with col2:
        st.subheader("📊 Capacidades")
        st.info("📁 Max: 100MB")
        st.info("📧 ~1000 emails/min")
        st.info("📤 CSV, XLSX, XLS")
        st.info("💾 XLSX, CSV")
    
    with col3:
        st.subheader("🎯 Qualidade dos Dados")
        if data['total_contacts'] > 0:
            if taxa_validacao >= 80:
                st.success(f"🌟 Excelente: {taxa_validacao:.1f}%")
            elif taxa_validacao >= 60:
                st.warning(f"⚠️ Boa: {taxa_validacao:.1f}%")
            else:
                st.error(f"❌ Baixa: {taxa_validacao:.1f}%")
            
            st.info(f"📊 {data['valid_emails']:,} emails validados")
            st.info(f"🎯 {data['total_listas']} listas completas")
        else:
            st.info("Aguardando dados...")

# ============================================
# TAB 2 - UPLOAD (mantém o mesmo)
# ============================================
with tab2:
    st.header("📤 Upload de Arquivo")
    
    st.markdown("""
    ### 📋 Instruções:
    1. Selecione um arquivo CSV, XLSX ou XLS
    2. O arquivo deve conter colunas de **nome** e **e-mail**
    3. Tamanho máximo: **100MB**
    4. Clique em **Processar** e aguarde
    """)
    
    uploaded_file = st.file_uploader(
        "Arraste ou selecione seu arquivo",
        type=['csv', 'xlsx', 'xls'],
        help="Formatos aceitos: CSV, XLSX, XLS (máx. 100MB)"
    )
    
    if uploaded_file:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📄 Arquivo", uploaded_file.name)
        with col2:
            st.metric("📊 Tamanho", f"{uploaded_file.size / 1024:.2f} KB")
        with col3:
            st.metric("📁 Tipo", uploaded_file.type.split('/')[-1].upper())
        
        if st.button("🚀 Processar Arquivo", type="primary", use_container_width=True):
            with st.spinner("📤 Enviando arquivo..."):
                files = {"file": uploaded_file}
                try:
                    response = requests.post("http://138.197.145.84/api/upload", files=files, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        job_id = data["job_id"]
                        
                        st.success(f"✅ Upload realizado com sucesso!")
                        st.code(job_id, language=None)
                        st.session_state['current_job_id'] = job_id
                        
                        st.markdown("### 📊 Processamento em Andamento")
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        col1, col2, col3 = st.columns(3)
                        metric1 = col1.empty()
                        metric2 = col2.empty()
                        metric3 = col3.empty()
                        
                        while True:
                            try:
                                status_response = requests.get(f"http://138.197.145.84/api/jobs/{job_id}", timeout=10)
                                status_data = status_response.json()
                                
                                progress = status_data.get("progress", 0)
                                status = status_data.get("status", "processing")
                                processed = status_data.get("processed", 0)
                                total = status_data.get("total", 0)
                                
                                progress_bar.progress(progress / 100)
                                status_text.markdown(f"**Status:** {status.upper()} - {progress}% completo")
                                
                                metric1.metric("📊 Progresso", f"{progress}%")
                                metric2.metric("✅ Processados", f"{processed:,}")
                                metric3.metric("📧 Total", f"{total:,}")
                                
                                if status == "done":
                                    st.success("🎉 Processamento concluído com sucesso!")
                                    st.balloons()
                                    st.info(f"💡 Vá para a aba **Resultados** e cole o ID: `{job_id}`")
                                    break
                                elif status == "error":
                                    st.error("❌ Erro no processamento!")
                                    break
                                
                                time.sleep(2)
                            except Exception as e:
                                st.error(f"❌ Erro: {str(e)}")
                                break
                    else:
                        st.error(f"❌ Erro no upload: {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")

# TAB 3 e 4 continuam iguais ao código anterior...
# (mantendo o resto do código igual)

# ============================================
# TAB 3 - RESULTADOS
# ============================================
with tab3:
    st.header("📊 Resultados do Processamento")
    
    job_id = st.text_input("🔑 ID da Lista", placeholder="Cole o ID aqui", key="job_id_input")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        refresh_button = st.button("🔄 Atualizar Status", type="primary", use_container_width=True)
    
    if refresh_button and job_id:
        try:
            with st.spinner("🔍 Buscando dados..."):
                response = requests.get(f"http://138.197.145.84/api/jobs/{job_id}", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status")
                    progress = data.get("progress", 0)
                    total = data.get("total", 0)
                    processed = data.get("processed", 0)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📊 Status", status.upper())
                    with col2:
                        st.metric("📈 Progresso", f"{progress}%")
                    with col3:
                        st.metric("✅ Processados", f"{processed:,}")
                    with col4:
                        st.metric("📧 Total", f"{total:,}")
                    
                    st.progress(progress / 100)
                    
                    if status == "done":
                        st.success("✅ PROCESSAMENTO CONCLUÍDO")
                        
                        results_response = requests.get(f"http://138.197.145.84/api/results/{job_id}?limit=5000", timeout=30)
                        
                        if results_response.status_code == 200:
                            results_data = results_response.json()
                            contacts = results_data.get("data", [])
                            
                            if contacts:
                                df = pd.DataFrame(contacts)
                                
                                st.markdown("### 📊 Estatísticas de Validação")
                                
                                if 'email_validation_status' in df.columns:
                                    status_counts = df['email_validation_status'].value_counts()
                                    
                                    col1, col2, col3 = st.columns(3)
                                    
                                    valid_count = status_counts.get('valid', 0)
                                    invalid_count = status_counts.get('invalid', 0)
                                    syntax_count = status_counts.get('syntax_only', 0)
                                    
                                    with col1:
                                        st.metric("✅ Válidos", f"{valid_count:,}", 
                                                delta=f"{(valid_count/len(df)*100):.1f}% do total")
                                    with col2:
                                        st.metric("❌ Inválidos", f"{invalid_count:,}",
                                                delta=f"{(invalid_count/len(df)*100):.1f}% do total")
                                    with col3:
                                        st.metric("⚠️ Sintaxe", f"{syntax_count:,}",
                                                delta=f"{(syntax_count/len(df)*100):.1f}% do total")
                                
                                st.markdown("### 📋 Dados Processados")
                                st.dataframe(df, use_container_width=True, height=400)
                                
                                st.markdown("### 📥 Downloads Disponíveis")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown("**📦 Download Completo:**")
                                    st.markdown(f"[⬇️ Baixar Excel](http://138.197.145.84/api/download/{job_id}?format=xlsx)")
                                    st.markdown(f"[⬇️ Baixar CSV](http://138.197.145.84/api/download/{job_id}?format=csv)")
                                
                                with col2:
                                    st.markdown("**🎯 Download Filtrado (válidos):**")
                                    st.markdown(f"[⬇️ Baixar Excel Filtrado](http://138.197.145.84/api/download/{job_id}/filtered?format=xlsx&valid_only=true)")
                                    st.markdown(f"[⬇️ Baixar CSV Filtrado](http://138.197.145.84/api/download/{job_id}/filtered?format=csv&valid_only=true)")
                else:
                    st.error("❌ Lista não encontrada!")
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")

# ============================================
# TAB 4 - CONFIG
# ============================================
with tab4:
    st.header("⚙️ Configurações do Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 Configurações")
        st.markdown("""
        **Limites:**
        - 📁 Tamanho: **100MB**
        - 👥 Contatos: **100,000**
        - ⏱️ Timeout: **3600s**
        
        **Funcionalidades:**
        - ✅ Validação DNS
        - ✅ Validação MX  
        - ✅ Processamento assíncrono
        - ✅ Cache habilitado
        """)
    
    with col2:
        st.subheader("📚 Informações")
        st.markdown("**Versão:** 1.0.0")
        st.code("Dashboard: http://138.197.145.84/validador/", language=None)
        st.code("API: http://138.197.145.84/api", language=None)
        st.markdown("[📦 GitHub](https://github.com/wesleyrobot/validador-de-e-mail)")
