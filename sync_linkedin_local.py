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
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
LINKEDIN_PROFILE_ID = 'magno-freitas'

def format_with_ai(raw_text):
    if not GROQ_API_KEY:
        print("⚠️ Chave GROQ_API_KEY não encontrada! Pulando formatação com IA...")
        return raw_text
        
    print("🤖 Enviando dados crus para a Groq (Llama 3) processar e formatar na velocidade da luz...")
    
    prompt = f"""
    Você é um recrutador tech internacional e um engenheiro de software especialista em design de README do GitHub.
    
    Eu vou te passar os dados brutos de um scrape do meu LinkedIn. Ele está cheio de lixo (como "Gostar", "Comentar", "Enviar", "Exibido apenas a você").
    
    SUA TAREFA EXCLUSIVA:
    1. Limpar todo esse lixo visual de site.
    2. Pegar APENAS as informações ÚTEIS (Experiência, Sobre mim, Projetos, Skills, Educação).
    3. Traduzir tudo de forma impecável para o INGLÊS profissional.
    4. Criar um documento Markdown organizado em seções elegantes, usando emojis.
    
    Siga as regras:
    - Não coloque título `<h1>` principal ou `# Welcome`, comece direto na seção `### 👨‍💻 About Me`
    - Não coloque bloco ```markdown em volta do resultado.
    - Devolva a resposta final 100% pronta para eu colar no meu readme.
    - Mantenha simples, moderno e direto.
    
    DADOS DO LINKEDIN:
    {raw_text}
    """

    try:
        # Usa o Llama 3 70B através da incrível infraestrutura LPU da Groq (Grátis e ultra rápida)
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {GROQ_API_KEY}"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that only outputs pure markdown."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            print(f"Erro da API da Groq: {response.text}")
            return "<!-- IA FAILING -->\n\nErro ao conectar com a IA Groq para formatar o currículo."
            
        response_data = response.json()
        formatted_text = response_data['choices'][0]['message']['content']
        
        # Limpando caso o modelo retorne dentro de uma tag de codeblock de markdown
        if formatted_text.startswith("```markdown"):
            formatted_text = formatted_text.replace("```markdown", "", 1)
        if formatted_text.startswith("```"):
            formatted_text = formatted_text.replace("```", "", 1)
        if formatted_text.endswith("```"):
            formatted_text = formatted_text[::-1].replace("```", "", 1)[::-1]
            
        print("✨ O Groq devolveu o perfil formatado com sucesso!")
        return formatted_text.strip()
    except Exception as e:
        print(f"❌ Erro ao falar com a API da Groq via HTTP: {e}")
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
