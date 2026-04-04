import requests
import re
import subprocess
import os

# Altere para o seu username gerado no DEV.to (ex: 'magnofreitas')
DEVTO_USERNAME = "magno-freitas" 

def fetch_latest_posts():
    print(f"Buscando artigos de @{DEVTO_USERNAME} no Dev.to...")
    url = f"https://dev.to/api/articles?username={DEVTO_USERNAME}&per_page=3"
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Erro ao acessar API do Dev.to: HTTP {response.status_code}")
            return None
            
        posts = response.json()
        if not posts:
            print("Nenhum artigo encontrado no Dev.to ainda.")
            return "*No articles published yet. Stay tuned!*"
            
        markdown_lines = []
        for post in posts:
            title = post.get('title', 'Untitled Post')
            link = post.get('url', '#')
            date = post.get('published_at', '')[:10]  # Pega só YYYY-MM-DD
            reactions = post.get('public_reactions_count', 0)
            
            # Formatação de cada artigo
            markdown_lines.append(f"- 📝 **[{title}]({link})** (_{date}_) - ❤️ {reactions} reactions")
            
        return "\n".join(markdown_lines)
    except Exception as e:
        print(f"Erro ao tentar puxar os posts do Dev.to: {e}")
        return None

def update_readme(posts_markdown):
    if not posts_markdown:
        return False
        
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read()

        marker_start = r'<!-- DEVTO_POSTS_START -->'
        marker_end = r'<!-- DEVTO_POSTS_END -->'
        
        formatted_posts = f"\n{posts_markdown}\n"
        
        pattern = re.compile(f'({marker_start}).*?({marker_end})', re.DOTALL)
        updated_readme = pattern.sub(rf'\1{formatted_posts}\2', readme_content)
        
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(updated_readme)
            
        print("✅ README.md local atualizado com os artigos do Dev.to!")
        return True
    except Exception as e:
        print(f"❌ Erro ao atualizar README: {e}")
        return False

def run_git_commands():
    try:
        print("\nVerificando alterações no repositório para os artigos...")
        status = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        if 'README.md' not in status.stdout:
            print("Nenhuma alteração detectada. Os artigos já estavam sincronizados.")
            return

        print("Artigos novos detectados! Comitando e enviando (push) para o GitHub...")
        subprocess.run(['git', 'add', 'README.md'], check=True)
        subprocess.run(['git', 'commit', '-m', 'docs: sync latest articles from Dev.to (local auto)'], check=True)
        subprocess.run(['git', 'push'], check=True)
        print("✅ Sincronização do Blog concluída com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao rodar os comandos do git: {e}")

def main():
    print("Iniciando sincronização de artigos (Blog -> GitHub)")
    posts_markdown = fetch_latest_posts()
    if posts_markdown:
        if update_readme(posts_markdown):
            run_git_commands()

if __name__ == "__main__":
    main()
