import httpx
import xml.etree.ElementTree as ET
import asyncio
from typing import List, Dict, Any
from app.core.config import settings

async def search_external_papers(query: str, limit: int = 5, project_id: str = None) -> List[Dict[str, Any]]:
    from app.agents.tools.logger import log_agent_step
    from app.core.database import async_session_maker
    from app.models.paper import QueryCache
    from sqlmodel import select
    """
    Search papers across Semantic Scholar and arXiv APIs.
    Merges findings, respects API rate limits (with retry and backoff),
    and caches successful search results in PostgreSQL.
    """
    # 0. Check PostgreSQL Cache
    cached_results = None
    try:
        async with async_session_maker() as session:
            stmt = select(QueryCache).where(QueryCache.query == query)
            result = await session.execute(stmt)
            cache_entry = result.scalars().first()
            if cache_entry:
                cached_results = cache_entry.results
                print(f"[SemanticScholar] Found cached results for query '{query}'")
                if project_id:
                    await log_agent_step(
                        project_id,
                        "RetrievalAgent",
                        "cache_hit",
                        "INFO",
                        f"Found cached Semantic Scholar / arXiv search results for query '{query}'"
                    )
                return cached_results[:limit]
    except Exception as e:
        print(f"Error checking cache: {e}")

    papers = []
    
    # 1. Search Semantic Scholar
    s2_api_key = settings.SEMANTIC_SCHOLAR_API_KEY
    headers = {}
    use_auth = False
    
    if s2_api_key:
        headers["x-api-key"] = s2_api_key
        use_auth = True
        
    s2_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,authors,venue,year,externalIds,url"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = None
            
            async def make_auth_request(client_inst):
                print(f"[SemanticScholar] Request: Query='{query}', Auth=YES")
                safe_headers = {k: ("***" if k.lower() == "x-api-key" else v) for k, v in headers.items()}
                print(f"[SemanticScholar] Headers: {safe_headers}")
                if project_id:
                    await log_agent_step(
                        project_id,
                        "RetrievalAgent",
                        "semantic_scholar_request",
                        "INFO",
                        f"Semantic Scholar Request: Query='{query}', Auth=YES, Headers={safe_headers}"
                    )
                return await client_inst.get(s2_url, params=params, headers=headers)

            async def make_unauth_request(client_inst):
                print(f"[SemanticScholar] Request: Query='{query}', Auth=NO")
                if project_id:
                    await log_agent_step(
                        project_id,
                        "RetrievalAgent",
                        "semantic_scholar_request",
                        "INFO",
                        f"Semantic Scholar Request: Query='{query}', Auth=NO"
                    )
                return await client_inst.get(s2_url, params=params)

            if use_auth:
                try:
                    response = await make_auth_request(client)
                    print(f"[SemanticScholar] Response Status Code (Authenticated): {response.status_code}")
                    
                    if response.status_code == 429:
                        print("[SemanticScholar] Rate limit (429) encountered. Sleeping 2 seconds before retry...")
                        if project_id:
                            await log_agent_step(
                                project_id,
                                "RetrievalAgent",
                                "semantic_scholar_rate_limit",
                                "WARNING",
                                "Semantic Scholar rate limit (429) encountered. Sleeping 2 seconds before retry..."
                            )
                        await asyncio.sleep(2.0)
                        
                        # Retry authenticated request once
                        response = await make_auth_request(client)
                        print(f"[SemanticScholar] Retry Response Status Code: {response.status_code}")
                        
                        if response.status_code == 429:
                            print("[SemanticScholar] Retry failed with 429. Sleeping 2 seconds before unauthenticated fallback...")
                            if project_id:
                                await log_agent_step(
                                    project_id,
                                    "RetrievalAgent",
                                    "semantic_scholar_rate_limit",
                                    "WARNING",
                                    "Semantic Scholar retry failed with 429. Sleeping 2 seconds before unauthenticated fallback..."
                                )
                            await asyncio.sleep(2.0)
                            use_auth = False
                        elif response.status_code != 200:
                            print(f"[SemanticScholar] Retry failed with status {response.status_code}. Sleeping 2 seconds before unauthenticated fallback...")
                            await asyncio.sleep(2.0)
                            use_auth = False
                    elif response.status_code != 200:
                        print(f"[SemanticScholar] Authenticated request failed with status {response.status_code}. Sleeping 2 seconds before unauthenticated fallback...")
                        await asyncio.sleep(2.0)
                        use_auth = False
                except Exception as auth_err:
                    print(f"[SemanticScholar] Error during authenticated request: {auth_err}. Sleeping 2 seconds before unauthenticated fallback...")
                    if project_id:
                        await log_agent_step(
                            project_id,
                            "RetrievalAgent",
                            "semantic_scholar_auth_error",
                            "WARNING",
                            f"Error during authenticated Semantic Scholar request: {str(auth_err)}. Sleeping 2 seconds before unauthenticated fallback."
                        )
                    await asyncio.sleep(2.0)
                    use_auth = False
            
            # If not authenticated, or if authenticated attempts failed and fell back
            if not use_auth or response is None or response.status_code != 200:
                response = await make_unauth_request(client)
                print(f"[SemanticScholar] Response Status Code (Unauthenticated): {response.status_code}")
                
                if response.status_code == 429:
                    print("[SemanticScholar] Rate limit (429) encountered on unauthenticated. Sleeping 2 seconds before retry...")
                    if project_id:
                        await log_agent_step(
                            project_id,
                            "RetrievalAgent",
                            "semantic_scholar_rate_limit",
                            "WARNING",
                            "Semantic Scholar rate limit (429) encountered on unauthenticated. Sleeping 2 seconds before retry..."
                        )
                    await asyncio.sleep(2.0)
                    
                    # Retry unauthenticated request once
                    response = await make_unauth_request(client)
                    print(f"[SemanticScholar] Unauthenticated Retry (1) Response Status Code: {response.status_code}")
                    
                    if response.status_code == 429:
                        print("[SemanticScholar] Unauthenticated retry failed with 429. Sleeping 4 seconds before second retry...")
                        if project_id:
                            await log_agent_step(
                                project_id,
                                "RetrievalAgent",
                                "semantic_scholar_rate_limit",
                                "WARNING",
                                "Semantic Scholar unauthenticated retry failed with 429. Sleeping 4 seconds before second retry..."
                            )
                        await asyncio.sleep(4.0)
                        
                        # Second retry unauthenticated request
                        response = await make_unauth_request(client)
                        print(f"[SemanticScholar] Unauthenticated Retry (2) Response Status Code: {response.status_code}")
            
            if response is not None and response.status_code == 200:
                data = response.json()
                total = data.get("total", 0)
                returned = len(data.get("data", []))
                print(f"[SemanticScholar] Response Totals: total matched = {total}, returned = {returned}")
                if project_id:
                    await log_agent_step(
                        project_id,
                        "RetrievalAgent",
                        "semantic_scholar_totals",
                        "INFO",
                        f"Semantic Scholar Totals: total matched = {total}, returned = {returned}"
                    )
                for item in data.get("data", []):
                    authors = [a.get("name") for a in item.get("authors", []) if a.get("name")]
                    doi = item.get("externalIds", {}).get("DOI")
                    
                    papers.append({
                        "title": item.get("title", "Untitled"),
                        "authors": authors,
                        "journal": item.get("venue") or "Semantic Scholar",
                        "year": item.get("year"),
                        "doi": doi,
                        "pdf_url": item.get("url")
                    })
    except Exception as e:
        print(f"Error querying Semantic Scholar: {e}")
        if project_id:
            await log_agent_step(
                project_id,
                "RetrievalAgent",
                "semantic_scholar_error",
                "ERROR",
                f"Error querying Semantic Scholar: {str(e)}"
            )

    # 2. Search arXiv if we have fewer results than the limit
    if len(papers) < limit:
        try:
            arxiv_limit = limit - len(papers)
            
            # Wait 3 seconds before request to respect arXiv rate limits (1 req per 3s)
            print("[arXiv] Waiting 3 seconds before query to respect rate limits...")
            if project_id:
                await log_agent_step(
                    project_id,
                    "RetrievalAgent",
                    "arxiv_wait",
                    "INFO",
                    "Waiting 3 seconds before arXiv query to respect rate limits..."
                )
            await asyncio.sleep(3.0)
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                arxiv_url = "https://export.arxiv.org/api/query"
                params = {
                    "search_query": f"all:{query}",
                    "max_results": arxiv_limit
                }
                print(f"[arXiv] Querying: '{query}', max_results={arxiv_limit}")
                response = await client.get(arxiv_url, params=params)

                print("[arXiv] HTTP Response Status Code:", response.status_code)
                if response.status_code == 200:
                    root = ET.fromstring(response.text)
                    ns = {"atom": "http://www.w3.org/2005/Atom"}
                    
                    for entry in root.findall("atom:entry", ns):
                        title = entry.find("atom:title", ns)
                        title_text = title.text.strip().replace("\n", " ") if title is not None else "Untitled"
                        
                        authors = []
                        for author in entry.findall("atom:author", ns):
                            name = author.find("atom:name", ns)
                            if name is not None and name.text:
                                authors.append(name.text.strip())
                                
                        id_url = entry.find("atom:id", ns)
                        pdf_url = id_url.text.strip().replace("abs", "pdf") if id_url is not None else None
                        
                        published = entry.find("atom:published", ns)
                        year = int(published.text[:4]) if published is not None and len(published.text) >= 4 else None
                        
                        papers.append({
                            "title": title_text,
                            "authors": authors,
                            "journal": "arXiv",
                            "year": year,
                            "doi": None,
                            "pdf_url": pdf_url
                        })
        except Exception as e:
            print(f"Error querying arXiv: {e}")
            
    # Cache results in database if papers were successfully retrieved
    if papers and not cached_results:
        try:
            async with async_session_maker() as session:
                stmt = select(QueryCache).where(QueryCache.query == query)
                result = await session.execute(stmt)
                existing_cache = result.scalars().first()
                if not existing_cache:
                    cache_entry = QueryCache(query=query, results=papers)
                    session.add(cache_entry)
                    await session.commit()
                    print(f"[SemanticScholar] Successfully cached {len(papers)} papers for query '{query}'")
        except Exception as cache_err:
            print(f"Error saving to cache: {cache_err}")

    return papers[:limit]
