import os
import logging
import inspect
from abc import abstractmethod
from typing import Optional

from django.conf import settings
from sqlalchemy import create_engine, text

from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_core.documents import Document

from .embedding_model import SentenceTransformerEmbeddingsModel
from langchain_community.document_loaders.s3_file import S3FileLoader


USE_OPEN_AI = False

logger = logging.getLogger(__name__)


def _is_enabled() -> bool:
    return os.getenv("VECTOR_INGEST_ENABLED", "true").lower() in {"1", "true", "yes", "on"}


def _get_pg_connection_string() -> str:
    conn = os.getenv("VECTOR_PG_CONNECTION", "").strip()
    if not conn:
        raise RuntimeError("VECTOR_PG_CONNECTION が未設定です")
    return conn


class VectorModel:
    """BaseLLMModel互換の最小実装（VectorStore登録用途）。"""

    def __init__(self, file_paths: list[str], collection_name: str = "manuals") -> None:
        self.collection_name = collection_name
        self.file_paths = file_paths

        # Embeddings
        use_open_ai = os.getenv("USE_OPEN_AI", "true" if USE_OPEN_AI else "false").lower() in {"1", "true", "yes", "on"}
        embedding_model_name = os.getenv("EMBEDDING_MODEL_NAME") or os.getenv("HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

        if use_open_ai:
            self.embeddings = OpenAIEmbeddings(
                model=embedding_model_name,
                api_key=os.getenv("OPENAI_API_KEY"),
            )
        else:
            self.embeddings = SentenceTransformerEmbeddingsModel(
                model_name=embedding_model_name,
                device=os.getenv("EMBEDDING_DEVICE", os.getenv("HF_EMBEDDINGS_DEVICE", "cpu")),
            )

        # Vector Store
        self.pg_connection_string = _get_pg_connection_string()
        self.vector_store = PGVector(
            embeddings=self.embeddings,
            collection_name=self.collection_name,
            connection=self.pg_connection_string,
            use_jsonb=True,
            pre_delete_collection=False,
        )

        # 初期化時にデフォルトのretrieverを設定（必要なら呼び出し側で使用）
        self.retriever = self._create_retriever(file_paths)

    def _create_retriever(self, file_paths: Optional[list[str]] = None):
        search_kwargs = {}
        if file_paths:
            # file_paths は "manuals/<s3_key>" のような source 文字列を渡す想定
            search_kwargs["filter"] = {"source": {"$in": file_paths}}
        return self.vector_store.as_retriever(search_kwargs=search_kwargs)

    def get_existing_sources(self) -> set[str]:
        """Vector DBに既に登録されているsourceのセットを取得する。"""
        engine = create_engine(self.pg_connection_string)
        with engine.connect() as conn:
            collection_row = conn.execute(
                text("SELECT uuid FROM langchain_pg_collection WHERE name = :collection_name"),
                {"collection_name": self.collection_name},
            ).fetchone()

            if not collection_row:
                return set()

            collection_id = collection_row[0]
            rows = conn.execute(
                text(
                    "SELECT DISTINCT cmetadata->>'source' as source "
                    "FROM langchain_pg_embedding "
                    "WHERE collection_id = :collection_id"
                ),
                {"collection_id": collection_id},
            )
            return {r[0] for r in rows if r and r[0]}

    def delete_by_source(self, source: str) -> None:
        """指定sourceの既存ベクトルを削除（更新時の再登録用）。"""
        engine = create_engine(self.pg_connection_string)
        with engine.begin() as conn:
            collection_row = conn.execute(
                text("SELECT uuid FROM langchain_pg_collection WHERE name = :collection_name"),
                {"collection_name": self.collection_name},
            ).fetchone()
            if not collection_row:
                return

            collection_id = collection_row[0]
            conn.execute(
                text(
                    "DELETE FROM langchain_pg_embedding "
                    "WHERE collection_id = :collection_id AND cmetadata->>'source' = :source"
                ),
                {"collection_id": collection_id, "source": source},
            )

    def ingest_documents(self, bucket_name: str, file_paths: list[str]) -> None:
        if not bucket_name:
            raise ValueError("bucket_nameを空にすることはできません")
        if not file_paths:
            raise ValueError("file_pathsを空にすることはできません")

        documents = self._load_documents(bucket_name, file_paths)
        if documents:
            self.vector_store.add_documents(documents)

    def _load_documents(self, bucket_name: str, file_paths: list[str]) -> list:
        documents: list[Document] = []

        for file_path in file_paths:
            if not file_path:
                continue

            source = f"{bucket_name}/{file_path}"

            endpoint_url = getattr(settings, "AWS_S3_ENDPOINT_URL", None) or os.getenv("AWS_S3_ENDPOINT_URL")
            region_name = getattr(settings, "AWS_S3_REGION_NAME", None) or os.getenv("AWS_S3_REGION_NAME")

            loader_kwargs = {
                "bucket": bucket_name,
                "key": file_path,
            }
            if endpoint_url:
                loader_kwargs["endpoint_url"] = endpoint_url
            if region_name:
                loader_kwargs["region_name"] = region_name

            # unstructured側へ言語ヒントを渡す（未指定だと英語デフォルトの警告が出る）
            raw_languages = os.getenv("UNSTRUCTURED_LANGUAGES", "jpn").strip()
            languages = [lang.strip() for lang in raw_languages.split(",") if lang.strip()]
            try:
                sig = inspect.signature(S3FileLoader)
                if "unstructured_kwargs" in sig.parameters:
                    loader_kwargs["unstructured_kwargs"] = {"languages": languages}
                elif "loader_kwargs" in sig.parameters:
                    # 実装差異に備えて、汎用のkwargsにも入れてみる
                    loader_kwargs["loader_kwargs"] = {"languages": languages}
            except Exception:
                # シグネチャ取得に失敗した場合は何もしない
                pass

            loader = S3FileLoader(**loader_kwargs)
            loaded_docs = loader.load()

            combined = "\n\n".join(
                [d.page_content for d in loaded_docs if getattr(d, "page_content", "").strip()]
            ).strip()
            if not combined:
                continue

            # 1ファイル=1レコード（splitしない）
            documents.append(Document(page_content=combined, metadata={"source": source}))

        return documents


def ingest_manual_to_vector_store(
    *,
    manual_id: int,
    company_id: int,
    application_id: int,
    s3_key: str,
    title: Optional[str] = None,
) -> None:
    """添付のBaseLLMModelと同じ方式で、S3(PDF) -> PGVector(PostgreSQL)へ登録する。"""

    if not _is_enabled():
        return

    bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None) or os.getenv("AWS_STORAGE_BUCKET_NAME") or "manuals"
    collection_name = os.getenv("VECTOR_COLLECTION_NAME", "manuals")

    wrapper = VectorModel([], collection_name=collection_name)

    source_key = f"{bucket_name}/{s3_key}"
    existing_sources = wrapper.get_existing_sources()

    # 既存がある場合は削除して再登録（更新時も確実に反映させる）
    delete_existing = os.getenv("VECTOR_DELETE_EXISTING_SOURCE", "true").lower() in {"1", "true", "yes", "on"}
    if source_key in existing_sources:
        if delete_existing:
            wrapper.delete_by_source(source_key)
        else:
            return

    # S3FileLoader は key (バケット内パス) を受け取るため、bucket/keyで渡さない
    wrapper.ingest_documents(bucket_name, [s3_key])


def delete_manual_from_vector_store(*, s3_key: str) -> None:
    """S3上の対象PDFに対応するベクトルをPGVectorから削除する。"""

    if not _is_enabled():
        return

    if not s3_key:
        return

    bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None) or os.getenv("AWS_STORAGE_BUCKET_NAME") or "manuals"
    collection_name = os.getenv("VECTOR_COLLECTION_NAME", "manuals")

    wrapper = VectorModel([], collection_name=collection_name)
    source_key = f"{bucket_name}/{s3_key}"
    wrapper.delete_by_source(source_key)
