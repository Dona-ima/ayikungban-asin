import requests
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

class QdrantAPIClient:
    """
    Client Python pour interagir avec l'API Qdrant FastAPI
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Vérifier l'état de l'API"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def upload_files(
        self,
        file_paths: List[str],
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload des fichiers vers l'API
        
        Args:
            file_paths: Liste des chemins des fichiers
            chunk_size: Taille des chunks
            chunk_overlap: Chevauchement entre chunks
            metadata: Métadonnées supplémentaires
        """
        files = []
        try:
            # Préparer les fichiers
            for file_path in file_paths:
                path = Path(file_path)
                if not path.exists():
                    raise FileNotFoundError(f"Fichier non trouvé: {file_path}")
                
                files.append(
                    ('files', (path.name, open(path, 'rb'), 'application/octet-stream'))
                )
            
            # Données du formulaire
            data = {
                'chunk_size': chunk_size,
                'chunk_overlap': chunk_overlap
            }
            
            if metadata:
                data['metadata'] = json.dumps(metadata)
            
            # Envoyer la requête
            response = self.session.post(
                f"{self.base_url}/upload",
                files=files,
                data=data
            )
            response.raise_for_status()
            return response.json()
            
        finally:
            # Fermer les fichiers
            for _, file_tuple in files:
                if hasattr(file_tuple[1], 'close'):
                    file_tuple[1].close()
    
    def search(
        self,
        query: str,
        k: int = 5,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Recherche dans la base vectorielle
        
        Args:
            query: Texte de recherche
            k: Nombre de résultats
            filter_conditions: Conditions de filtrage
        """
        data = {
            "query": query,
            "k": k
        }
        
        if filter_conditions:
            data["filter_conditions"] = filter_conditions
        
        response = self.session.post(
            f"{self.base_url}/search",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def delete_documents(self, document_ids: List[str]) -> Dict[str, Any]:
        """Supprimer des documents"""
        data = {"ids": document_ids}
        response = self.session.delete(
            f"{self.base_url}/documents",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Informations sur la collection"""
        response = self.session.get(f"{self.base_url}/collection/info")
        response.raise_for_status()
        return response.json()
    
    def backup_collection(self, backup_name: str) -> Dict[str, Any]:
        """Créer une sauvegarde"""
        response = self.session.post(
            f"{self.base_url}/collection/backup",
            params={"backup_name": backup_name}
        )
        response.raise_for_status()
        return response.json()
    
    def find_similar_documents(
        self,
        document_id: str,
        k: int = 5,
        include_original: bool = False
    ) -> Dict[str, Any]:
        """Trouver des documents similaires"""
        params = {
            "k": k,
            "include_original": include_original
        }
        response = self.session.get(
            f"{self.base_url}/search/similar/{document_id}",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_documents_by_filter(
        self,
        filename: Optional[str] = None,
        category: Optional[str] = None,
        file_extension: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Récupérer des documents par filtre"""
        params = {"limit": limit}
        
        if filename:
            params["filename"] = filename
        if category:
            params["category"] = category
        if file_extension:
            params["file_extension"] = file_extension
        
        response = self.session.get(
            f"{self.base_url}/documents/by-filter",
            params=params
        )
        response.raise_for_status()
        return response.json()

# Exemple d'utilisation
def example_usage():
    """Exemple d'utilisation du client API"""
    
    print("🚀 Test de l'API Qdrant FastAPI")
    
    # Initialiser le client
    client = QdrantAPIClient("http://localhost:8000")
    
    try:
        # 1. Vérifier l'état de l'API
        print("\n1. Vérification de l'état de l'API...")
        health = client.health_check()
        print(f"✅ API Status: {health['status']}")
        print(f"   Database: {health['database_path']}")
        
        # 2. Créer des fichiers de test
        print("\n2. Création de fichiers de test...")
        
        # Fichier texte
        with open("test_document.txt", "w", encoding="utf-8") as f:
            f.write("""
            Ceci est un document de test pour l'API FastAPI.
            Il contient des informations sur l'intelligence artificielle,
            le machine learning et les bases de données vectorielles.
            Qdrant est un excellent choix pour la recherche sémantique.
            """)
        
        # Fichier JSON
        with open("test_config.json", "w", encoding="utf-8") as f:
            json.dump({
                "application": "Vector Search API",
                "version": "1.0.0",
                "database": "Qdrant Embedded",
                "features": ["search", "upload", "delete", "backup"]
            }, f, indent=2)
        
        # 3. Upload des fichiers
        print("\n3. Upload des fichiers...")
        file_paths = ["test_document.txt", "test_config.json"]
        metadata = [
            {"category": "documentation", "author": "Test User"},
            {"category": "configuration", "environment": "development"}
        ]
        
        upload_result = client.upload_files(
            file_paths=file_paths,
            chunk_size=500,
            chunk_overlap=50,
            metadata=metadata
        )
        print(f"✅ Upload réussi: {upload_result['total_chunks']} chunks créés")
        print(f"   IDs: {upload_result['document_ids'][:3]}...")
        
        # 4. Test de recherche
        print("\n4. Test de recherche...")
        search_results = client.search(
            query="intelligence artificielle machine learning",
            k=3
        )
        
        print(f"🔍 Requête: '{search_results['query']}'")
        print(f"   Résultats: {search_results['total_results']}")
        print(f"   Temps: {search_results['processing_time']:.3f}s")
        
        for i, result in enumerate(search_results['results'], 1):
            print(f"\n   {i}. Score: {result['score']:.3f}")
            print(f"      Fichier: {result['metadata'].get('filename', 'N/A')}")
            print(f"      Extrait: {result['text'][:100]}...")
        
        # 5. Recherche avec filtre
        print("\n5. Recherche avec filtre...")
        filtered_results = client.search(
            query="configuration",
            k=3,
            filter_conditions={"file_extension": ".json"}
        )
        
        print(f"   Résultats filtrés (JSON): {filtered_results['total_results']}")
        for result in filtered_results['results']:
            print(f"   - {result['metadata'].get('filename')} (Score: {result['score']:.3f})")
        
        # 6. Informations sur la collection
        print("\n6. Informations sur la collection...")
        info = client.get_collection_info()
        print(f"   Nom: {info['name']}")
        print(f"   Vecteurs: {info['vectors_count']}")
        print(f"   Points: {info['points_count']}")
        print(f"   Taille vecteur: {info['vector_size']}")
        
        # 7. Test de filtrage par métadonnées
        print("\n7. Test de filtrage par métadonnées...")
        filtered_docs = client.get_documents_by_filter(
            category="documentation",
            limit=5
        )
        print(f"   Documents avec category='documentation': {filtered_docs['total_results']}")
        
        # 8. Sauvegarde
        print("\n8. Création d'une sauvegarde...")
        backup_result = client.backup_collection("test_backup")
        print(f"✅ Sauvegarde: {backup_result['backup_path']}")
        
        print("\n🎉 Tous les tests réussis!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter à l'API. Vérifiez qu'elle est démarrée.")
        print("   Commande: uvicorn main:app --reload")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        
    finally:
        # Nettoyer les fichiers de test
        for file_path in ["test_document.txt", "test_config.json"]:
            if Path(file_path).exists():
                Path(file_path).unlink()

if __name__ == "__main__":
    example_usage()
