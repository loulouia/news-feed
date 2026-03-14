# 📡 Meu Feed — Notícias Personalizadas

Um feed de notícias personalizado que agrega conteúdo das suas fontes favoritas, com atualização diária automática via GitHub Actions.

![Preview](https://via.placeholder.com/800x400/1a1918/f0efed?text=Meu+Feed)

## ✨ Funcionalidades

- 📰 **Agregação de múltiplas fontes** — RSS/Atom de newsletters, blogs e portais
- 🎨 **Dark/Light mode** — Tema automático ou manual
- 📱 **100% Responsivo** — Funciona em qualquer dispositivo
- ⚡ **Rápido** — Site estático, sem servidor
- 🔄 **Atualização automática** — GitHub Actions roda diariamente
- 🏷️ **Filtros por categoria** — Tech, Marketing, Negócios, Lifestyle
- 💰 **Gratuito** — Hospedado no GitHub Pages

---

## 🚀 Deploy Rápido (5 minutos)

### Passo 1: Criar repositório no GitHub

1. Vá em [github.com/new](https://github.com/new)
2. Nome do repositório: `meu-feed` (ou o que preferir)
3. Marque **"Public"** (necessário para GitHub Pages gratuito)
4. Clique em **"Create repository"**

### Passo 2: Fazer upload dos arquivos

**Opção A: Pelo navegador (mais fácil)**

1. Na página do seu novo repositório, clique em **"uploading an existing file"**
2. Arraste todos os arquivos desta pasta para lá
3. Clique em **"Commit changes"**

**Opção B: Pelo terminal**

```bash
# Clone seu repositório vazio
git clone https://github.com/SEU-USUARIO/meu-feed.git
cd meu-feed

# Copie todos os arquivos para cá e então:
git add .
git commit -m "🚀 Primeiro commit"
git push origin main
```

### Passo 3: Ativar GitHub Pages

1. Vá em **Settings** (configurações) do repositório
2. No menu lateral, clique em **Pages**
3. Em "Source", selecione:
   - Branch: `main`
   - Folder: `/ (root)`
4. Clique em **Save**

🎉 Pronto! Seu site estará disponível em:  
`https://SEU-USUARIO.github.io/meu-feed/`

### Passo 4: Primeira atualização dos feeds

A GitHub Action vai rodar automaticamente e buscar as notícias. Para forçar a primeira execução:

1. Vá em **Actions** no seu repositório
2. Clique em **"Update Feeds"** na sidebar
3. Clique em **"Run workflow"** → **"Run workflow"**

Aguarde ~1 minuto e atualize a página do seu site!

---

## ⚙️ Personalização

### Adicionar/Remover fontes

Edite o arquivo `feeds.json`:

```json
{
  "categories": [
    {
      "id": "tech-ia",
      "name": "Tech & IA",
      "icon": "⚡",
      "color": "accent",
      "feeds": [
        {
          "name": "TechCrunch",
          "url": "https://techcrunch.com/feed/",
          "type": "rss"
        }
        // Adicione mais feeds aqui
      ]
    }
  ]
}
```

### Encontrar RSS feeds

- **Substack**: `https://NOME.substack.com/feed`
- **Beehiiv**: `https://NOME.beehiiv.com/feed`
- **WordPress**: geralmente `/feed/` no final da URL
- **Qualquer site**: use [RSS.app](https://rss.app) para criar um feed

### Mudar horário de atualização

Edite `.github/workflows/update-feeds.yml`:

```yaml
schedule:
  # Formato: minuto hora dia mês dia-da-semana
  - cron: '0 10 * * *'  # 10:00 UTC = 7:00 BRT
```

### Personalizar o design

- **Cores**: edite as variáveis CSS no início do `style.css`
- **Nome do site**: edite a linha `<a class="site-logo">` no `index.html`
- **Ícone**: mude o emoji no favicon (linha `<link rel="icon">`)

---

## 🔧 Rodar localmente (opcional)

Se quiser testar antes de fazer deploy:

```bash
# Instalar dependência
pip install feedparser

# Buscar feeds
python fetch_feeds.py

# Servir localmente (Python 3)
python -m http.server 8000

# Abra http://localhost:8000 no navegador
```

---

## 📁 Estrutura do projeto

```
meu-feed/
├── index.html          # Página principal
├── style.css           # Estilos customizados
├── base.css            # Reset CSS
├── feeds.json          # Configuração das fontes
├── data.json           # Dados gerados (não edite manualmente)
├── fetch_feeds.py      # Script que busca os feeds
├── requirements.txt    # Dependências Python
├── .github/
│   └── workflows/
│       └── update-feeds.yml  # Automação diária
└── README.md
```

---

## ❓ FAQ

**O site não está atualizando?**
- Vá em Actions e verifique se há erros
- Clique em "Run workflow" para forçar atualização

**Uma fonte não está funcionando?**
- Verifique se a URL do RSS está correta
- Teste a URL no navegador — deve mostrar XML
- Alguns sites bloqueiam acesso automatizado

**Posso usar domínio próprio?**
- Sim! Em Settings → Pages → Custom domain

**Quantas fontes posso adicionar?**
- Não há limite técnico, mas muitas fontes = atualização mais lenta

---

## 📄 Licença

MIT — Use como quiser!

---

Feito com ☕ e Claude
