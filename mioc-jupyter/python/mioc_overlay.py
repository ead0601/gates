#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# MIOC overlay renderer (v1.6.1)
# - Matches v1.4 "PIN-only" endpoints (no 'PIN:' needed) in NET/PORT
# - CPIN rendered as centered rectangles using DEVICE,CPIN <w,h> (default 20x20), with a crosshair
# - PAD instances (type=PAD) drawn RED; other devices GREEN; NETs PURPLE
# - UI-only nets (key ui_only=true) drawn as GRAY dashed
# - Single --thickness controls ALL outlines/lines and CPIN crosshair thickness
# - Draw order: KEEPIN (cyan) -> PAD/devices -> nets -> CPINs (on top)
#
# Usage:
#   python3 mioc_overlay.py -i die.jpg -a mioc_annotated_netlist.txt -o overlay.png --thickness 3

import argparse
import re
from typing import Dict, Tuple, List, Optional
import cv2
import numpy as np
import os

DIR_TOKENS = set(["N","E","S","W","NE","NW","SE","SW","NS","EW"])

def parse_annotation(path: str):
    """
    Returns:
      devices: {device_type: (w,h)}
      instances: List[dict] -> {type,id,x,y}
      cpins: {pin_id: (x,y,dir_opt,layer)}
      ports: {port_name: [cpin_id, ...]}
      nets:  List[dict] -> {name, role, endpoints[List[str]], kv{dict}, dir_hint:Optional[str]}
      keepins: List[dict] -> {x,y,w,h} from DEVICE,KPIN + INST,KPIN
    """
    devices: Dict[str, Tuple[int,int]] = {}
    instances: List[Dict] = []
    cpins: Dict[str, Tuple[int,int,Optional[str],str]] = {}
    ports: Dict[str, List[str]] = {}
    nets: List[Dict] = []
    keepins: List[Dict] = []

    section = None
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Pass 1: DEVICE sizes
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.upper().startswith("SECTION,"):
            sec = line.split(",")
            if len(sec) >= 3 and sec[0].upper()=="SECTION":
                if sec[2].upper()=="START":
                    section = sec[1].upper()
                elif sec[2].upper()=="END":
                    section = None
            continue
        if section == "DEVICES" and line.startswith("DEVICE,"):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 4:
                dtype = parts[1]
                try:
                    w = int(parts[2]); h = int(parts[3])
                    devices[dtype] = (w,h)
                except ValueError:
                    pass

    # Regex helpers
    # PIN,CPIN,<id>,<x>,<y>[,<dir>],<layer>
    pin_re = re.compile(
        r"^PIN\s*,\s*CPIN\s*,\s*([^,\s]+)\s*,\s*([+-]?\d+)\s*,\s*([+-]?\d+)"
        r"(?:\s*,\s*([NSEW]{1,2}))?\s*,\s*([^,\s]+)",
        re.IGNORECASE
    )
    # INST,<type>,<id>,<x>,<y>[,key=val...]
    inst_re = re.compile(
        r"^INST\s*,\s*([^,\s]+)\s*,\s*([^,\s]+)\s*,\s*([+-]?\d+)\s*,\s*([+-]?\d+)(?:\s*,.*)?$",
        re.IGNORECASE
    )
    # PORT,<name>,<dir>,<cpin1>,<cpin2>,...
    port_re = re.compile(
        r"^PORT\s*,\s*([^,\s]+)\s*,\s*([^,\s]+)\s*,(.*)$",
        re.IGNORECASE
    )
    # NET,<name>,<role>,<ref1>,<ref2>[,<ref3>...][,key=val...]
    net_re = re.compile(
        r"^NET\s*,\s*([^,\s]+)\s*,\s*([^,\s]+)\s*,(.*)$",
        re.IGNORECASE
    )

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        m = pin_re.match(line)
        if m:
            pid = m.group(1)
            try:
                x = int(m.group(2)); y = int(m.group(3))
                dir_opt = m.group(4)  # may be None
                layer = m.group(5)
                cpins[pid] = (x,y,dir_opt,layer)
            except ValueError:
                pass
            continue

        m = inst_re.match(line)
        if m:
            dtype = m.group(1); iid = m.group(2)
            try:
                x = int(m.group(3)); y = int(m.group(4))
                instances.append({"type": dtype, "id": iid, "x": x, "y": y})
            except ValueError:
                pass
            continue

        m = port_re.match(line)
        if m:
            name = m.group(1); pdir = m.group(2); rest = m.group(3)
            toks = [t.strip() for t in rest.split(",") if t.strip()]
            lst = []
            for tok in toks:
                if tok.upper().startswith("PIN:"):
                    tok = tok.split(":",1)[1]
                lst.append(tok)
            if lst:
                ports[name] = lst
            continue

        m = net_re.match(line)
        if m:
            name = m.group(1); role = m.group(2)
            tail = [t.strip() for t in m.group(3).split(",") if t.strip()]
            endpoints: List[str] = []
            kv = {}
            dir_hint = None
            for tok in tail:
                if "=" in tok:
                    k,v = tok.split("=",1)
                    kv[k.strip().lower()] = v.strip()
                elif tok in DIR_TOKENS:
                    dir_hint = tok
                else:
                    if tok.upper().startswith("PIN:"):
                        tok = tok.split(":",1)[1]
                    endpoints.append(tok)
            nets.append({"name": name, "role": role, "endpoints": endpoints, "kv": kv, "dir_hint": dir_hint})
            continue

    # Derive KEEPIN boxes from DEVICE,KPIN + INST,KPIN
    if "KPIN" in devices:
        w,h = devices["KPIN"]
        for inst in instances:
            if inst["type"].upper()=="KPIN":
                keepins.append({"x":inst["x"], "y":inst["y"], "w":w, "h":h})

    return devices, instances, cpins, ports, nets, keepins

