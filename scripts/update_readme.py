import os
import re
import requests
from bs4 import BeautifulSoup
import urllib.parse

# Pegando os cookies dos Secrets do GitHub
LINKEDIN_LI_AT = os.getenv('LINKEDIN_LI_AT')
LINKEDIN_JSESSIONID = os.getenv('LINKEDIN_JSESSIONID')
LINKEDIN_PROFILE_ID = 'magno-freitas'

def main():
    if not LINKEDIN_LI_AT or not LINKEDIN_JSESSIONID:
        print("Erro: Cookies do LinkedIn não encontrados.")
        import sys
        sys.exit(1)

    print(f"Buscando perfil de: {LINKEDIN_PROFILE_ID} usando Web Scraping puro...")
    try:
        url = f"https://www.linkedin.com/in/{LINKEDIN_PROFILE_ID}/"
        
        # O JSESSIONID normalmente tem aspas ao redor do valor, precisamos garantir que o Header csrf-token tenha o valor exato (sem as aspas)
        csrf_token = LINKEDIN_JSESSIONID.replace('"', '')

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'csrf-token': csrf_token,
            'x-restli-protocol-version': '2.0.0'
        }

        cookies = {
            'li_at': LINKEDIN_LI_AT,
            'JSESSIONID': LINKEDIN_JSESSIONID
        }

        # Acessando a página para capturar os dados (LinkedIn muitas vezes embute os dados do perfil em tags <code id="..._bpr_...">)
        # Vamos usar a rota da API interna do LinkedIn (Voyager) que é o que a web usa
        encoded_id = urllib.parse.quote(LINKEDIN_PROFILE_ID)
        api_url = f"https://www.linkedin.com/voyager/api/identity/profiles/{encoded_id}/profileView"
        
        response = requests.get(api_url, headers=headers, cookies=cookies)
        
        if response.status_code != 200:
            print(f"Erro ao acessar API do LinkedIn: HTTP {response.status_code}")
            print(response.text[:200])
            import sys
            sys.exit(1)

        data = response.json()
        
        # Extraindo o summary (Sobre/About)
        summary = ""
        if 'profile' in data and 'summary' in data['profile']:
            summary = data['profile']['summary']
            
        if not summary:
            # Alternativa dependendo da estrutura de retorno da API
            try:
                elements = data.get('included', [])
                for el in elements:
                    if 'summary' in el and el['summary']:
                        summary = el['summary']
                        break
            except:
                pass

        if not summary:
            print("Nenhum 'Sobre/Summary' encontrado no JSON do LinkedIn.")
            return

        # Lendo o README atual
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read()

        marker_start = r'<!-- LINKEDIN_ABOUT_START -->'
        marker_end = r'<!-- LINKEDIN_ABOUT_END -->'
        
        formatted_summary = f"\n{summary}\n"
        
        pattern = re.compile(f'({marker_start}).*?({marker_end})', re.DOTALL)
        updated_readme = pattern.sub(rf'\1{formatted_summary}\2', readme_content)
        
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(updated_readme)
            
        print("README.md atualizado com sucesso com os dados do LinkedIn!")

    except Exception as e:
        print(f"Erro durante a execução: {e}")
        import sys
        sys.exit(1)

if __name__ == '__main__':
    main()
