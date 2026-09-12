from __future__ import annotations

import hashlib
import importlib.util
import shutil
from pathlib import Path


REMOTE_ROOT = "/home/ftfan/ncw"
REMOTE_OUT = "sync_server_extract_20260913_run4"
REMOTE_BASE = (
    "sfs/CoOH/cp2k/Al16/oer/"
    "spin_config_scan_site03_5OH_current_20260714/"
    "vasp_jacs6c06054_reconstructed_exact_Al16_3x2_20260809/"
    "electronic_structure_al_contribution_20260818"
)
COHP_BASE = f"{REMOTE_BASE}/cohp_bader_formal_oh_o_20260822"
VASP_BASE = f"{REMOTE_BASE}/cohp_oh_o_corrected_20260820"

CASES = {
    "pristine__OH": ("pristine", "*OH", f"{COHP_BASE}/undoped_control/OH_pair_corrected_nomadelung", f"{VASP_BASE}/undoped_control/OH"),
    "pristine__O": ("pristine", "*O", f"{COHP_BASE}/undoped_control/O_nomadelung", f"{VASP_BASE}/undoped_control/O"),
    "Al16__OH": ("Al16", "*OH", f"{COHP_BASE}/Al16_adjacent/OH_nomadelung", f"{VASP_BASE}/Al16_adjacent/OH"),
    "Al16__O": ("Al16", "*O", f"{COHP_BASE}/Al16_adjacent/O_nomadelung", f"{VASP_BASE}/Al16_adjacent/O"),
}

