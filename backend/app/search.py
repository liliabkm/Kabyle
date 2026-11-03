import unicodedata

def fold(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',value).casefold() if not unicodedata.combining(c))

def searchable(data):
    parts=[data.get(k,'') for k in ('latin','french','tifinagh')]
    for key in ('synonyms','alternative_versions','french_variants','source_skill_names'):
        value=data.get(key,[])
        parts.extend(value if isinstance(value,list) else [value])
    return fold(' '.join(v for v in parts if isinstance(v,str)))

def pair_key(kind,data):
    if kind!='phrase':return None
    import hashlib
    latin=unicodedata.normalize('NFC',data.get('latin','')).strip()
    french=unicodedata.normalize('NFC',data.get('french','')).strip()
    return hashlib.sha256((latin+'\0'+french).encode()).hexdigest()