def ref_to_xy(ref: str, cpins: Dict[str, Tuple[int,int,Optional[str],str]], ports: Dict[str, List[str]]) -> Optional[Tuple[int,int,Optional[str]]]:
    try:
        if ref.upper().startswith("PIN:"):
            ref = ref.split(":",1)[1]
        if ref.upper().startswith("PORT:"):
            pname = ref.split(":",1)[1]
            lst = ports.get(pname, [])
            if lst:
                pid = lst[0]
                if pid in cpins:
                    x,y,dir_opt,_ = cpins[pid]
                    return (x,y,dir_opt)
            return None
        if ref in cpins:
            x,y,dir_opt,_ = cpins[ref]
            return (x,y,dir_opt)
    except Exception:
        return None
    return None

def elbow_dir_from_pin_dir(pin_dir: Optional[str]) -> Optional[str]:
    if not pin_dir:
        return None
    pin_dir = pin_dir.upper()
    if any(d in pin_dir for d in ["E","W"]):
        return "EW"
    if any(d in pin_dir for d in ["N","S"]):
        return "NS"
    return None

def draw_manhattan(img, p1, p2, color, thickness=2, dir_pref: Optional[str]=None):
    x1,y1 = p1; x2,y2 = p2
    horizontal_first = True
    if dir_pref == "NS":
        horizontal_first = False
    elif dir_pref == "EW":
        horizontal_first = True
    elif abs(x2-x1) < abs(y2-y1):
        horizontal_first = True
    else:
        horizontal_first = False

    if horizontal_first:
        elbow = (x2, y1)
        cv2.line(img, (x1,y1), elbow, color, thickness, lineType=cv2.LINE_AA)
        cv2.line(img, elbow, (x2,y2), color, thickness, lineType=cv2.LINE_AA)
    else:
        elbow = (x1, y2)
        cv2.line(img, (x1,y1), elbow, color, thickness, lineType=cv2.LINE_AA)
        cv2.line(img, elbow, (x2,y2), color, thickness, lineType=cv2.LINE_AA)

def draw_dashed_line(img, a, b, color, thickness=2, dash_px=12, gap_px=8):
    x1,y1 = a; x2,y2 = b
    if x1 == x2:
        length = abs(y2 - y1)
        sign = 1 if y2>=y1 else -1
        pos = 0
        while pos < length:
            y_start = y1 + sign*pos
            y_end = y1 + sign*min(length, pos + dash_px)
            cv2.line(img, (x1, y_start), (x2, y_end), color, thickness, lineType=cv2.LINE_AA)
            pos += dash_px + gap_px
    elif y1 == y2:
        length = abs(x2 - x1)
        sign = 1 if x2>=x1 else -1
        pos = 0
        while pos < length:
            x_start = x1 + sign*pos
            x_end = x1 + sign*min(length, pos + dash_px)
            cv2.line(img, (x_start, y1), (x_end, y2), color, thickness, lineType=cv2.LINE_AA)
            pos += dash_px + gap_px
    else:
        cv2.line(img, (x1,y1), (x2,y2), color, thickness, lineType=cv2.LINE_AA)