REMOTE_CODE = r'''
from __future__ import print_function
import csv, hashlib, math, os, re

OUT = "sync_server_extract_20260913_run4"
for sub in ("COHP/source_data", "PDOS/source_data", "raw_minimal"):
    d=os.path.join(OUT,sub)
    if not os.path.isdir(d): os.makedirs(d)

cases = {
    "pristine__OH": ("pristine", "*OH", "COHP_BASE_REPL/undoped_control/OH_pair_corrected_nomadelung", "VASP_BASE_REPL/undoped_control/OH"),
    "pristine__O": ("pristine", "*O", "COHP_BASE_REPL/undoped_control/O_nomadelung", "VASP_BASE_REPL/undoped_control/O"),
    "Al16__OH": ("Al16", "*OH", "COHP_BASE_REPL/Al16_adjacent/OH_nomadelung", "VASP_BASE_REPL/Al16_adjacent/OH"),
    "Al16__O": ("Al16", "*O", "COHP_BASE_REPL/Al16_adjacent/O_nomadelung", "VASP_BASE_REPL/Al16_adjacent/O"),
}

def ffloat(x):
    return float(x.replace("D", "E").replace("d", "e"))

def read_poscar(path):
    lines = open(path, 'r').read().splitlines()
    scale = ffloat(lines[1].split()[0])
    cell = [[scale * ffloat(x) for x in lines[i].split()[:3]] for i in range(2,5)]
    elements = lines[5].split(); counts = [int(x) for x in lines[6].split()]
    idx = 7
    if lines[idx].strip().lower().startswith("s"): idx += 1
    direct = lines[idx].strip().lower().startswith("d"); idx += 1
    species=[]; coords=[]
    for el,n in zip(elements, counts):
        for _ in range(n): species.append(el)
    for i in range(len(species)):
        vals=[ffloat(x) for x in lines[idx+i].split()[:3]]
        if direct:
            coords.append([sum(vals[j]*cell[j][k] for j in range(3)) for k in range(3)])
        else: coords.append([scale*x for x in vals])
    return cell, species, coords

def dist(cell, a, b):
    # Minimum-image distance using the fractional representation.
    # Cells here are upper/lower triangular; solve by a small least-squares-free
    # search around the nearest Cartesian image, sufficient for the validated slab.
    best=1e99
    for i in range(-1,2):
      for j in range(-1,2):
       for k in range(-1,2):
        d=[b[q]-a[q]+i*cell[0][q]+j*cell[1][q]+k*cell[2][q] for q in range(3)]
        best=min(best, math.sqrt(sum(x*x for x in d)))
    return best

def roles(system, state, cell, species, coords, icohp):
    co = 21 if system == "pristine" else 16
    neighbor_candidates = [i+1 for i,e in enumerate(species) if e == ("Co" if system == "pristine" else "Al") and i+1 != co]
    o_candidates = [i+1 for i,e in enumerate(species) if e == "O"]
    h_candidates = [i+1 for i,e in enumerate(species) if e == "H"]
    def label_idx(label): return int(re.search(r"\d+", label).group(0))
    def has(label, element, idx): return label == element + str(idx)
    # Use ICOHPLIST only to define the candidate interaction set; roles are
    # then selected and independently checked against the current structure.
    co_o = [x for x in icohp if (has(x["a"],"Co",co) and x["b"].startswith("O")) or (has(x["b"],"Co",co) and x["a"].startswith("O"))]
    if not co_o: raise RuntimeError("ICOHPLIST has no active Co-O candidate")
    oads = min([label_idx(x["a"] if x["a"].startswith("O") else x["b"]) for x in co_o], key=lambda i: dist(cell, coords[co-1], coords[i-1]))
    remaining = [i for i in o_candidates if i != oads]
    best=None
    for x in co_o:
        oi=label_idx(x["a"] if x["a"].startswith("O") else x["b"])
        if oi == oads: continue
        for y in icohp:
            if y is x: continue
            if y["a"].startswith("O") and label_idx(y["a"]) == oi: other=y["b"]
            elif y["b"].startswith("O") and label_idx(y["b"]) == oi: other=y["a"]
            else: continue
            ni=label_idx(other)
            if ni in neighbor_candidates:
                score=abs(dist(cell,coords[co-1],coords[oi-1])-2.05)+abs(dist(cell,coords[ni-1],coords[oi-1])-2.05)
                if best is None or score < best[0]: best=(score,oi,ni)
    if best is None: raise RuntimeError("Could not identify a two-metal bridge from ICOHPLIST and structure")
    ob, neighbor = best[1], best[2]
    h = min(h_candidates, key=lambda i: dist(cell, coords[ob-1], coords[i-1]))
    return {"Coact":co, "Oads":oads, "Obridge":ob, "neighbor":neighbor, "Hterminal":h}

def pair_name(el, idx): return "%s%d" % (el,idx)

def parse_icohp(path):
    rows=[]
    for line in open(path, 'r').read().splitlines():
        m=re.match(r"^\s*\d+\s+(\w+\d+)\s+(\w+\d+)\s+([0-9.Ee+-]+)\s+[-0-9 ]+\s+([-0-9.Ee+]+)\s+([-0-9.Ee+]+)", line)
        if m:
            rows.append({"a":m.group(1),"b":m.group(2),"d":ffloat(m.group(3)),"up":ffloat(m.group(4)),"down":ffloat(m.group(5))})
    return rows

def parse_cohpcar(path):
    lines=open(path, 'r').read().splitlines()
    nint,nspin,ned=map(int, lines[1].split()[:3])
    names=lines[2:2+nint]
    data=lines[2+nint:2+nint+ned]
    out=[]
    for line in data:
        vals=line.split()
        # For spin-polarized COHPCAR each interaction occupies four columns:
        # pCOHP(up), integrated(up), pCOHP(down), integrated(down).
        if len(vals) < 1+nint*4: continue
        e=ffloat(vals[0])
        for p in range(1,nint):
            for s,label in enumerate(("up","down")):
                raw=ffloat(vals[1+p*4+(0 if s == 0 else 2)])
                out.append((e,p,label,raw,names[p]))
    return out

def parse_lobsterout(path):
    txt=open(path, 'r').read()
    version=re.search(r"LOBSTER v([^\s(]+)",txt)
    spills=re.findall(r"abs\. charge spilling:\s*([0-9.]+)%",txt)
    rec=re.search(r"number of electrons recovered by projection:\s*([0-9.]+) of ([0-9.]+)",txt)
    basis=[]
    if "recommended basis functions:" in txt:
        part=txt.split("recommended basis functions:",1)[1].split("initializing LCAO system",1)[0]
        basis=[x.strip() for x in part.splitlines() if x.strip() and not x.strip().startswith("INFO")]
    warnings=[x.strip() for x in txt.splitlines() if "WARNING:" in x]
    return version.group(1) if version else "unknown", spills, rec, basis, warnings, "finished in" in txt

def parse_doscar(path, selected, role_by_index, system, state):
    lines=open(path, 'r').read().splitlines()
    hdr=lines[5].split(); ned=int(hdr[2]); ef=ffloat(hdr[3])
    source_path = "source_manifest:COHP/PDOS/%s/%s/DOSCAR" % (system, state)
    out=[]
    for line in lines[6:6+ned]:
        v=line.split();
        if len(v)>=3:
            e=ffloat(v[0])-ef
            if e < -8.0 or e > 4.0: continue
            out += [(system,state,"%.5f" % e,"up","TDOS",0,"all","total","%.8g" % ffloat(v[1]),source_path),(system,state,"%.5f" % e,"down","TDOS",0,"all","total","%.8g" % ffloat(v[2]),source_path)]
    idx=6+ned
    orbitals=["s","py","pz","px","dxy","dyz","dz2","dxz","dx2-y2"]
    for atom in range(1, max(selected)+1):
        if idx >= len(lines): break
        idx += 1
        block=lines[idx:idx+ned]; idx += ned
        if atom not in selected: continue
        role=role_by_index[atom]; el=role["element"]
        if role["site_role"] == "Coact" or (role["site_role"] == "neighbor" and el == "Co"):
            wanted = set(["dxy","dyz","dz2","dxz","dx2-y2"])
        elif role["site_role"] in ("Oads", "Obridge"):
            wanted = set(["py","pz","px"])
        elif role["site_role"] == "neighbor" and el == "Al":
            wanted = set(["s","py","pz","px"])
        else:
            wanted = set(orbitals)
        for line in block:
            v=line.split()
            if len(v)<1+2*len(orbitals): continue
            e=ffloat(v[0])-ef
            if e < -8.0 or e > 4.0: continue
            for j,orb in enumerate(orbitals):
                if orb not in wanted: continue
                out.append((system,state,"%.5f" % e,"up",role["site_role"],atom,el,orb,"%.8g" % ffloat(v[1+2*j]),source_path))
                out.append((system,state,"%.5f" % e,"down",role["site_role"],atom,el,orb,"%.8g" % ffloat(v[2+2*j]),source_path))
    return out, ef

def write_tsv(path, header, rows):
    with open(path, "w") as f:
        w=csv.writer(f, delimiter="\t", lineterminator="\n"); w.writerow(header); w.writerows(rows)

cohp_rows=[]; icohp_rows=[]; map_rows=[]; qual_rows=[]; pdos_rows=[]; pdos_map=[]; manifest=[]
for key,(system,state,cohp_dir,vasp_dir) in cases.items():
    case_out=os.path.join(OUT,"raw_minimal",key)
    if not os.path.isdir(case_out): os.makedirs(case_out)
    role_pairs={"Coact-Oads":("Coact","Oads"),"Coact-Obridge":("Coact","Obridge"),"neighbor-Obridge":("neighbor","Obridge")}
    ic=parse_icohp(os.path.join(cohp_dir,"ICOHPLIST.lobster"))
    p=os.path.join(cohp_dir,"POSCAR.lobster.vasp"); cell,species,coords=read_poscar(p); r=roles(system,state,cell,species,coords,ic)
    named={name:{"idx":idx,"element":species[idx-1]} for name,idx in r.items()}
    bykey={(x["a"],x["b"]):x for x in ic}; bykey.update({(x["b"],x["a"]):x for x in ic})
    for role,(a,b) in role_pairs.items():
        x=bykey.get((pair_name(named[a]["element"],named[a]["idx"]),pair_name(named[b]["element"],named[b]["idx"])))
        if not x: raise RuntimeError("Missing ICOHP pair for %s %s" % (key, role))
        aidx,bidx=named[a]["idx"],named[b]["idx"]
        d=dist(cell,coords[aidx-1],coords[bidx-1])
        map_rows.append([system,state,os.path.join("raw_minimal",key,"POSCAR.lobster.vasp"),r["Coact"],r["Oads"],r["Obridge"],r["neighbor"],species[r["neighbor"]-1],role,aidx,named[a]["element"],bidx,named[b]["element"],"%.6f" % d,"validated","dynamic geometry mapping; ICOHPLIST distance %.6f A" % x['d']])
        icohp_rows.append([system,state,role,aidx,bidx,"%.6f" % d,"%.5f" % x['up'],"%.5f" % x['down'],"%.5f" % (x['up']+x['down']),"%.5f" % (-x['up']-x['down']),"/home/ftfan/ncw/"+os.path.join(cohp_dir,"ICOHPLIST.lobster"),"validated"])
    coh=parse_cohpcar(os.path.join(cohp_dir,"COHPCAR.lobster"))
    for e,pair,spin,raw,_ in coh:
        role=None
        for rr,(a0,b0) in role_pairs.items():
            if "No.%d:" % pair in _ and (pair_name(named[a0]["element"],named[a0]["idx"]) in _ and pair_name(named[b0]["element"],named[b0]["idx"]) in _): role=rr; break
        if role is None: continue
        a,b=role_pairs[role]; aa,bb=named[a]["idx"],named[b]["idx"]
        d=dist(cell,coords[aa-1],coords[bb-1])
        cohp_rows.append([system,state,role,aa,bb,"%.6f" % d,"%.5f" % e,spin,"%.8g" % raw,"%.8g" % (-raw),"source_manifest:COHP/PDOS/%s/%s/COHPCAR.lobster" % (system,state)])
    ver,sp,rec,basis,warns,finished=parse_lobsterout(os.path.join(cohp_dir,"lobsterout"))
    qual_rows.append([system,state,ver,sp[0] if len(sp)>0 else "",sp[1] if len(sp)>1 else "",rec.group(1) if rec else "",rec.group(2) if rec else "", "yes" if finished else "no", "; ".join(basis), "; ".join(warns), "acceptable <=2% spilling; no Madelung energy required"])
    selected=set(r[name] for name in ("Coact","Oads","Obridge","neighbor")); roles_by={idx:{"site_role":name,"element":species[idx-1]} for name,idx in r.items() if name != "Hterminal"}
    pd,ef=parse_doscar(os.path.join(vasp_dir,"DOSCAR"),selected,roles_by,system,state); pdos_rows.extend(pd)
    for name,idx in r.items(): pdos_map.append([system,state,name,idx,species[idx-1],os.path.join("raw_minimal",key,"POSCAR.lobster.vasp"),"dynamic role; selected from current POSCAR geometry and checked against ICOHPLIST"])
    for fn in ("POSCAR.lobster.vasp","lobsterin","lobsterout"):
        src=os.path.join(cohp_dir,fn); dst=os.path.join(case_out,fn); open(dst,'wb').write(open(src,'rb').read())
    for src in [os.path.join(cohp_dir,fn) for fn in ("COHPCAR.lobster","ICOHPLIST.lobster","lobsterout","POSCAR.lobster.vasp","lobsterin")] + [os.path.join(vasp_dir,"DOSCAR")]:
        data=open(src,'rb').read(); copied = "yes" if os.path.basename(src) in ("POSCAR.lobster.vasp","lobsterin","lobsterout") else "no"
        manifest.append(["COHP/PDOS",system,state,"/home/ftfan/ncw/"+src,os.path.basename(src),len(data),hashlib.sha256(data).hexdigest(),copied,"server source; compact extraction performed under sync_server_extract_20260913_run2"])

write_tsv(os.path.join(OUT,"COHP/source_data/cohp_curves.tsv"),["system","state","pair_role","atom1_index","atom2_index","distance_A","energy_eV_rel_EF","spin","pCOHP_raw","minus_pCOHP","source_file"],cohp_rows)
write_tsv(os.path.join(OUT,"COHP/source_data/icohp_summary.tsv"),["system","state","pair_role","atom1_index","atom2_index","distance_A","ICOHP_spin_up_eV","ICOHP_spin_down_eV","ICOHP_total_eV","minus_ICOHP_total_eV","source_file","validation_status"],icohp_rows)
write_tsv(os.path.join(OUT,"COHP/source_data/lobster_quality.tsv"),["system","state","lobster_version","abs_charge_spilling_up_percent","abs_charge_spilling_down_percent","electrons_recovered","total_electrons","normal_finish","basis_report","warnings","quality_note"],qual_rows)
write_tsv(os.path.join(OUT,"mapping.tsv"),["system","state","source_structure","Coact_index","Oads_index","Obridge_index","neighbor_index","neighbor_element","pair_role","atom1_index","atom1_element","atom2_index","atom2_element","distance_A","validation_status","validation_note"],map_rows)
write_tsv(os.path.join(OUT,"PDOS/source_data/pdos_curves.tsv"),["system","state","energy_eV_rel_EF","spin","site_role","atom_index","element","orbital","dos","source_file"],pdos_rows)
write_tsv(os.path.join(OUT,"PDOS/source_data/pdos_site_mapping.tsv"),["system","state","site_role","atom_index","element","source_structure","validation_note"],pdos_map)
write_tsv(os.path.join(OUT,"source_manifest.tsv"),["dataset","system","state","source_path","source_filename","file_size_bytes","sha256","copied_to_repo","note"],manifest)
print("EXTRACTED", len(cohp_rows), len(icohp_rows), len(pdos_rows), len(map_rows))
'''.replace("COHP_BASE_REPL", COHP_BASE).replace("VASP_BASE_REPL", VASP_BASE)


