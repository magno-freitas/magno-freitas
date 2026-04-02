from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os
import re
import time
import subprocess
from dotenv import load_dotenv

# Carrega variáveis de ambiente de um arquivo .env local
load_dotenv()

LINKEDIN_LI_AT = os.getenv('LINKEDIN_LI_AT')
LINKEDIN_PROFILE_ID = 'magno-freitas'

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
    chrome_options = Options()
    # Descomente a linha abaixo se quiser que a janela do Chrome não apareça
    # chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    # Inicia o Chrome
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
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
        print("Aguardando carregamento da seção 'Sobre'...")
        try:
            # Procura pelo container da seção "Sobre" (Summary)
            about_section = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='about']//ancestor::section//div[contains(@class, 'display-flex ph5 pv3')]"))
            )
            # A partir de 2024, o texto fica geralmente no componente de "ver mais" ou logo abaixo do About
            summary_element = about_section.find_element(By.XPATH, ".//span[@aria-hidden='true']")
            summary_text = summary_element.text
        except Exception:
            # Fallback para caso o layout seja diferente
            print("Layout principal falhou, tentando fallback (procurando qualquer span no contexto 'Sobre')...")
            # Enrola a página um pouco para ativar o carregamento das text areas
            driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(2)
            elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Sobre') or contains(text(), 'About')]/ancestor::section//span[@aria-hidden='true']")
            # O primeiro span dentro do componente "Sobre" costuma ser o texto em si, o índice 1 pega o texto visível
            if len(elements) > 1:
                summary_text = elements[1].text
            elif elements:
                summary_text = elements[0].text
            else:
                summary_text = ""
                
        if not summary_text:
            print("❌ Erro: Não foi possível extrair a seção 'Sobre' do seu perfil.")
            return

        print(f"Resumo capturado com sucesso! Trecho: {summary_text[:50]}...")

        # Atualizando o README
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read()

        marker_start = r'<!-- LINKEDIN_ABOUT_START -->'
        marker_end = r'<!-- LINKEDIN_ABOUT_END -->'
        
        formatted_summary = f"\n{summary_text}\n"
        
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
