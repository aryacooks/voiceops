import re
import yaml
from .config import DATASET_DIR
from .data import table
TYPE = {'policy':'pol', 'agent_guide':'agent', 'marketing':'mkt'}
SECTION = re.compile(r'^#{1,6} \[([^\]]+)\]([^\n]*)', re.M)

def load_chunks():
    chunks=[]
    for path in sorted((DATASET_DIR / 'kb').glob('*.md')):
        raw=path.read_text()
        parts=raw.split('---',2)
        # Dataset headers are flat key:value and include unquoted colons in titles.
        meta={line.split(':',1)[0].strip():line.split(':',1)[1].strip() for line in parts[1].splitlines() if ':' in line}
        body=parts[2]
        sections=list(SECTION.finditer(body))
        for i, match in enumerate(sections):
            section=body[match.start():sections[i+1].start() if i+1<len(sections) else len(body)].strip()
            words=section.split()
            # A conservative word budget approximates 400 tokens, with 40-word overlap.
            for n, offset in enumerate(range(0,len(words),260)):
                text=meta['title']+'\n'+match[2].strip()+'\n'+' '.join(words[offset:offset+300])
                chunks.append(dict(chunk_id=f'{path.stem}:{match[1]}:{n}', section_id=match[1],
                    doc=path.name, doc_type=TYPE.get(meta['doc_type'],meta['doc_type']),
                    status=meta['status'], effective_from=str(meta['effective_from']),
                    doc_id=meta.get('doc_id',''), version=meta.get('version',''),
                    superseded_by=meta.get('superseded_by',''), text=text))
                if offset+300>=len(words): break
    # Catalog facts are public runtime data, never practice answers.
    for row in table('products').to_dict('records'):
        sid='products.csv:'+row['sku']
        chunks.append(dict(chunk_id=sid,section_id=sid,doc='products.csv',doc_type='catalog',
                           status='current',effective_from='',doc_id='',version='',superseded_by='',text='Product catalog: '+'; '.join(f'{k}: {v}' for k,v in row.items())))
    return chunks
