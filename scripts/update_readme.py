import os
import re
import requests
from bs4 import BeautifulSoup

LINKEDIN_PROFILE_ID = 'magno-freitas'

def main():
    print(f"Buscando perfil público de: {LINKEDIN_PROFILE_ID}...")
    try:
        url = f"https://www.linkedin.com/in/{LINKEDIN_PROFILE_ID}/"
        
        # Simulando um navegador muito padrão vindo do Google
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/'
        }

        # Não passaremos cookies, faremos scraping da versão pública do perfil
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Erro ao acessar perfil público: HTTP {response.status_code}")
            import sys
            sys.exit(1)

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Procura pelo summary na versão HTML do perfil (o LinkedIn esconde as vezes dentro de tags "core-section-container")
        summary_section = soup.find('section', {'data-section': 'summary'})
        
        summary = ""
        if summary_section:
            summary_text_elem = summary_section.find('div', class_='core-section-container__content')
            if summary_text_elem:
                summary = summary_text_elem.get_text(strip=True, separator='\n')

        # Fallback: Se não achar, o LinkedIn injeta dados em tags <code style="display: none">
        if not summary:
            print("Tentando buscar em tags <code> embarcadas...")
            import json
            for code_tag in soup.find_all('code'):
                try:
                    data = json.loads(code_tag.text)
                    # Procurando a chave "summary" perdidamente nos jsons escondidos
                    if isinstance(data, dict):
                        if 'included' in data:
                            for item in data['included']:
                                if 'summary' in item and item['summary']:
                                    summary = item['summary']
                                    break
                        elif 'summary' in data:
                            summary = data['summary']
                except:
                    pass

        if not summary:
            print("Nenhum 'Sobre/Summary' encontrado no HTML público. O LinkedIn pode estar bloqueando visitantes não logados.")
            import sys
            sys.exit(1)

        print(f"Resumo encontrado: {summary[:50]}...")

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
            
        print("README.md atualizado com sucesso!")

    except Exception as e:
        print(f"Erro durante a execução: {e}")
        import sys
        sys.exit(1)

if __name__ == '__main__':
    main()
