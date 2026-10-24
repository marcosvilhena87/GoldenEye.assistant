#!/usr/bin/env python3
"""Triagem exploratoria de dumps RDRAM em pares OFF/ON, sem promover XYZ."""
import argparse
import csv
import json
import math
import struct
from pathlib import Path

def load(path):
    return Path(path).read_bytes()

def decode(raw, order):
    return struct.unpack(order + "f", raw)[0]

def analyze(paths, top):
    d = {k: load(v) for k, v in paths.items()}
    sizes = {len(x) for x in d.values()}
    if len(sizes) != 1:
        raise ValueError("Todos os dumps devem ter o mesmo tamanho, offset-base e dominio")
    n = sizes.pop()
    if n % 4:
        raise ValueError("Dump nao alinhado a 4 bytes; documente offset-base e remova padding")
    out = []
    for i in range(0, n, 4):
        a,b,c,e,f = (d[k][i:i+4] for k in ("off1","off2","on1","on2","rotate"))
        if a == b or c != e: # candidate changed while OFF and stable ON
            continue
        if c != f: # exclude rotate-sensitive
            continue
        rows = []
        for endian, name in ((">", "be"), ("<", "le")):
            vals = [decode(x,endian) for x in (a,b,c,e,f)]
            if not all(math.isfinite(v) and abs(v)<1e8 for v in vals):
                continue
            if abs(vals[0]-vals[1]) <= max(1e-5,1e-6*max(abs(vals[0]),abs(vals[1]))):
                continue
            rows.append({"offset_hex":f"0x{i:06X}","kind":"f32_"+name,
                "off1":vals[0],"off2":vals[1],"on1":vals[2],
                "on2":vals[3],"rotate":vals[4],
                "delta_off":vals[1]-vals[0]})
        out.extend(rows)
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for phase in ("off1","off2","on1","on2","rotate"):
        p.add_argument("--"+phase,required=True,help="Dump RAW RDRAM; mesmo tamanho/base entre todos")
    p.add_argument("--output",default="output/csv/freeze_enemy_candidates_v1.csv")
    args=p.parse_args()
    paths={k:getattr(args,k) for k in ("off1","off2","on1","on2","rotate")}
    out=analyze(paths,100000)
    target=Path(args.output)
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        raise FileExistsError("Saida existente; escolha outro --output para preservar capturas")
    fields=["offset_hex","kind","off1","off2","on1","on2","rotate","delta_off"]
    with target.open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=fields);w.writeheader();w.writerows(out)
    print(json.dumps({"candidates":len(out),"report":str(target),
      "warning":"Apenas floats que mudam em OFF e sao byte-estaveis ON e em rotacao. Nao prova XYZ; falsos negativos esperados."},ensure_ascii=False))
if __name__=="__main__":
    main()