def draw_dashed_manhattan(img, p1, p2, color, thickness=2, dir_pref: Optional[str]=None):
    x1,y1 = p1; x2,y2 = p2
    horizontal_first = True
    if dir_pref == "NS":
        horizontal_first = False
    elif dir_pref == "EW":
        horizontal_first = True
    elif abs(x2-x1) < abs(y2-y1):
        horizontal_first = True
    else:
        horizontal_first = False

    dash_px = max(6, thickness*4)
    gap_px  = max(4, thickness*3)

    if horizontal_first:
        elbow = (x2, y1)
        draw_dashed_line(img, (x1,y1), elbow, color, thickness, dash_px, gap_px)
        draw_dashed_line(img, elbow, (x2,y2), color, thickness, dash_px, gap_px)
    else:
        elbow = (x1, y2)
        draw_dashed_line(img, (x1,y1), elbow, color, thickness, dash_px, gap_px)
        draw_dashed_line(img, elbow, (x2,y2), color, thickness, dash_px, gap_px)

def render_overlay(die_img_path: str, annot_path: str, out_path: str, thickness: int = 2, draw_keepin: bool = True):
    RED     = (0, 0, 255)
    GREEN   = (0, 255, 0)
    PURPLE  = (255, 0, 255)
    GRAY    = (128,128,128)
    CYAN    = (255,255,0)

    t = int(max(1, thickness))

    img = cv2.imread(die_img_path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {die_img_path}")

    devices, instances, cpins, ports, nets, keepins = parse_annotation(annot_path)

    if draw_keepin and keepins:
        for kb in keepins:
            cv2.rectangle(img, (kb["x"], kb["y"]), (kb["x"]+kb["w"], kb["y"]+kb["h"]), CYAN, thickness=t, lineType=cv2.LINE_AA)

    # 1) Devices
    for inst in instances:
        dtype = inst["type"]
        if dtype not in devices:
            continue
        w,h = devices[dtype]
        x,y = inst["x"], inst["y"]
        color = RED if dtype.upper()=="PAD" else GREEN
        cv2.rectangle(img, (x,y), (x+w, y+h), color, thickness=t, lineType=cv2.LINE_AA)

    # 2) Nets
    for net in nets:
        eps = net.get("endpoints", [])
        kv  = net.get("kv", {})
        ui_only = (kv.get("ui_only","").lower()=="true")
        coords: List[Tuple[int,int,Optional[str]]] = []
        for ref in eps:
            xy = ref_to_xy(ref, cpins, ports)
            if xy is not None:
                coords.append(xy)
        if len(coords) >= 2:
            p1 = (coords[0][0], coords[0][1])
            p2 = (coords[-1][0], coords[-1][1])
            dir_pref = elbow_dir_from_pin_dir(coords[-1][2]) or elbow_dir_from_pin_dir(coords[0][2])
            if ui_only:
                draw_dashed_manhattan(img, p1, p2, GRAY, thickness=t, dir_pref=dir_pref)
            else:
                draw_manhattan(img, p1, p2, PURPLE, thickness=t, dir_pref=dir_pref)

    # 3) CPINs
    c_w, c_h = devices.get("CPIN", (20,20))
    half_w = c_w//2; half_h = c_h//2
    for pid, (px,py,dir_opt,layer) in cpins.items():
        tl = (px - half_w, py - half_h)
        br = (px + (c_w - half_w), py + (c_h - half_h))
        cv2.rectangle(img, tl, br, RED, thickness=t, lineType=cv2.LINE_AA)
        cv2.line(img, (px - half_w, py), (px + half_w, py), RED, thickness=t, lineType=cv2.LINE_AA)
        cv2.line(img, (px, py - half_h), (px, py + half_h), RED, thickness=t, lineType=cv2.LINE_AA)

    ext = os.path.splitext(out_path)[1].lower()
    if ext in [".jpg", ".jpeg"]:
        ok = cv2.imwrite(out_path, img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    else:
        ok = cv2.imwrite(out_path, img)
    if not ok:
        raise RuntimeError(f"Failed to write: {out_path}")

def main():
    ap = argparse.ArgumentParser(description="Merge die image with annotation overlay (PIN-only, UI-only nets, keep-in box).")
    ap.add_argument("-i", "--image", required=True, help="Path to input die image (e.g., die_flat.jpg)")
    ap.add_argument("-a", "--annotation", required=True, help="Path to annotation file (v1.4-style)")
    ap.add_argument("-o", "--output", required=True, help="Path to output image (.png or .jpg)")
    ap.add_argument("--thickness", type=int, default=2, help="Single thickness for all outlines/lines and CPIN crosshair")
    ap.add_argument("--no-keepin", action="store_true", help="Do not draw keep-in boxes")
    args = ap.parse_args()

    render_overlay(args.image, args.annotation, args.output, thickness=args.thickness, draw_keepin=(not args.no_keepin))

if __name__ == "__main__":
    main()
