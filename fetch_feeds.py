#!/usr/bin/env python3
"""
Feed Fetcher - Busca notícias de RSS feeds e gera dados para o site
Versão 2.0 - Com busca automática de imagens
"""

import json
import feedparser
import html
import re
import urllib.request
import urllib.errora
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import time

# Configurações
FEEDS_CONFIG = "feeds.json"
OUTPUT_FILE = "data.json"
MAX_WORKERS = 10
REQUEST_TIMEOUT = 15


def clean_html(text):
    """Remove tags HTML e limpa o texto"""
    if not text:
        return ""
    # Remove tags HTML
    clean = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    clean = html.unescape(clean)
    # Remove espaços extras
    clean = ' '.join(clean.split())
    # Limita tamanho
    if len(clean) > 300:
        clean = clean[:297] + "..."
    return clean


def parse_date(entry):
    """Extrai e parseia a data de um entry do feed"""
    date_fields = ['published_parsed', 'updated_parsed', 'created_parsed']
    
    for field in date_fields:
        if hasattr(entry, field) and getattr(entry, field):
            try:
                parsed = getattr(entry, field)
                dt = datetime(*parsed[:6], tzinfo=timezone.utc)
                return dt.isoformat()
            except:
                pass
    
    # Fallback: data atual
    return datetime.now(timezone.utc).isoformat()


def get_entry_id(entry, feed_name):
    """Gera um ID único para o entry"""
    unique_string = f"{feed_name}-{entry.get('link', '')}-{entry.get('title', '')}"
    return hashlib.md5(unique_string.encode()).hexdigest()[:12]


def extract_image_from_entry(entry):
    """Tenta extrair imagem do entry do RSS de várias formas"""
    
    # 1. Media content
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            url = media.get('url', '')
            if url and ('image' in media.get('type', '') or 
                       any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif'])):
                return url
    
    # 2. Media thumbnail
    if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
        for thumb in entry.media_thumbnail:
            if thumb.get('url'):
                return thumb['url']
    
    # 3. Enclosures
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if 'image' in enc.get('type', ''):
                return enc.get('href') or enc.get('url')
    
    # 4. Image tag
    if hasattr(entry, 'image') and entry.image:
        if isinstance(entry.image, dict):
            return entry.image.get('href') or entry.image.get('url')
        elif isinstance(entry.image, str):
            return entry.image
    
    # 5. Content/Summary - busca primeira imagem
    content = entry.get('content', [{}])[0].get('value', '') if entry.get('content') else ''
    content = content or entry.get('summary', '') or entry.get('description', '')
    
    if content:
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content, re.IGNORECASE)
        if img_match:
            img_url = img_match.group(1)
            # Ignora imagens muito pequenas (trackers, pixels, etc)
            if not any(x in img_url.lower() for x in ['pixel', 'tracker', 'spacer', '1x1', 'blank']):
                return img_url
    
    return None


def fetch_image_from_url(url):
    """Busca imagem de capa usando microlink.io API"""
    if not url:
        return None
    
    try:
        api_url = f"https://api.microlink.io?url={urllib.parse.quote(url, safe='')}"
        
        req = urllib.request.Request(
            api_url,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; NewsFeed/2.0)'}
        )
        
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode())
            
            if data.get('status') == 'success' and data.get('data'):
                # Tenta pegar a imagem principal
                image_data = data['data'].get('image')
                if image_data and image_data.get('url'):
                    return image_data['url']
                
                # Fallback: logo do site
                logo_data = data['data'].get('logo')
                if logo_data and logo_data.get('url'):
                    return logo_data['url']
    
    except Exception as e:
        pass  # Silently fail - não queremos parar o processo por causa de uma imagem
    
    return None


# Importa urllib.parse para encode de URL
import urllib.parse


