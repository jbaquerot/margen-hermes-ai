"""Offline-only ONNX E5 encoder. Artifact acquisition is an explicit separate step."""
from pathlib import Path
import hashlib
import json


class LocalE5:
    def __init__(self, directory, *, threads=2):
        root = Path(directory)
        manifest = json.loads((root / 'manifest.json').read_text())
        if manifest['model'] != 'intfloat/multilingual-e5-small' or manifest['dimension'] != 384:
            raise RuntimeError("Modelo local no compatible")
        for name, digest in manifest['files'].items():
            path = (root / name).resolve()
            if not path.is_relative_to(root.resolve()):
                raise RuntimeError('Ruta de artefacto inválida')
            with path.open('rb') as stream:
                actual = hashlib.file_digest(stream, 'sha256').hexdigest()
            if actual != digest:
                raise RuntimeError("Artefacto de modelo inválido")
        required = {'model.onnx','tokenizer.json'}
        if not required <= set(manifest['files']):
            raise RuntimeError('Faltan hashes de artefactos obligatorios')
        import onnxruntime as ort
        from tokenizers import Tokenizer
        self.tokenizer = Tokenizer.from_file(str(root / 'tokenizer.json'))
        self.tokenizer.no_truncation()
        self.tokenizer.no_padding()
        ort.disable_telemetry_events()
        options = ort.SessionOptions()
        options.intra_op_num_threads = max(1, min(threads,2))
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(str(root / 'model.onnx'), options,
                                             providers=['CPUExecutionProvider'])
        self.revision = manifest['revision'] + ':' + manifest['files']['model.onnx']

    def chunks(self, text):
        ids = self.tokenizer.encode(text, add_special_tokens=False).ids
        if len(ids) <= 450:
            return [text]
        return [self.tokenizer.decode(ids[i:i+450]) for i in range(0, len(ids), 400)]

    def encode(self, texts, *, query=False):
        import numpy as np
        result = []
        for text in texts:
            encoded = self.tokenizer.encode(('query: ' if query else 'passage: ') + text)
            if len(encoded.ids) > 512:
                raise ValueError("Texto supera el contexto de E5; debe fragmentarse.")
            ids = np.asarray([encoded.ids], dtype=np.int64)
            mask = np.ones_like(ids)
            inputs = {'input_ids': ids, 'attention_mask': mask,
                      'token_type_ids': np.zeros_like(ids)}
            inputs = {x.name:inputs[x.name] for x in self.session.get_inputs()}
            output = self.session.run(None, inputs)[0]
            if output.ndim == 3:
                output = (output * mask[...,None]).sum(axis=1) / mask.sum(axis=1)[...,None]
            vector = output[0]
            if vector.shape != (384,) or not np.isfinite(vector).all():
                raise RuntimeError("Vector E5 inválido")
            norm = np.linalg.norm(vector)
            if not norm:
                raise RuntimeError("Vector E5 vacío")
            result.append((vector / norm).tolist())
        return result
