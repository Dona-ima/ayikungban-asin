#!pip install flask-cors
#!pip install langchain-community
#!pip install langchain-mistralai

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_mistralai import MistralAIEmbeddings, ChatMistralAI
from langchain_community.vectorstores import FAISS
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain

from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI

# Charger ton vecteur FAISS (chemin selon ton projet)
vectorstore = FAISS.load_local(
    "vectorstore_index",  # 📂 nom du dossier où tu as sauvegardé FAISS
    embeddings,
    allow_dangerous_deserialization=True
)

# Initialiser ton modèle LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Construire la chaîne QA
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever()
)


# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Permet les requêtes cross-origin

class ChatbotAPI:
    def __init__(self):
        self.session_histories = {}  # Dict pour stocker l'historique par session
        self.chain = None
        self.setup_chatbot()

    def setup_chatbot(self):
        """Initialise le chatbot avec les documents et modèles"""
        try:
            # Configuration de l'API Mistral
            mistral_api_key = os.getenv("MISTRAL_API_KEY")
            if not mistral_api_key:
                raise ValueError("MISTRAL_API_KEY non trouvée dans les variables d'environnement")

            # Initialisation des embeddings et du modèle
            self.embeddings = MistralAIEmbeddings(
                model="mistral-embed",
                mistral_api_key=mistral_api_key
            )

            self.llm = ChatMistralAI(
                model="mistral-small-2402",
                mistral_api_key=mistral_api_key
            )

            # Chargement du vectorstore
            self.load_vectorstore()

            # Configuration du prompt et de la chaîne
            self.setup_chain()

            logger.info("Chatbot initialisé avec succès")

        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation: {str(e)}")
            raise

    def load_documents(self, pdf_files):
        """Charge et traite les documents PDF"""
        all_pages = []

        for pdf_file in pdf_files:
            if os.path.exists(pdf_file):
                loader = PyPDFLoader(pdf_file)
                pages = loader.load_and_split()
                all_pages.extend(pages)
            else:
                logger.warning(f"Fichier non trouvé: {pdf_file}")

        # Découpage en chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )

        chunks = text_splitter.split_documents(all_pages)
        return chunks

    def create_vectorstore(self, pdf_files):
        """Crée le vectorstore à partir des PDFs"""
        chunks = self.load_documents(pdf_files)
        vectorstore = FAISS.from_documents(chunks, self.embeddings)
        vectorstore.save_local("vectorstore.db")
        return vectorstore

    def load_vectorstore(self):
        """Charge le vectorstore existant ou le crée"""
        try:
            self.vectorstore = FAISS.load_local(
                "vectorstore.db",
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info("Vectorstore chargé depuis le fichier")
        except Exception as e:
            logger.warning(f"Impossible de charger le vectorstore: {str(e)}")
            logger.info("Création d'un nouveau vectorstore...")

            # Liste des fichiers PDF (adaptez selon votre structure)
            pdf_files = [
                "documents/Catalogue Officiel des Prestations Foncières de l'ANDF.pdf",
                "documents/La Réforme Foncière au Bénin.pdf",
                "documents/code du fontier Benin.pdf",
                "documents/loi-2017-15.pdf"
            ]

            self.vectorstore = self.create_vectorstore(pdf_files)

    def setup_chain(self):
        """Configure la chaîne de traitement"""
        retriever = self.vectorstore.as_retriever()

        template = """
        Tu es un expert en droit foncier et immobilier au Bénin.

        RÈGLES :
        - Tu réponds exclusivement dans le cadre béninois
        - Tu ne demandes jamais à l'utilisateur de préciser le pays
        - Tu ne dis jamais "cela dépend du pays"
        - Tu assumes toujours que la question concerne le Bénin
        - Tu contextualises chaque réponse avec les lois, institutions et pratiques béninoises

        Historique de la session : {session_history}
        {context}

        En te basant sur l'ensemble des documents, réponds clairement à la question suivante :
        {input}

        Ta réponse doit être :
        - claire et concise
        - rédigée en français simple
        - structurée si nécessaire
        - contextualisée pour le Bénin
        - fondée sur les textes, mais accessible à un citoyen ou agent
        - si l'information n'est pas présente, propose de consulter l'ANDF ou le Portail National des e-Services (service-public.bj)
        """

        prompt = ChatPromptTemplate.from_template(template)
        doc_chain = create_stuff_documents_chain(self.llm, prompt)
        self.chain = create_retrieval_chain(retriever, doc_chain)

    def get_response(self, input_text, session_id="default"):
        """Génère une réponse pour une question donnée"""
        try:
            # Récupère ou crée l'historique de session
            if session_id not in self.session_histories:
                self.session_histories[session_id] = []

            session_history = self.session_histories[session_id]
            session_history.append(f"Utilisateur : {input_text}")

            # Génère la réponse
            response = self.chain.invoke({
                "input": input_text,
                "context": "",
                "session_history": "\n".join(session_history[-10:])  # Limite à 10 derniers échanges
            })

            # Met à jour l'historique
            session_history.append(f"RoseBleue : {response['answer']}")

            return {
                "success": True,
                "answer": response['answer'],
                "session_id": session_id
            }

        except Exception as e:
            logger.error(f"Erreur lors de la génération de réponse: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "answer": "Désolé, une erreur est survenue. Veuillez réessayer."
            }

# Instance globale du chatbot
chatbot = None

def initialize_chatbot():
    """Initialise le chatbot au démarrage"""
    global chatbot
    try:
        chatbot = ChatbotAPI()
        logger.info("API initialisée avec succès")
    except Exception as e:
        logger.error(f"Erreur d'initialisation: {str(e)}")
        raise

# Routes de l'API
@app.route('/health', methods=['GET'])
def health_check():
    """Point de santé de l'API"""
    return jsonify({
        "status": "healthy",
        "service": "Chatbot Foncier Béninois",
        "version": "1.0.0"
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Point d'entrée principal pour les conversations"""
    try:
        data = request.get_json()

        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "error": "Le champ 'message' est requis"
            }), 400

        message = data['message'].strip()
        session_id = data.get('session_id', 'default')

        if not message:
            return jsonify({
                "success": False,
                "error": "Le message ne peut pas être vide"
            }), 400

        # Génère la réponse
        response = chatbot.get_response(message, session_id)

        if response['success']:
            return jsonify(response)
        else:
            return jsonify(response), 500

    except Exception as e:
        logger.error(f"Erreur dans /chat: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Erreur interne du serveur",
            "answer": "Désolé, une erreur est survenue. Veuillez réessayer."
        }), 500

@app.route('/sessions/<session_id>/history', methods=['GET'])
def get_session_history(session_id):
    """Récupère l'historique d'une session"""
    try:
        history = chatbot.session_histories.get(session_id, [])
        return jsonify({
            "success": True,
            "session_id": session_id,
            "history": history
        })
    except Exception as e:
        logger.error(f"Erreur dans /sessions/{session_id}/history: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Erreur lors de la récupération de l'historique"
        }), 500

@app.route('/sessions/<session_id>', methods=['DELETE'])
def clear_session(session_id):
    """Efface l'historique d'une session"""
    try:
        if session_id in chatbot.session_histories:
            del chatbot.session_histories[session_id]

        return jsonify({
            "success": True,
            "message": f"Session {session_id} effacée"
        })
    except Exception as e:
        logger.error(f"Erreur dans DELETE /sessions/{session_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Erreur lors de l'effacement de la session"
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint non trouvé"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Erreur interne du serveur"
    }), 500

if __name__ == '__main__':
    # Initialisation au démarrage
    initialize_chatbot()

    # Démarrage du serveur
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )


def get_response(user_message: str) -> str:
    try:
        response = qa_chain.run(user_message)
        return response
    except Exception as e:
        return f"Erreur dans le chatbot : {str(e)}"

