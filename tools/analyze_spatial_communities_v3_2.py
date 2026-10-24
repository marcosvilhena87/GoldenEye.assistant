"""v3.2 community robustness on the *existing* v3.1 phase-pair CSV.

No address recognition, inference of pointers, or hypothesis significance.
"""
import argparse
import csv
from collections import Counter,defaultdict
from itertools import combinations
from pathlib import Path

try:
    from .analyze_spatial_position_v2_4 import PHASES, START, END
except ImportError:
    from analyze_spatial_position_v2_4 import PHASES, START, END

BLOCKS=tuple(f"0x{x:06X}" for x in range(START,END+1,4))
PAIRS=tuple(combinations(BLOCKS,2))
PARAMS=((0,.85,6),(.02,.90,7),(.05,.90,7),(.02,.95,7),(.02,.90,9))
EDGE_FIELDS=("original","replica","left","right","gain","sync","min_phases",
             "supported_phases","direct","direct_edge_weight","phase_bitmap")
COMM_FIELDS=("original","replica","component","community","block","size","members",
             "internal_edges","possible_edges","density","external_edges",
             "is_transitively_connected","method")
SENSE_FIELDS=("original","replica","gain","sync","min_phases","edge_count",
              "node_count","component_count","largest_component",
              "baseline_edge_overlap","baseline_edge_jaccard")
PERSIST_FIELDS=("original","replica","phase","total_supported_edges",
                "baseline_edges_supported","baseline_edge_fraction",
                "unique_nodes","note")
RANK_FIELDS=("original","replica","left","right","support_count","gain_mean",
             "logloss_mean","sync_mean","selection_rank","note")

def read_csv(path):
    with path.open(encoding="utf8",newline="") as fp:return list(csv.DictReader(fp))

def validate(rows):
    if len(rows)!=len(PAIRS)*len(PHASES):raise ValueError("Incomplete v3.1 phase-pairs CSV")
    expected={(l,r,p) for l,r in PAIRS for p in PHASES}
    seen=set()
    session_ids=set()
    for r in rows:
        key=(r["left"],r["right"],r["phase"])
        if key not in expected or key in seen:raise ValueError("Duplicate or unknown pair/phase")
        seen.add(key)
        session_ids.add((r["original"],r["replica"]))
        for field in ("accuracy_gain","logloss_gain"):
            float(r[field])
        if r["test_sync"]!="":float(r["test_sync"])
    if seen!=expected or len(session_ids)!=1:raise ValueError("Mixed sessions or missing observations")
    original,replica=next(iter(session_ids))
    if original==replica:raise ValueError("Distinct sessions required")
    return original,replica

def qualifies(r,gain,sync):
    return float(r["accuracy_gain"])>=gain and r["test_sync"]!="" and float(r["test_sync"])>=sync

def edges_for(data,gain,sync,min_phases):
    return {pair for pair,observations in data.items()
            if sum(qualifies(r,gain,sync) for r in observations)>=min_phases}

def components(nodes,edges):
    adj={node:set() for node in nodes}
    for l,r in edges:adj[l].add(r);adj[r].add(l)
    remaining=set(nodes);out=[]
    while remaining:
        first=min(remaining);remaining.remove(first);todo=[first];members={first}
        while todo:
            for neighbor in sorted(adj[todo.pop()]):
                if neighbor in remaining:
                    remaining.remove(neighbor);members.add(neighbor);todo.append(neighbor)
        out.append(tuple(sorted(members)))
    return sorted(out,key=lambda group:group[0])

def community_partition(nodes,edges):
    # Deterministic modularity-increase agglomeration (unweighted undirected).
    # Only strictly positive modularity increments merge communities.
    m=len(edges)
    groups=[frozenset([x]) for x in nodes]
    if not m:return tuple((x,) for x in sorted(nodes))
    degrees=Counter(x for pair in edges for x in pair)
    while True:
        best_gain=0.0;best=None
        for i,j in combinations(range(len(groups)),2):
            a,b=groups[i],groups[j]
            crossing=sum((l in a and r in b) or (r in a and l in b) for l,r in edges)
            if not crossing:continue
            ka=sum(degrees[x] for x in a);kb=sum(degrees[x] for x in b)
            delta=crossing/m-(ka*kb)/(2*m*m)
            if delta>best_gain+1e-12:
                best_gain=delta;best=(i,j)
        if best is None:break
        i,j=best
        groups=[g for k,g in enumerate(groups) if k not in (i,j)]+[groups[i]|groups[j]]
        groups.sort(key=lambda g:min(g))
    return tuple(tuple(sorted(g)) for g in groups)

