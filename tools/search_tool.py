import os
import requests
from dotenv import load_dotenv

load_dotenv()

def search_youtube_courses(query: str, num_results: int = 3) -> list:
    api_key = os.getenv("SERPER_API_KEY")
    
    url = "https://google.serper.dev/search"
    
    payload = {
        "q": f"{query} course tutorial site:youtube.com",
        "num": num_results * 2
    }
    
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        results = []
        organic = data.get("organic", [])
        
        for item in organic[:num_results]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "description": item.get("snippet", ""),
                "source": "YouTube"
            })
        
        return results
    
    except Exception as e:
        print(f"Search error: {e}")
        return []


def search_courses(topic: str, career: str, num_results: int = 3) -> list:
    query = f"best {topic} course for {career} beginners 2025"
    
    youtube_results = search_youtube_courses(query, num_results)
    
    return youtube_results