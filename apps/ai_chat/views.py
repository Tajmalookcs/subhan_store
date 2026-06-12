import json
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt


def _build_system_prompt():
    """Build a system prompt with live product/category context from the DB."""
    from apps.products.models import Category, Product

    categories = list(
        Category.objects.filter(is_active=True, parent=None)
        .values_list('name', flat=True)
    )

    featured = list(
        Product.objects.filter(is_active=True, is_featured=True)
        .values('name', 'selling_price', 'sale_price', 'category__name')[:12]
    )

    featured_lines = []
    for p in featured:
        price = p['sale_price'] if p['sale_price'] else p['selling_price']
        featured_lines.append(f"  - {p['name']} ({p['category__name']}) — Rs. {price}")

    categories_str = ', '.join(categories) if categories else 'Grocery, Beverages, Dairy, Bakery, Personal Care, Household'
    featured_str = '\n'.join(featured_lines) if featured_lines else '  - (products loading)'

    return f"""You are Subhan Assistant, the helpful AI shopping assistant for Subhan Super Store.

About the store:
- Name: Subhan Super Store
- Location: Jaranwala, Punjab, Pakistan
- Established: Since 1996
- Tagline: No Compromise on Quality
- Contact: 041-431 2982 | 0371-431 2982 | 0301-431 2988
- Facebook: SubhanSuperStoreJaranwala

Product categories available:
{categories_str}

Some featured products right now:
{featured_str}

Your role:
- Help customers find products and check availability
- Recommend products based on their needs
- Answer questions about prices, categories, and deals
- Provide store info (location, timings, contact)
- Be friendly, helpful, and concise — like a knowledgeable store assistant

Response style:
- Keep replies short and to the point (2–4 sentences max unless listing products)
- Use bullet points for product lists
- Always mention prices in Pakistani Rupees (Rs.)
- If asked something you don't know, suggest contacting the store directly
- Do NOT make up products or prices not mentioned above

Language: Reply in the same language the customer writes in (Urdu or English)."""


@require_POST
def chat_message(request):
    api_key = settings.FALAK_API_KEY
    api_url = getattr(settings, 'FALAK_API_URL', 'https://api.falak.ai/v1')

    if not api_key:
        return JsonResponse({'reply': 'AI assistant is not configured yet. Please contact the store directly.'})

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    user_message = (data.get('message') or '').strip()
    history = data.get('history', [])

    if not user_message:
        return JsonResponse({'error': 'Empty message'}, status=400)

    messages = [{'role': 'system', 'content': _build_system_prompt()}]

    for entry in history[-6:]:  # last 6 turns for context
        role = entry.get('role')
        content = entry.get('content', '')
        if role in ('user', 'assistant') and content:
            messages.append({'role': role, 'content': content})

    messages.append({'role': 'user', 'content': user_message})

    try:
        response = requests.post(
            f'{api_url.rstrip("/")}/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'gemini-2.0-flash',
                'messages': messages,
                'max_tokens': 400,
                'temperature': 0.7,
            },
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()
        reply = result['choices'][0]['message']['content']
        return JsonResponse({'reply': reply})

    except requests.exceptions.Timeout:
        return JsonResponse({'reply': 'Sorry, the assistant is taking too long to respond. Please try again.'})
    except requests.exceptions.RequestException as e:
        return JsonResponse({'reply': 'Assistant is temporarily unavailable. Please contact the store directly.'})
    except (KeyError, IndexError):
        return JsonResponse({'reply': 'Unexpected response from AI service. Please try again.'})
