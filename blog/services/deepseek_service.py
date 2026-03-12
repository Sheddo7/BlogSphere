# blog/services/deepseek_service.py
import requests
import json
from django.conf import settings


class DeepSeekService:
    """Service for interacting with DeepSeek AI API"""

    BASE_URL = "https://api.deepseek.com/v1/chat/completions"

    def __init__(self):
        self.api_key = getattr(settings, 'DEEPSEEK_API_KEY', '')
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in settings")

    def generate_content(self, prompt, temperature=0.7, max_tokens=4096):
        """
        Send a prompt to DeepSeek and get response

        Args:
            prompt (str): The prompt to send
            temperature (float): Controls randomness (0-1)
            max_tokens (int): Maximum response length

        Returns:
            dict: Response with content and metadata
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(
                self.BASE_URL,
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                return {
                    'success': True,
                    'content': content,
                    'word_count': len(content.split())
                }
            else:
                return {
                    'success': False,
                    'error': f"API error: {response.status_code}",
                    'details': response.text
                }

        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'Request timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def paraphrase_article(self, title, content, category, min_words=500):
        """
        Specialized method for paraphrasing news articles
        """
        prompt = f"""You are a professional journalist. Rewrite this news article in a clear, factual style.

REQUIREMENTS:
- Write at least {min_words} words
- Preserve all facts, names, dates, and quotes exactly
- Use completely original wording
- Maintain a neutral, professional tone
- Category: {category}

TITLE: {title}
CONTENT:
{content[:8000]}

Write your version now:"""

        result = self.generate_content(prompt, temperature=0.4, max_tokens=4096)

        if result['success']:
            # Clean up any duplicate sentences
            cleaned = self._remove_duplicates(result['content'])
            result['content'] = cleaned
            result['word_count'] = len(cleaned.split())

        return result

    def _remove_duplicates(self, text):
        """Remove duplicate sentences"""
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        seen = set()
        unique = []
        for s in sentences:
            norm = s.strip().lower()
            if norm and norm not in seen:
                seen.add(norm)
                unique.append(s)
        return ' '.join(unique)