def fetch_single_feed(feed_config, category_id, category_name, max_items):
    """Busca um único feed RSS"""
    feed_name = feed_config["name"]
    feed_url = feed_config["url"]
    
    try:
        # Parse do feed
        parsed = feedparser.parse(feed_url)
        
        if parsed.bozo and not parsed.entries:
            print(f"  ⚠️  {feed_name}: Feed inválido ou inacessível")
            return []
        
        articles = []
        for entry in parsed.entries[:max_items]:
            # Primeiro tenta extrair imagem do RSS
            image = extract_image_from_entry(entry)
            
            article = {
                "id": get_entry_id(entry, feed_name),
                "title": clean_html(entry.get('title', 'Sem título')),
                "link": entry.get('link', ''),
                "summary": clean_html(entry.get('summary', entry.get('description', ''))),
                "date": parse_date(entry),
                "source": feed_name,
                "category_id": category_id,
                "category_name": category_name,
                "image": image,
                "needs_image": image is None  # Flag para buscar depois
            }
            articles.append(article)
        
        print(f"  ✓ {feed_name}: {len(articles)} artigos")
        return articles
        
    except Exception as e:
        print(f"  ✗ {feed_name}: Erro - {str(e)[:50]}")
        return []


def fetch_missing_images(articles, max_to_fetch=20):
    """Busca imagens para artigos que não têm usando microlink.io"""
    
    articles_needing_images = [a for a in articles if a.get('needs_image') and a.get('link')][:max_to_fetch]
    
    if not articles_needing_images:
        return
    
    print(f"\n🖼️  Buscando imagens para {len(articles_needing_images)} artigos...")
    
    def fetch_image_for_article(article):
        image = fetch_image_from_url(article['link'])
        if image:
            article['image'] = image
        article.pop('needs_image', None)
        return article
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_image_for_article, a): a for a in articles_needing_images}
        
        completed = 0
        for future in as_completed(futures):
            completed += 1
            article = futures[future]
            try:
                future.result()
            except Exception as e:
                pass
    
    # Remove flag dos que não foram processados
    for article in articles:
        article.pop('needs_image', None)
    
    images_found = sum(1 for a in articles_needing_images if a.get('image'))
    print(f"  ✓ Encontradas {images_found}/{len(articles_needing_images)} imagens")


def fetch_all_feeds():
    """Busca todos os feeds configurados"""
    # Carrega configuração
    config_path = Path(__file__).parent / FEEDS_CONFIG
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    settings = config.get("settings", {})
    max_items = settings.get("max_items_per_feed", 10)
    max_featured = settings.get("max_featured", 6)
    max_list = settings.get("max_list_items", 30)
    
    all_articles = []
    
    print("\n📡 Buscando feeds...\n")
    
    # Prepara lista de tarefas
    tasks = []
    for category in config["categories"]:
        for feed in category["feeds"]:
            tasks.append((feed, category["id"], category["name"], max_items))
    
    # Executa em paralelo
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(fetch_single_feed, *task): task 
            for task in tasks
        }
        
        for future in as_completed(futures):
            articles = future.result()
            all_articles.extend(articles)
    
    # Ordena por data (mais recentes primeiro)
    all_articles.sort(key=lambda x: x["date"], reverse=True)
    
    # Busca imagens faltantes para os artigos mais recentes (featured + primeiros da lista)
    # Limitamos a 20 para não exceder o limite gratuito do microlink (150/dia)
    fetch_missing_images(all_articles, max_to_fetch=20)
    
    # Separa featured e list
    featured = all_articles[:max_featured]
    remaining = all_articles[max_featured:max_featured + max_list]
    
    # Agrupa por categoria para estatísticas
    stats = {}
    for article in all_articles:
        cat_id = article["category_id"]
        if cat_id not in stats:
            stats[cat_id] = 0
        stats[cat_id] += 1
    
    # Monta output
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_articles": len(all_articles),
        "categories": [
            {
                "id": cat["id"],
                "name": cat["name"],
                "icon": cat["icon"],
                "color": cat["color"],
                "count": stats.get(cat["id"], 0)
            }
            for cat in config["categories"]
        ],
        "featured": featured,
        "articles": remaining,
        "all_articles": all_articles  # Para filtros no frontend
    }
    
    # Salva output
    output_path = Path(__file__).parent / OUTPUT_FILE
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Concluído! {len(all_articles)} artigos salvos em {OUTPUT_FILE}")
    print(f"   Featured: {len(featured)} | Lista: {len(remaining)}")
    
    # Conta artigos com imagem
    with_image = sum(1 for a in all_articles if a.get('image'))
    print(f"   Com imagem: {with_image}/{len(all_articles)}")
    
    return output


if __name__ == "__main__":
    fetch_all_feeds()