def audit(rows):
    original,replica=validate(rows)
    data=defaultdict(list)
    for r in rows:data[(r["left"],r["right"])].append(r)
    for pair in data:data[pair].sort(key=lambda r:PHASES.index(r["phase"]))
    g0,s0,n0=PARAMS[1]
    baseline=edges_for(data,g0,s0,n0)
    details=[];rank=[]
    for pair,obs in sorted(data.items()):
        direct=pair in baseline
        support=sum(qualifies(r,g0,s0) for r in obs)
        details.append(dict(original=original,replica=replica,left=pair[0],right=pair[1],
            gain=g0,sync=s0,min_phases=n0,supported_phases=support,direct=int(direct),
            direct_edge_weight=support if direct else 0,
            phase_bitmap="".join("1" if qualifies(r,g0,s0) else "0" for r in obs)))
        rank.append(dict(original=original,replica=replica,left=pair[0],right=pair[1],
            support_count=support,
            gain_mean=sum(float(r["accuracy_gain"]) for r in obs)/len(obs),
            logloss_mean=sum(float(r["logloss_gain"]) for r in obs)/len(obs),
            sync_mean=sum(float(r["test_sync"]) for r in obs if r["test_sync"]!="")/
                max(1,sum(r["test_sync"]!="" for r in obs)),
            selection_rank=0,
            note="exploratory_190_pairs_no_multiple_comparison_adjustment"))
    rank.sort(key=lambda r:(-r["support_count"],-r["gain_mean"],r["left"],r["right"]))
    for i,r in enumerate(rank,1):r["selection_rank"]=i
    grouped=components(BLOCKS,baseline)
    communities=[]
    for comp_index,comp in enumerate(grouped,1):
        subset={(a,b) for a,b in baseline if a in comp and b in comp}
        # Greedy splitting inside each connected component.
        partition=community_partition(comp,subset)
        for community_index,members in enumerate(partition,1):
            member_set=set(members)
            internal=sum(a in member_set and b in member_set for a,b in baseline)
            external=sum((a in member_set)!=(b in member_set) for a,b in baseline)
            possible=len(members)*(len(members)-1)//2
            members_str=";".join(members)
            transitive=int(len(members)>1 and internal<possible)
            for member in members:
                communities.append(dict(original=original,replica=replica,
                    component=comp_index,community=community_index,block=member,
                    size=len(members),members=members_str,internal_edges=internal,
                    possible_edges=possible,density=internal/possible if possible else "",
                    external_edges=external,is_transitively_connected=transitive,
                    method="deterministic_greedy_modularity_exploratory"))
    sensitivity=[]
    for gain,sync,n in PARAMS:
        candidate=edges_for(data,gain,sync,n)
        comp=components(BLOCKS,candidate)
        both=len(candidate&baseline);either=len(candidate|baseline)
        sensitivity.append(dict(original=original,replica=replica,gain=gain,sync=sync,
            min_phases=n,edge_count=len(candidate),
            node_count=len({x for pair in candidate for x in pair}),
            component_count=len(comp),largest_component=max(map(len,comp)),
            baseline_edge_overlap=both,baseline_edge_jaccard=both/either if either else 1))
    persist=[]
    for i,phase in enumerate(PHASES):
        supported={pair for pair,obs in data.items() if qualifies(obs[i],g0,s0)}
        overlap=len(baseline&supported)
        persist.append(dict(original=original,replica=replica,phase=phase,
            total_supported_edges=len(supported),baseline_edges_supported=overlap,
            baseline_edge_fraction=overlap/len(baseline) if baseline else "",
            unique_nodes=len({x for pair in supported for x in pair}),
            note="same_sessions_exploratory_not_independent_validation"))
    return details,communities,sensitivity,persist,rank

OUTPUTS=(("_edges.csv",EDGE_FIELDS),("_communities.csv",COMM_FIELDS),
         ("_sensitivity.csv",SENSE_FIELDS),("_phase_persistence.csv",PERSIST_FIELDS),
         ("_ranking.csv",RANK_FIELDS))
def run(original,replica,root):
    path=root/"output"/"csv"/f"spatial_v3_1_{original}__{replica}_phase_pairs.csv"
    rows=read_csv(path)
    if validate(rows)!=(original,replica):raise ValueError("Session identifier mismatch")
    results=audit(rows)
    base=root/"output"/"csv"/f"spatial_v3_2_{original}__{replica}"
    paths=[Path(str(base)+name) for name,_ in OUTPUTS]
    if any(path.exists() for path in paths):
        raise FileExistsError("Refusing to overwrite v3.2 files")
    for path,(_,fields),group in zip(paths,OUTPUTS,results):
        with path.open("x",encoding="utf8",newline="") as fp:
            writer=csv.DictWriter(fp,fieldnames=fields)
            writer.writeheader();writer.writerows(group)
    return paths,results

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("original");p.add_argument("replica")
    p.add_argument("--root",type=Path,default=Path("."))
    args=p.parse_args()
    paths,results=run(args.original,args.replica,args.root.resolve())
    for path,group in zip(paths,results):print(f"Wrote {path} rows={len(group)}")
    print("No community is established as a memory layout or physical coordinate.")
