import os
import re
from linkedin_api import Linkedin

# Pegando as credenciais dos Secrets do GitHub
LINKEDIN_LI_AT = os.getenv('LINKEDIN_LI_AT')
LINKEDIN_JSESSIONID = os.getenv('LINKEDIN_JSESSIONID')
LINKEDIN_PROFILE_ID = 'magno-freitas'  # Seu ID no linkedin.com/in/...

def main():
    if not LINKEDIN_LI_AT or not LINKEDIN_JSESSIONID:
        print("Erro: Cookies do LinkedIn (li_at e JSESSIONID) não encontrados nas variáveis de ambiente.")
        import sys
        sys.exit(1)

    print(f"Tentando autenticar no LinkedIn usando Cookies de Sessão...")
    try:
        # Usa o repositório não-oficial. Como contornar o bug dos cookies:
        api = Linkedin("", "") 
        # Injeta os cookies manualmente na sessão do requests que a lib usa por baixo
        api.client.session.cookies.set('li_at', LINKEDIN_LI_AT)
        api.client.session.cookies.set('JSESSIONID', LINKEDIN_JSESSIONID)
        
        print(f"Buscando perfil de: {LINKEDIN_PROFILE_ID}")
        profile = api.get_profile(LINKEDIN_PROFILE_ID)
        
        # Puxa a seção "Sobre" (Summary) do seu LinkedIn
        summary = profile.get('summary', '')
        
        if not summary:
            print("Nenhum 'Sobre/Summary' encontrado no LinkedIn.")
            return

        # Lendo o README atual
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read()

        # Expressão regular para encontrar a área entre os marcadores
        marker_start = r'<!-- LINKEDIN_ABOUT_START -->'
        marker_end = r'<!-- LINKEDIN_ABOUT_END -->'
        
        # Formata o resumo do LinkedIn para o README (com quebras de linha Markdown)
        formatted_summary = f"\n{summary}\n"
        
        pattern = re.compile(f'({marker_start}).*?({marker_end})', re.DOTALL)
        updated_readme = pattern.sub(rf'\1{formatted_summary}\2', readme_content)
        
        # Escrevendo a atualização no README
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(updated_readme)
            
        print("README.md atualizado com sucesso com os dados do LinkedIn!")

    except Exception as e:
        print(f"Erro durante a execução: {e}")
        import sys
        sys.exit(1)  # Isso faz o GitHub Action reportar falha

if __name__ == '__main__':
    main()
