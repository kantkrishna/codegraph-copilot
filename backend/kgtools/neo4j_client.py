# backend/kgtools/neo4j_client.py

# This file contains the Neo4j client implementation, fulfilling both KG and RAG client interfaces.

from typing import Dict, Any, List, Optional
from neo4j import GraphDatabase
from backend.config import settings

class Neo4jKGClient:
    """
    Concrete implementation of KGClient and RAGClient that queries the Neo4j database
    populated by CodeGraph AI's ingestion pipeline.
    """
    def __init__(self) -> None:
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri, 
            auth=(settings.neo4j_user, settings.neo4j_password)
        )

    def close(self) -> None:
        """Closes the Neo4j driver connection."""
        self.driver.close()

    def search_entity(self, name: str) -> Optional[Dict[str, Any]]:
        clean_name = name.lower().replace(" service", "").replace(" component", "").replace(" stub", "").strip()
        
        query = """
        MATCH (e)
        WHERE toLower(coalesce(e.name, '')) CONTAINS $name
        WITH e, labels(e) AS lbls, toLower(coalesce(e.name, '')) AS lower_name
        WITH e, lbls, lower_name,
             CASE WHEN lower_name = $name THEN 1000 ELSE 0 END AS exact_score,
             CASE 
                WHEN 'Service' IN lbls OR 'App' IN lbls THEN 500
                WHEN 'File' IN lbls OR 'Document' IN lbls OR 'markdown' IN lbls THEN -10000
                ELSE 0 
             END AS type_score
        ORDER BY (exact_score + type_score) DESC, size(lower_name) ASC
        RETURN e AS entity, lbls AS labels
        LIMIT 1
        """
        with self.driver.session() as session:
            result = session.run(query, name=clean_name)
            record = result.single()
            if record and record["entity"]:
                node = record["entity"]
                return {
                    "id": str(node.element_id),
                    "type": record["labels"][0] if record["labels"] else "Entity",
                    "name": node.get("name", name)
                }
        return None

    def fetch_relationships(
        self, 
        entity_id: str, 
        direction: str, 
        relationship_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        with self.driver.session() as session:
            if direction in ("outbound", "both"):
                out_query = """
                MATCH (e)-[r]->(target)
                WHERE elementId(e) = $entity_id OR coalesce(e.name, '') = $entity_id
                RETURN target, type(r) as edge_type
                """
                for rec in session.run(out_query, entity_id=entity_id):
                    target = rec["target"]
                    results.append({
                        "target_id": str(target.element_id),
                        "target_name": target.get("name", "Unknown"),
                        "edge_type": rec["edge_type"]
                    })
                    
            if direction in ("inbound", "both"):
                in_query = """
                MATCH (source)-[r]->(e)
                WHERE elementId(e) = $entity_id OR coalesce(e.name, '') = $entity_id
                RETURN source, type(r) as edge_type
                """
                for rec in session.run(in_query, entity_id=entity_id):
                    source = rec["source"]
                    results.append({
                        "source_id": str(source.element_id),
                        "source_name": source.get("name", "Unknown"),
                        "edge_type": rec["edge_type"]
                    })
                    
        return results

    def search_documents(
        self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Acts as the RAG client by executing a schema-agnostic search over the 
        real Knowledge Graph nodes. Uses keyword tokenization to prevent exact-match failures.
        """
        # 1. Strip punctuation and common stop words to create a resilient keyword list
        stop_words = {
            "how", "does", "the", "what", "is", "a", "an", "for", "to", "in", "on", "and", 
            "works", "calculated", "before", "saving", "explain", "logic", "where", "implemented"
        }
        clean_query = query.replace("?", "").replace(",", "").replace(".", "")
        keywords = [w.lower() for w in clean_query.split() if w.lower() not in stop_words]
        
        # Fallback if all words were stripped
        if not keywords:
            keywords = [query.lower()]

        # 2. Match nodes where ANY of their properties contain ANY of our keywords
        # REMOVED 'OR n:Method' to eliminate the Neo4j schema warning
        search_query = """
        MATCH (n)
        WHERE (n:File OR n:Document OR n:Class OR n:Function OR n:Service)
          AND any(kw IN $keywords WHERE any(k IN keys(n) WHERE n[k] IS NOT NULL AND toLower(toString(n[k])) CONTAINS kw))
        RETURN coalesce(n.name, 'Unknown') AS title, 
               n AS node_data, 
               elementId(n) AS filepath
        LIMIT $top_k
        """
        results: List[Dict[str, Any]] = []
        with self.driver.session() as session:
            for record in session.run(search_query, keywords=keywords, top_k=top_k):
                node_props = dict(record["node_data"])
                
                # Filter out heavy vectors and complex objects
                clean_props = {
                    k: str(v) for k, v in node_props.items() 
                    if not k.endswith('embedding') and isinstance(v, (str, int, float))
                }
                
                snippet = " | ".join(f"{k}: {v[:500]}" for k, v in clean_props.items())
                
                results.append({
                    "title": record["title"],
                    "snippet": snippet[:1500],
                    "filepath": record["filepath"]
                })
        return results