from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import re
import time
import subprocess
import requests
from dotenv import load_dotenv

# Carrega variáveis de ambiente de um arquivo .env local
load_dotenv()

LINKEDIN_LI_AT = os.getenv('LINKEDIN_LI_AT')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
LINKEDIN_PROFILE_ID = 'magno-freitas'

def format_with_ai(raw_text):
    if not GEMINI_API_KEY:
        print("⚠️ Chave GEMINI_API_KEY não encontrada! Pulando formatação com IA...")
        return raw_text
        
    print("🤖 Enviando dados crus para o Google Gemini processar e formatar com perfeição visual...")
    
    prompt = f"""
    You are an elite, international Tech Recruiter and a Staff Software Engineer evaluating top-tier backend and data professionals. 
    
    I will provide you with raw, messy scraped data from my LinkedIn profile (which may contain UI noise like "Like", "Comment", "Share", "Followers").
    
    YOUR EXCLUSIVE MISSION:
    1. Filter out absolutely ALL website UI noise and meaningless metrics.
    2. Extract only my genuine professional value (Experience, About Me, Projects, Skills, Education).
    3. Translate everything flawlessly into highly professional, IMPACT-DRIVEN ENGLISH.
    4. Rewrite the content to reflect a **SENIOR-LEVEL PROFESSIONAL** tone. Instead of just listing tasks, frame them as scalable solutions, business impacts, and architectural decisions. Elevate the language (e.g., instead of "I make Python scripts", use "I engineer automated Python pipelines to optimize business workflows").
    5. Format the output as an elegant, clean GitHub README Markdown section.
    
    REQUIRED SECTIONS & STRUCTURE:
    ### 👨‍💻 Professional Summary
    (A powerful, senior-level 2-3 sentence elevator pitch about my focus on scalable Backend systems, IoT integrations, and Data Analytics).

    ### 💼 Professional Experience
    (Format each role cleanly. Focus on impact, metrics, and technology stack used. Use elegant bullet points).

    ### 🛠️ Core Stack & Architecture
    (Group my skills logically: Backend & API, Data & Cloud Analytics, IoT & Hardware).

    ### 🎓 Education & Certifications
    (Clean list of my academic background and relevant achievements).
    
    RULES:
    - DO NOT include an `<h1>` main title or `# Welcome`, start directly at `### 👨‍💻 Professional Summary`.
    - DO NOT wrap your response in ```markdown blocks. Just return the raw markdown text.
    - Keep the design minimalist, modern, and highly authoritative.
    
    LINKEDIN RAW DATA:
    {raw_text}
    """

    try:
        # Usando a v1beta e o gemini-1.5-pro que é o melhor modelo pra raciocínio longo
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={GEMINI_API_KEY}"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3}
        }
        
        response = None
        max_retries = 3
        
        for attempt in range(max_retries):
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                break
            elif response.status_code == 503 or response.status_code == 429:
                print(f"⏳ O Google Gemini está congestionado ou com limite de taxa (Erro {response.status_code}). Tentativa {attempt + 1} de {max_retries}... Aguardando 20s.")
                time.sleep(20)
            else:
                break
        
        if response.status_code != 200:
            print(f"Erro da API do Gemini ({response.status_code}): {response.text}")
            return "<!-- IA FAILING -->\n\nErro ao conectar com a IA do Google para formatar o currículo."
            
        response_data = response.json()
        formatted_text = response_data['candidates'][0]['content']['parts'][0]['text']
        
        # Limpando caso o modelo retorne dentro de uma tag de codeblock de markdown
        if formatted_text.startswith("```markdown"):
            formatted_text = formatted_text.replace("```markdown", "", 1)
        if formatted_text.startswith("```"):
            formatted_text = formatted_text.replace("```", "", 1)
        if formatted_text.endswith("```"):
            formatted_text = formatted_text[::-1].replace("```", "", 1)[::-1]
            
        print("✨ O Gemini devolveu o perfil formatado com sucesso!")
        return formatted_text.strip()
    except Exception as e:
        print(f"❌ Erro ao falar com a API do Gemini via HTTP: {e}")
        return "<!-- IA FAILING -->\n\nErro interno de conexão."

def run_git_commands():
    try:
        print("\nVerificando alterações no repositório...")
        status = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        if 'README.md' not in status.stdout:
            print("Nenhuma alteração detectada no README.md. O conteúdo já estava sincronizado.")
            return

        print("Alterações detectadas! Comitando e enviando (push) para o GitHub...")
        subprocess.run(['git', 'add', 'README.md'], check=True)
        subprocess.run(['git', 'commit', '-m', 'docs: sync README with LinkedIn profile (local auto)'], check=True)
        subprocess.run(['git', 'push'], check=True)
        print("✅ Sincronização e Push concluídos com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao rodar os comandos do git: {e}")