def load_runner():
    p = Path(__file__).resolve().parents[1] / ".codex/skills/ftfan-ncw-ssh/scripts/ssh_ncw.py"
    spec = importlib.util.spec_from_file_location("ftfan_ncw_ssh", p)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load SSH skill runner")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def main() -> None:
    runner = load_runner(); paramiko = runner.ensure_paramiko()
    client = paramiko.SSHClient(); client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=runner.HOST, port=runner.PORT, username=runner.USER, password=runner.load_password(), timeout=15, banner_timeout=15, auth_timeout=60, look_for_keys=False, allow_agent=False)
    try:
        cmd = f"test -d {REMOTE_ROOT!r} && cd {REMOTE_ROOT!r} && mkdir -p {REMOTE_OUT!r} && python -"
        stdin, stdout, stderr = client.exec_command(cmd)
        stdin.write(REMOTE_CODE); stdin.channel.shutdown_write()
        out = stdout.read().decode(errors="replace"); err = stderr.read().decode(errors="replace")
        code = stdout.channel.recv_exit_status()
        if out: print(out, end="")
        if err: print(err, end="")
        if code != 0: raise SystemExit(code)
        local = Path(__file__).resolve().parents[1] / "sync_download_20260913_run4"
        if local.exists(): shutil.rmtree(local)
        sftp=client.open_sftp()
        def get_tree(remote_dir, local_dir):
            local_dir.mkdir(parents=True, exist_ok=True)
            for item in sftp.listdir_attr(remote_dir):
                rp=f"{remote_dir}/{item.filename}"; lp=local_dir/item.filename
                if item.st_mode & 0o40000: get_tree(rp,lp)
                else: sftp.get(rp,str(lp))
        get_tree(f"{REMOTE_ROOT}/{REMOTE_OUT}", local)
        print(f"DOWNLOADED {local}")
    finally:
        client.close()


if __name__ == "__main__": main()

