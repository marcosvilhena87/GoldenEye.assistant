"""Quality-aware A/B/A report. All states/results are operator-declared."""
from pathlib import Path
from collections import defaultdict
import csv,sys
P=Path(__file__).resolve().parents[1]/"output/csv/autoaim_v3_1_events.csv"
if not P.exists(): sys.exit("No v3.1 events CSV; start observer first")
with P.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
if not rows: sys.exit("No events")
session=sys.argv[1] if len(sys.argv)>1 else rows[-1]["session"]
rows=[r for r in rows if r["session"]==session]
if not rows: sys.exit("Session not found")
rows.sort(key=lambda x:(int(x["epoch"]),int(x["command_id"]) if x["command_id"].isdigit() else 0))
initials=[r for r in rows if r["event"]=="INITIAL_STATE_OPERATOR"]
initial=initials[0]["detail"] if initials else None
print("SESSION",session,"INITIAL",initial or "UNKNOWN")
groups=defaultdict(list)
for r in rows:
    if r["phase"].startswith("aba_"): groups[(int(r["epoch"]),r["phase"])].append(r)
expected=[("aba_enabled_1","enabled"),("aba_disabled","disabled"),("aba_enabled_2","enabled")]
issues=[];observations={}
for name,state in expected:
    matches=[(epoch,events) for (epoch,p),events in groups.items() if p==name]
    if not matches:
        issues.append(name+": MISSING_PHASE");print(name,": MISSING_PHASE");continue
    if len(matches)!=1: issues.append(name+": MULTIPLE_EPOCHS")
    epoch,events=matches[-1]
    results=[r["detail"] for r in events if r["event"]=="OPERATOR"]
    interventions=[r["detail"] for r in events if r["event"]=="INTERVENTION_OPERATOR"]
    rpress=sum(r["event"]=="RAW_R" and r["detail"]=="pressed" for r in events)
    zpress=sum(r["event"]=="RAW_Z" and r["detail"]=="pressed" for r in events)
    flags=[]
    if not results: flags.append("MISSING_RESULT")
    if len(results)!=1: flags.append("RESULT_COUNT_"+str(len(results)))
    # A1 is an existing initial configuration, not a change during trial.
    if name=="aba_enabled_1":
        if initial!="enabled": flags.append("INITIAL_ENABLED_UNCONFIRMED")
    elif not any(("enabled" if state=="enabled" else "disabled") in v for v in interventions):
        flags.append("MISSING_STATE_CHANGE_ANNOTATION")
    # Even detected raw buttons are provisional and not sufficient to certify R/Z actions.
    if rpress or zpress: flags.append("RAW_BUTTON_EDGES_PRESENT")
    issues.extend(name+": "+f for f in flags)
    observations[name]=results
    print(f"{name}: epoch={epoch} result={results or '-'} interventions={interventions or '-'} raw_R={rpress} raw_Z={zpress} issues={flags or 'none'}")
if all(k in observations for k,_ in expected):
    pattern=[observations[k][0] if observations[k] else "MISSING" for k,_ in expected]
    print("A/B/A operator-observed:", " -> ".join(pattern))
print("QUALITY:", "INCOMPLETE" if issues else "COMPLETE_OPERATOR_ANNOTATIONS")
for issue in issues: print(" -",issue)
print("Not validated: initial settings, target positions, or auto-aim effects are not read from game memory.")
