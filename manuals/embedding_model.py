from sentence_transformers import SentenceTransformer
from langchain_core.embeddings import Embeddings
import logging

logger = logging.getLogger(__name__)


class SentenceTransformerEmbeddingsModel(Embeddings):
    """
    オープンモデルを使用したいためEmbeddingを継承した専用クラスを実装
    
    Attributes:
        model: SentenceTransformerモデルのインスタンス
    """
    def __init__(self, model_name: str, device: str = "cpu") -> None:
        """
        埋め込みモデルを初期化する
        
        Args:
            model_name: 使用するSentenceTransformerモデル名
            device: 使用するデバイス（"cpu" または "cuda"）
            
        Raises:
            ValueError: model_nameが空の場合
            Exception: モデルのロードに失敗した場合
        """
        if not model_name:
            raise ValueError("model_nameを空にすることはできません")
        
        try:
            self.model = SentenceTransformer(model_name, device=device)
            logger.info(f"埋め込みモデルを正常にロードしました: {model_name} (デバイス: {device})")
        except Exception as e:
            logger.error(f"埋め込みモデル '{model_name}' のロードに失敗しました: {e}")
            raise RuntimeError("埋め込みモデルのロードに失敗しました")

    def embed_query(self, text: str) -> list[float]:
        """
        単一のクエリテキストを埋め込みベクトルに変換する
        
        Args:
            text: 埋め込むテキスト
            
        Returns:
            list[float]: 埋め込みベクトル
            
        Raises:
            ValueError: textが空の場合
            Exception: 埋め込み処理に失敗した場合
        """
        if not text:
            raise ValueError("textを空にすることはできません")
        
        try:
            embedding = self.model.encode(text).tolist()
            return embedding
        except Exception as e:
            logger.error(f"クエリテキストの埋め込みに失敗しました: {e}")
            raise RuntimeError("テキストの埋め込み処理に失敗しました")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        複数のドキュメントテキストを埋め込みベクトルに変換する
        
        Args:
            texts: 埋め込むテキストのリスト
            
        Returns:
            list[list[float]]: 埋め込みベクトルのリスト
            
        Raises:
            ValueError: textsが空の場合
            Exception: 埋め込み処理に失敗した場合
        """
        if not texts:
            logger.warning("embed_documentsに空のテキストリストが提供されました")
            return []
        
        try:
            embeddings = [self.model.encode(t).tolist() for t in texts if t]
            
            # 空文字列がある場合の警告
            empty_count = len(texts) - len(embeddings)
            if empty_count > 0:
                logger.warning(f"embed_documentsで {empty_count} 件の空テキストをスキップしました")
            
            return embeddings
        except Exception as e:
            logger.error(f"ドキュメントの埋め込みに失敗しました: {e}")
            raise RuntimeError("ドキュメントの埋め込み処理に失敗しました")
