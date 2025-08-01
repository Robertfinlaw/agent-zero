import aiohttp
from python.helpers import runtime
import os

# Use alternative search services for Railway deployment
SEARXNG_URL = os.environ.get("SEARXNG_URL", "http://localhost:55510/search")

async def search(query:str):
    # For Railway deployment, directly call the search function instead of RFC
    if os.environ.get("RAILWAY_ENVIRONMENT_NAME") or os.environ.get("PORT"):
        return await _search(query)
    else:
        return await runtime.call_development_function(_search, query=query)

async def _search(query:str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(SEARXNG_URL, data={"q": query, "format": "json"}) as response:
                return await response.json()
    except Exception as e:
        # Fallback: try DuckDuckGo search for Railway deployment
        try:
            from python.helpers import duckduckgo_search
            import asyncio
            ddg_results = await asyncio.to_thread(duckduckgo_search.search, query, 5)
            
            # Convert DuckDuckGo format to SearXNG format
            searxng_results = []
            for result_str in ddg_results:
                # Parse the string representation from DuckDuckGo
                try:
                    # DuckDuckGo returns string representation of dict, need to parse it
                    import ast
                    result_dict = ast.literal_eval(result_str)
                    searxng_results.append({
                        "title": result_dict.get("title", ""),
                        "url": result_dict.get("href", ""),
                        "content": result_dict.get("body", "")
                    })
                except:
                    # If parsing fails, create a basic entry
                    searxng_results.append({
                        "title": f"DuckDuckGo result for: {query}",
                        "url": "https://duckduckgo.com/?q=" + query.replace(" ", "+"),
                        "content": str(result_str)[:200] + "..."
                    })
            
            return {"results": searxng_results}
        except Exception as ddg_error:
            # Final fallback to basic mock response
            return {
                "results": [{
                    "title": f"Search results for: {query}",
                    "url": "https://www.google.com/search?q=" + query.replace(" ", "+"),
                    "content": f"Search services unavailable. Search query: {query}. Original error: {str(e)}. Consider using alternative search tools."
                }]
            }
