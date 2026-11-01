"""Independent, stateful apt.dat envelope checks for the KIAH R03 build.

The first version line is a file header, not a 1200 routing record.
Airport children are invalid until a 1/16/17 declaration establishes their owner.
"""
from pathlib import Path
from collections import Counter
import json
import sys

def check_structure(path, expected_counts=True):
    rows=[(i+1,s.strip()) for i,s in enumerate(Path(path).read_text(encoding='utf-8-sig').splitlines()) if s.strip()]
    errors=[]; airports={}; owner=None; finished=False; routing_headers=0
    if len(rows)<4 or rows[0][1] not in ('I','A') or rows[1][1].split()[0]!='1200':
        errors.append('Invalid apt.dat file preamble')
    for number,text in rows[2:]:
        fields=text.split()
        if not fields[0].isdigit():
            errors.append(f'Non-numeric record at line {number}');continue
        code=int(fields[0])
        if finished:
            errors.append(f'Data follows EOF at line {number}');continue
        if code==99:
            finished=True;continue
        if code in (1,16,17):
            if len(fields)<6:
                errors.append(f'Incomplete airport declaration at line {number}');continue
            owner=fields[4]
            if owner in airports:errors.append(f'Duplicate airport {owner}')
            airports[owner]={'header':text,'records':[]}
            continue
        if owner is None:
            if not any(e.startswith('Airport data precedes') for e in errors):
                errors.append(f'Airport data precedes an airport declaration at line {number}')
            continue
        airports[owner]['records'].append((code,fields))
        if code==1200:routing_headers+=1
    if not finished:errors.append('Missing EOF record')
    if list(airports)!=['KIAH']:errors.append(f'Expected one KIAH airport; found {list(airports)}')
    records=airports.get('KIAH',{}).get('records',[])
    counts=Counter(c for c,s in records)
    starts={' '.join(s[6:]):s for c,s in records if c==1300}
    if expected_counts and airports:
        for c,n in {100:5,1300:240,1201:1416,1202:988,1206:588,1500:32}.items():
            if counts[c]!=n:errors.append(f'Record {c}: expected {n}, found {counts[c]}')
        if routing_headers!=1:errors.append(f'Expected one routing header; found {routing_headers}')
        if len(starts)!=counts[1300]:errors.append('Duplicate start names')
        for name in ('Gate B1','Gate B5','Gate B23','Gate D3','Gate A20'):
            if name not in starts:errors.append(f'Missing start: {name}')
        if not any(c==1302 and s[1:]==['icao_code','KIAH'] for c,s in records):errors.append('KIAH ICAO metadata missing')
        nodes=[int(s[4]) for c,s in records if c==1201]
        if len(nodes)!=len(set(nodes)):errors.append('Duplicate taxi node IDs')
        known=set(nodes)
        for c,s in records:
            if c in (1202,1206) and (int(s[1]) not in known or int(s[2]) not in known):
                errors.append('Route references a missing node');break
    return {'passed':not errors,'errors':errors,'airport_ids':list(airports),'record_counts':dict(counts),'b5_present':'Gate B5' in starts}

if __name__=='__main__':
    result=check_structure(sys.argv[1]);print(json.dumps(result,indent=2));sys.exit(0 if result['passed'] else 1)
