"""Persistent writing examples from confirmed sent messages, never drafts.

Feature-hashed word embeddings avoid a hidden first-use model download. They are
local and deterministic; semantic embedding quality can be improved separately.
"""
import hashlib
import math
import re

from src.config import Config
from src.domain import Email


def embed(text, dimensions=256):
    vector = [0.0] * dimensions
    for word in re.findall(r'\w+', text.lower()):
        digest = hashlib.sha256(word.encode()).digest()
        index = int.from_bytes(digest[:4], 'big') % dimensions
        vector[index] += 1 if digest[4] % 2 else -1
    norm = math.sqrt(sum(value * value for value in vector)) or 1
    return [value / norm for value in vector]


class Memory:
    def __init__(self, config=None):
        self.config = config or Config()
        self._client = None
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            import chromadb
            from chromadb.config import Settings
            self._client = chromadb.PersistentClient(
                path=self.config.memory_path,
                settings=Settings(anonymized_telemetry=False))
            self._collection = self._client.get_or_create_collection(
                'sent_examples_v1', embedding_function=None,
                metadata={'hnsw:space': 'cosine'})
        return self._collection

    def remember_sent(self, email: Email):
        if not email.sent_by_user:
            raise ValueError('Only Gmail-confirmed SENT messages belong in style memory')
        if not email.id or not email.body.strip():
            return False
        # Persist bounded useful excerpts, retaining full-body digest for provenance.
        document = email.body[:self.config.style_chars]
        metadata = dict(source_message_id=email.id, thread_id=email.thread_id,
                        timestamp=email.timestamp, sent_by_user=True, subject=email.subject,
                        body_sha256=hashlib.sha256(email.body.encode()).hexdigest())
        self.collection.upsert(ids=['gmail:' + email.id], documents=[document],
                               embeddings=[embed(email.subject + '\n' + document)], metadatas=[metadata])
        return True

    def import_sent(self, gmail, limit=100, query=''):
        count = 0
        for message_id in gmail.messages(label='SENT', limit=limit, query=query):
            count += bool(self.remember_sent(gmail.confirm_sent(message_id)))
        return count

    def retrieve(self, query, exclude_thread='', exclude_ids=()):
        count = self.collection.count()
        if not count or not self.config.retrieval_limit:
            return []
        filters = []
        if exclude_thread:
            filters.append({'thread_id': {'$ne': exclude_thread}})
        if exclude_ids:
            filters.append({'source_message_id': {'$nin': list(exclude_ids)}})
        args = {'where': {'$and': filters} if len(filters) > 1 else filters[0]} if filters else {}
        found = self.collection.query(query_embeddings=[embed(query)],
                                      n_results=min(count, self.config.retrieval_limit),
                                      include=['documents', 'metadatas', 'distances'], **args)
        examples, remaining = [], self.config.style_chars
        for doc, meta in zip(found['documents'][0], found['metadatas'][0]):
            if remaining <= 0:
                break
            excerpt = doc[:remaining]
            examples.append({'body': excerpt, 'metadata': meta})
            remaining -= len(excerpt)
        return examples

    def inspect(self, limit=20, include_content=False):
        if not 1 <= limit <= 1000:
            raise ValueError('Inspect limit must be 1..1000')
        records = self.collection.get(limit=limit, include=['metadatas', 'documents'])
        result = []
        for i, message_id in enumerate(records['ids']):
            meta = records['metadatas'][i]
            item = {'id': message_id, 'source_message_id': meta['source_message_id'],
                    'thread_id': meta['thread_id'], 'timestamp': meta['timestamp'],
                    'sent_by_user': meta['sent_by_user']}
            if include_content:
                item.update(body=records['documents'][i], subject=meta['subject'])
            result.append(item)
        return result

    def delete(self, source_message_id):
        self.collection.delete(ids=['gmail:' + source_message_id])

    def reset(self, confirmed=False):
        if not confirmed:
            raise ValueError('Memory reset needs explicit confirmation')
        self._client = self._client or self.collection._client
        self._client.delete_collection('sent_examples_v1')
        self._collection = None
