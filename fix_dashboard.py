with open('streamlit_app.py', 'r') as f:
    content = f.read()

# Substituir a função load_all_contacts_data
old_section = '''                contacts = data.get('data', [])'''

new_section = '''                # JSON é uma lista direta
                if isinstance(data, list):
                    contacts = data
                else:
                    contacts = data.get('data', data.get('contacts', []))'''

content = content.replace(old_section, new_section)

with open('streamlit_app.py', 'w') as f:
    f.write(content)

print("✅ Função corrigida para ler lista direta")
