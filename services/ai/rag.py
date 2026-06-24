import os
import logging
from typing import List, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger("ai.rag")

_model = None


def _ensure_dict(f):
    if isinstance(f, dict):
        return f
    return {
        "file_path": f.file_path,
        "parsed_data": getattr(f, "parsed_data", {}),
        "content": getattr(f, "content", ""),
        "file_name": getattr(f, "file_name", ""),
    }


def get_embedding_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        logger.info("Loading embedding model: %s", model_name)
        _model = SentenceTransformer(model_name)
    return _model


def embed_text(text: str) -> list[float]:
    model = get_embedding_model()
    return model.encode(text).tolist()


def chunk_parsed_data(project_id: str, files: list) -> list[dict]:
    chunks = []
    for f in files:
        d = _ensure_dict(f)
        file_path = d["file_path"]
        parsed = d.get("parsed_data") or {}

        if parsed.get("module_docstring") or parsed.get("imports"):
            lines = [f"File: {file_path}"]
            if parsed.get("module_docstring"):
                lines.append(f"Module: {parsed['module_docstring']}")
            imports = parsed.get("imports", [])
            if imports:
                imp_strs = []
                for i in imports:
                    if isinstance(i, dict):
                        imp_strs.append(i.get("display", str(i)))
                    else:
                        imp_strs.append(str(i))
                lines.append(f"Imports: {' '.join(imp_strs)}")
            chunks.append({
                "project_id": project_id,
                "file_path": file_path,
                "chunk_type": "module",
                "chunk_text": "\n".join(lines),
                "metadata": {"file_path": file_path, "type": "module"},
            })

        for item in parsed.get("ordered_items", []):
            typ = item["type"]
            data = item["data"]
            if typ == "import":
                continue
            if typ == "function":
                chunk_text = _function_to_text(data, file_path)
            elif typ == "class":
                chunk_text = _class_to_text(data, file_path)
            else:
                continue
            chunks.append({
                "project_id": project_id,
                "file_path": file_path,
                "chunk_type": typ,
                "chunk_text": chunk_text,
                "metadata": {
                    "file_path": file_path,
                    "type": typ,
                    "name": data.get("name", ""),
                    "line": data.get("line", 0),
                },
            })
    return chunks


def _function_to_text(data: dict, file_path: str) -> str:
    args = ", ".join(a["name"] for a in data.get("args", []))
    decorators = ", ".join(data.get("decorators", []))
    connections = ", ".join(data.get("connections", []))
    return (
        f"File: {file_path}\n"
        f"Function: {data['name']}({args})\n"
        f"Returns: {data.get('returns', 'None')}\n"
        f"Async: {data.get('is_async', False)}\n"
        f"Decorators: {decorators}\n"
        f"Lines: {data.get('line', '?')}-{data.get('end_line', '?')}\n"
        f"Calls: {connections}\n"
        f"Docstring: {data.get('docstring', '')}"
    )


def _class_to_text(data: dict, file_path: str) -> str:
    methods = []
    for m in data.get("methods", []):
        margs = ", ".join(a["name"] for a in m.get("args", []))
        methods.append(f"  {m['name']}({margs}) -> {m.get('returns', 'None')}")
    bases = ", ".join(data.get("bases", []))
    connections = ", ".join(data.get("connections", []))
    return (
        f"File: {file_path}\n"
        f"Class: {data['name']}({bases})\n"
        f"Lines: {data.get('line', '?')}-{data.get('end_line', '?')}\n"
        f"Methods:\n" + "\n".join(methods) + "\n"
        f"Uses: {connections}\n"
        f"Docstring: {data.get('docstring', '')}"
    )


def embed_and_store_chunks(project_id, files, db: Session):
    from models import CodeEmbedding

    chunks = chunk_parsed_data(project_id, files)
    if not chunks:
        return

    db.query(CodeEmbedding).filter(
        CodeEmbedding.project_id == project_id
    ).delete()
    db.flush()

    model = get_embedding_model()
    texts = [c["chunk_text"] for c in chunks]
    embeddings = model.encode(texts).tolist()

    for chunk, embedding in zip(chunks, embeddings):
        ce = CodeEmbedding(
            project_id=chunk["project_id"],
            file_path=chunk["file_path"],
            chunk_type=chunk["chunk_type"],
            chunk_text=chunk["chunk_text"],
            embedding=embedding,
            metadata=chunk["metadata"],
        )
        db.add(ce)
    db.commit()
    logger.info("Stored %d embeddings for project %s", len(chunks), project_id)


def _detect_pattern(results) -> tuple[bool, str]:
    if len(results) < 3:
        return False, ""
    types = {}
    for r in results:
        t = r.chunk_type
        if t not in types:
            types[t] = []
        types[t].append(r)
    for typ, items in types.items():
        if len(items) >= 3 and typ in ("function", "class"):
            names = [r.chunk_metadata.get("name", "?") if r.chunk_metadata else "?" for r in items]
            display = ", ".join(names[:5])
            if len(names) > 5:
                display += "..."
            return True, f"Pattern: {len(items)} similar {typ}s ({display}). Write concise differential docs focusing on what makes each unique."
    return False, ""


def retrieve_context(project_id, query: str, top_k: int = 5, db: Session = None) -> tuple[str, bool]:
    from models import CodeEmbedding

    query_emb = embed_text(query)

    results = (
        db.query(CodeEmbedding)
        .filter(CodeEmbedding.project_id == project_id)
        .order_by(CodeEmbedding.embedding.cosine_distance(query_emb))
        .limit(top_k)
        .all()
    )

    if not results:
        return "", False

    is_pattern, pattern_desc = _detect_pattern(results)

    context_parts = []
    for r in results:
        meta = r.chunk_metadata or {}
        name = meta.get("name", "unknown")
        prev_doc = meta.get("prev_doc", "")
        header = f"Related code in {r.file_path} ({r.chunk_type}: {name})"
        chunk = f"{header}\n{r.chunk_text}"
        if prev_doc:
            chunk += f"\nPreviously generated doc:\n{prev_doc}"
        context_parts.append(chunk)

    context_text = "\n\n".join(context_parts)
    if is_pattern and pattern_desc:
        context_text = pattern_desc + "\n\n" + context_text

    return context_text, is_pattern


def store_generated_doc(project_id, chunk_type: str, item_name: str, file_path: str, generated_text: str, db: Session):
    from models import CodeEmbedding
    embeddings = (
        db.query(CodeEmbedding)
        .filter(
            CodeEmbedding.project_id == project_id,
            CodeEmbedding.file_path == file_path,
            CodeEmbedding.chunk_type == chunk_type,
        )
        .all()
    )
    for emb in embeddings:
        meta = emb.chunk_metadata or {}
        if meta.get("name") == item_name:
            meta["prev_doc"] = generated_text[:500]
            emb.chunk_metadata = meta
            db.commit()
            return
