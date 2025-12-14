# sleep_tracking_app/management/commands/index_sleep_articles.py
import os
from django.core.management.base import BaseCommand
from sleep_tracking_app.rag.vector_db import SleepVectorDB
import fitz  # PyMuPDF

ARTICLES_FOLDER = os.getenv("SLEEP_ARTICLES_FOLDER", "sleep_articles")
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", 800))

class Command(BaseCommand):
    help = "Index PDF articles from sleep_articles folder into Qdrant"

    def handle(self, *args, **options):
        db = SleepVectorDB()
        if not os.path.exists(ARTICLES_FOLDER):
            self.stdout.write(self.style.ERROR(f"Папка {ARTICLES_FOLDER} не найдена"))
            return

        files = [f for f in os.listdir(ARTICLES_FOLDER) if f.lower().endswith(".pdf")]
        if not files:
            self.stdout.write(self.style.WARNING("PDF файлов не найдено"))
            return

        chunks = []
        for fname in files:
            path = os.path.join(ARTICLES_FOLDER, fname)
            doc = fitz.open(path)
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            words = text.split()
            cur = []
            cur_len = 0
            chunk_index = 0
            for w in words:
                cur.append(w)
                cur_len += len(w) + 1
                if cur_len >= CHUNK_SIZE:
                    chunk_text = " ".join(cur)
                    chunk_id = f"{fname}_{chunk_index}"
                    chunks.append({"id": chunk_id, "text": chunk_text, "meta": {"source": fname, "chunk_index": chunk_index}})
                    chunk_index += 1
                    cur = []
                    cur_len = 0
            if cur:
                chunk_text = " ".join(cur)
                chunk_id = f"{fname}_{chunk_index}"
                chunks.append({"id": chunk_id, "text": chunk_text, "meta": {"source": fname, "chunk_index": chunk_index}})

        self.stdout.write(self.style.NOTICE(f"Подготовлено {len(chunks)} фрагментов. Загружаю в Qdrant..."))
        db.upsert_chunks(chunks)
        stats = db.get_stats()
        self.stdout.write(self.style.SUCCESS(f"Готово. В коллекции {stats.get('collection_name')} {stats.get('points_count')} векторов"))
