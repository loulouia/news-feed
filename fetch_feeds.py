#!/usr/bin/env python3
"""
Feed Fetcher - Busca notícias de RSS feeds e gera dados para o site
"""

import json
import feedparser
import html
import re
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

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
            # Extrai imagem se disponível
            image = None
            if hasattr(entry, 'media_content') and entry.media_content:
                image = entry.media_content[0].get('url')
            elif hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                image = entry.media_thumbnail[0].get('url')
            elif hasattr(entry, 'enclosures') and entry.enclosures:
                for enc in entry.enclosures:
                    if 'image' in enc.get('type', ''):
                        image = enc.get('href')
                        break
            
            article = {
                "id": get_entry_id(entry, feed_name),
                "title": clean_html(entry.get('title', 'Sem título')),
                "link": entry.get('link', ''),
                "summary": clean_html(entry.get('summary', entry.get('description', ''))),
                "date": parse_date(entry),
                "source": feed_name,
                "category_id": category_id,
                "category_name": category_name,
                "image": image
            }
            articles.append(article)
        
        print(f"  ✓ {feed_name}: {len(articles)} artigos")
        return articles
        
    except Exception as e:
        print(f"  ✗ {feed_name}: Erro - {str(e)[:50]}")
        return []


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
    
    return output


if __name__ == "__main__":
    fetch_all_feeds()