def main():
    if not LINKEDIN_LI_AT:
        print("❌ Erro: Cookie 'li_at' não encontrado no arquivo .env.")
        print("Crie um arquivo chamado .env na mesma pasta do script e adicione: LINKEDIN_LI_AT=seu_cookie_aqui")
        return

    print("Configurando o navegador invisível...")
    edge_options = Options()
    # Descomente a linha abaixo se quiser que a janela do Edge não apareça
    # edge_options.add_argument("--headless=new")
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--no-sandbox")

    # Informa ao Selenium para usar o executável que está salvo na mesma pasta do script
    driver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "msedgedriver.exe")
    if not os.path.exists(driver_path):
        print(f"❌ Erro: O arquivo '{driver_path}' não foi encontrado.")
        print("Por favor, baixe o msedgedriver para a versão 146 e coloque-o na mesma pasta do script.")
        return

    try:
        service = Service(executable_path=driver_path)
        driver = webdriver.Edge(service=service, options=edge_options)
    except Exception as e:
        print(f"❌ Erro ao iniciar o Edge com o driver manual: {e}")
        return
    
    try:
        print("Acessando a página principal do LinkedIn para injetar o cookie...")
        driver.get('https://www.linkedin.com')
        time.sleep(2)
        
        # Injeta o cookie de sessão para evitar o login manual
        driver.add_cookie({
            'name': 'li_at',
            'value': LINKEDIN_LI_AT,
            'domain': '.linkedin.com'
        })
        
        print(f"Acessando o perfil: {LINKEDIN_PROFILE_ID}...")
        driver.get(f'https://www.linkedin.com/in/{LINKEDIN_PROFILE_ID}/')
        
        # O LinkedIn carrega as páginas sob demanda, então esperamos o componente Sobre aparecer
        print("Aguardando carregamento da página completa...")
        time.sleep(5) # Espera um tempo fixo para o perfil carregar
        
        # O LinkedIn carrega dinamicamente. Vamos rolar a página até o fim para forçar o carregamento de todas as seções
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

        print("Extraindo todo o texto das seções principais do perfil...")
        
        extracted_sections = []
        
        # Estratégia coringa: O LinkedIn muda nomes de classes o tempo todo. 
        # Sabemos que o perfil fica dentro da main class 'scaffold-layout__main'
        try:
            main_layout = driver.find_element(By.TAG_NAME, "main")
            
            # Pega as seções filhas diretas que compõem o corpo do perfil
            sections = main_layout.find_elements(By.XPATH, "./section | .//section[contains(@class, 'artdeco-card') or contains(@class, 'pv-profile-card')]")
            
            # Se não encontrar assim, pega simplesmente tudo que for <section> dentro de main
            if len(sections) < 2:
                sections = main_layout.find_elements(By.XPATH, ".//section")
                
            for sec in sections:
                text = sec.text
                # Seções úteis tem mais de 20 caracteres de texto legível
                if text and len(text) > 20:
                    lines = [line.strip() for line in text.split('\n') if line.strip() and len(line.strip()) > 2]
                    
                    if any(ignored in text.lower() for ignored in ["pessoas que você talvez conheça", "pessoas também viram", "outros perfis", "pesquisar por", "sugestões"]):
                        continue
                        
                    clean_text = "\n".join(lines)
                    if clean_text not in extracted_sections:
                        extracted_sections.append(clean_text)
                        
        except Exception as e:
            print(f"Erro ao buscar 'main' ou 'sections': {e}")

        if not extracted_sections:
            print("❌ Erro: Não foi possível extrair o texto das seções do seu perfil. O layout pode estar ofuscado.")
            return

        # Junta todas as seções com duas quebras de linha entre elas
        full_profile_text = "\n\n---\n\n".join(extracted_sections)
        
        print(f"Dados capturados com sucesso! Tamanho: {len(full_profile_text)} caracteres.")

        # Passa pelo funil da IA antes de escrever
        final_markdown = format_with_ai(full_profile_text)

        # Atualizando o README
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read()

        marker_start = r'<!-- LINKEDIN_ABOUT_START -->'
        marker_end = r'<!-- LINKEDIN_ABOUT_END -->'
        
        # Formata os dados num bloco de código para o README não quebrar com espaços bizarros
        formatted_summary = f"\n{final_markdown}\n"
        
        pattern = re.compile(f'({marker_start}).*?({marker_end})', re.DOTALL)
        updated_readme = pattern.sub(rf'\1{formatted_summary}\2', readme_content)
        
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(updated_readme)
            
        print("✅ README.md local atualizado!")
        
        # Aciona os comandos do Git automaticamente
        run_git_commands()

    except Exception as e:
        print(f"❌ Erro na execução do scraper: {e}")
    
    finally:
        driver.quit()

if __name__ == '__main__':
    main()
