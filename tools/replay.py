"""Interactive replay of real tracking rows through the three pixel frames.

Inputs are two verbatim data extracts quoted on the same page:

* a tracking window (rows of `/tracking_data/bounding_boxes` in camera_view_px
  and `/tracking_data/chaser_states` in arena_relative_canvas_px), and
* the session's `/calibration_snapshot` (homography_matrix, arena origin and
  size, canvas size, camera native size).

The player applies the matrix to the bbox corners and takes the bounding-rect
center, which is the `target_point_method` the chaser_states dataset declares,
then subtracts `arena_origin_in_canvas_*`. Citrus's own `target_pos_*` and
`chaser_pos_*` are drawn beside the result so the two can be compared frame by
frame. Nothing else is computed.
"""

from __future__ import annotations

import html
import json
from typing import Any


def _layout_from_calibration(calib: dict[str, Any]) -> dict[str, Any]:
    snap = calib["calibration_snapshot"]
    ag = snap["groups"]["arena_geometry"]["attrs"]
    cams = {n: g for n, g in snap["groups"].items() if "homography_matrix" in (g.get("datasets") or {})}
    if len(cams) != 1:
        raise ValueError(f"expected one camera group with homography_matrix, found {sorted(cams)}")
    cam_id, cam = next(iter(cams.items()))
    hds = cam["datasets"]["homography_matrix"]
    if hds["attrs"].get("source_frame") != "camera_view_px" or hds["attrs"].get("dest_frame") != "final_display_canvas_px":
        raise ValueError("homography_matrix does not declare camera_view_px -> final_display_canvas_px")
    native = {}
    acj = snap.get("datasets", {}).get("arena_config_json", {}).get("value")
    if acj:
        for cc in json.loads(acj).get("camera_calibrations", []):
            if str(cc.get("camera_id")) == cam_id:
                native = {"w": cc.get("native_width_px"), "h": cc.get("native_height_px")}
    return {
        "camera_id": cam_id,
        "H": hds["value"],
        "native": native,
        "canvas": {"w": calib["root_attrs"]["stimulus_output_width"], "h": calib["root_attrs"]["stimulus_output_height"]},
        "origin": [ag["arena_origin_in_canvas_x_px"], ag["arena_origin_in_canvas_y_px"]],
        "arena": [ag["arena_region_width_px"], ag["arena_region_height_px"]],
        "exp": {
            "shape": ag.get("experimental_area_shape"),
            "cx": ag.get("experimental_area_center_x_px"),
            "cy": ag.get("experimental_area_center_y_px"),
            "r": ag.get("experimental_area_radius_px"),
            "w": ag.get("experimental_area_width_px"),
            "h": ag.get("experimental_area_height_px"),
        },
        "arena_id": calib["root_attrs"].get("arena_id"),
        "session_uuid": calib["root_attrs"].get("session_uuid"),
    }


PLAYER_CSS = """
.replay{border:1px solid var(--line);border-radius:10px;padding:12px 14px;background:var(--card);margin:14px 0}
.replay .ctl{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:10px;font-size:.9rem}
.replay button{font:inherit;padding:4px 12px;border:1px solid var(--line);border-radius:6px;background:var(--code);color:var(--fg);cursor:pointer}
.replay input[type=range]{flex:1 1 240px}
.replay .panels{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}
.replay .panel h5{margin:0 0 4px;font:600 12px ui-monospace,Menlo,Consolas,monospace;color:var(--fg)}
.replay .panel svg{width:100%;height:auto;display:block;background:var(--code);border-radius:6px}
.replay .readout{margin-top:10px;font:12px ui-monospace,Menlo,Consolas,monospace;display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:4px 18px}
.replay .readout span{color:var(--muted)}
.replay .legend{font-size:.82rem;color:var(--muted);margin-top:8px}
.replay .sw{display:inline-block;width:10px;height:10px;border-radius:50%;vertical-align:middle;margin-right:4px}
"""

PLAYER_JS = r"""
(function(){
  const root = document.getElementById(PID);
  const D = JSON.parse(document.getElementById(PID + '-data').textContent);
  const H = D.calib.H, O = D.calib.origin, A = D.calib.arena, N = D.calib.native, C = D.calib.canvas, E = D.calib.exp;
  const rows = D.chaser, bbox = new Map(D.bbox.map(b => [String(b.payload_frame_id), b]));
  function inv3(m){const [a,b,c]=m[0],[d,e,f]=m[1],[g,h,i]=m[2];const det=a*(e*i-f*h)-b*(d*i-f*g)+c*(d*h-e*g);
    return [[(e*i-f*h)/det,-(b*i-c*h)/det,(b*f-c*e)/det],[-(d*i-f*g)/det,(a*i-c*g)/det,-(a*f-c*d)/det],[(d*h-e*g)/det,-(a*h-b*g)/det,(a*e-b*d)/det]];}
  const Hi = inv3(H);
  function ap(m,p){const w=m[2][0]*p[0]+m[2][1]*p[1]+m[2][2];return [(m[0][0]*p[0]+m[0][1]*p[1]+m[0][2])/w,(m[1][0]*p[0]+m[1][1]*p[1]+m[1][2])/w];}
  // panels: camera (native), canvas (cropped to arena + margin), arena (arena-relative)
  const margin = Math.round(Math.max(A[0],A[1])*0.15);
  const cv = {x0:O[0]-margin, y0:O[1]-margin, w:A[0]+2*margin, h:A[1]+2*margin};
  const P = {
    cam:{svg:root.querySelector('.p-cam svg'), vb:[0,0,N.w,N.h]},
    can:{svg:root.querySelector('.p-can svg'), vb:[cv.x0,cv.y0,cv.w,cv.h]},
    arn:{svg:root.querySelector('.p-arn svg'), vb:[0,0,A[0],A[1]]}};
  for (const k in P){P[k].svg.setAttribute('viewBox',P[k].vb.join(' '));}
  const ns='http://www.w3.org/2000/svg';
  function el(tag,attrs,parent){const e=document.createElementNS(ns,tag);for(const k in attrs)e.setAttribute(k,attrs[k]);parent.appendChild(e);return e;}
  function unit(p){return p.vb[2]/300;} // 1 screen-ish px in panel units
  // static scenery
  const arenaQuadCam=[[O[0],O[1]],[O[0]+A[0],O[1]],[O[0]+A[0],O[1]+A[1]],[O[0],O[1]+A[1]]].map(p=>ap(Hi,p));
  el('rect',{x:0,y:0,width:N.w,height:N.h,fill:'none',stroke:'currentColor','stroke-width':unit(P.cam)*1.5},P.cam.svg);
  el('polygon',{points:arenaQuadCam.map(p=>p.join(',')).join(' '),fill:'none',stroke:'#2a5db0','stroke-width':unit(P.cam)*1.5,'stroke-dasharray':(unit(P.cam)*6)+' '+(unit(P.cam)*4)},P.cam.svg);
  el('rect',{x:O[0],y:O[1],width:A[0],height:A[1],fill:'none',stroke:'#2a5db0','stroke-width':unit(P.can)*1.5},P.can.svg);
  el('rect',{x:0,y:0,width:A[0],height:A[1],fill:'none',stroke:'#2a5db0','stroke-width':unit(P.arn)*1.5},P.arn.svg);
  if (E.shape==='CIRCLE' && E.r){
    el('circle',{cx:O[0]+E.cx,cy:O[1]+E.cy,r:E.r,fill:'#2a5db0','fill-opacity':.08,stroke:'#2a5db0','stroke-width':unit(P.can)},P.can.svg);
    el('circle',{cx:E.cx,cy:E.cy,r:E.r,fill:'#2a5db0','fill-opacity':.08,stroke:'#2a5db0','stroke-width':unit(P.arn)},P.arn.svg);
    const pts=[];for(let k=0;k<72;k++){const t=2*Math.PI*k/72;pts.push(ap(Hi,[O[0]+E.cx+E.r*Math.cos(t),O[1]+E.cy+E.r*Math.sin(t)]));}
    el('polygon',{points:pts.map(p=>p.join(',')).join(' '),fill:'#2a5db0','fill-opacity':.08,stroke:'#2a5db0','stroke-width':unit(P.cam)},P.cam.svg);
  }
  // axes glyphs
  for (const k of ['cam','can','arn']){const p=P[k],u=unit(p),x=p.vb[0],y=p.vb[1];
    el('line',{x1:x,y1:y,x2:x+u*40,y2:y,stroke:'currentColor','stroke-width':u*1.5},p.svg);
    el('line',{x1:x,y1:y,x2:x,y2:y+u*40,stroke:'currentColor','stroke-width':u*1.5},p.svg);
    const t1=el('text',{x:x+u*44,y:y+u*5,'font-size':u*12,fill:'currentColor'},p.svg);t1.textContent='+x';
    const t2=el('text',{x:x+u*4,y:y+u*54,'font-size':u*12,fill:'currentColor'},p.svg);t2.textContent='+y';}
  // dynamic layers
  const L={};
  for (const k of ['cam','can','arn']){L[k]={trail:el('polyline',{fill:'none',stroke:'#c9641b','stroke-width':unit(P[k])*1.2,opacity:.7},P[k].svg),
    box:el('polygon',{fill:'none',stroke:'#c9641b','stroke-width':unit(P[k])*1.5},P[k].svg),
    derived:el('circle',{r:unit(P[k])*4,fill:'#c9641b'},P[k].svg),
    citrus:el('circle',{r:unit(P[k])*6,fill:'none',stroke:'#7a3fb5','stroke-width':unit(P[k])*1.8},P[k].svg),
    chaser:el('circle',{r:1,fill:'#7a9a01','fill-opacity':.55,stroke:'#7a9a01','stroke-width':unit(P[k])},P[k].svg)};}
  const trail=[];
  const out=root.querySelector('.readout'), slider=root.querySelector('input[type=range]'), btn=root.querySelector('.play'), spd=root.querySelector('select');
  slider.max=rows.length-1;
  function fmt(v){return (typeof v==='number')?(Number.isInteger(v)?String(v):v.toFixed(1)):String(v);}
  function show(i){
    const r=rows[i], b=bbox.get(String(r.target_source_frame_id));
    let derivedArena=null, corners=null, rectC=null;
    if (b){
      const cs=[[b.x_min,b.y_min],[b.x_min+b.width,b.y_min],[b.x_min+b.width,b.y_min+b.height],[b.x_min,b.y_min+b.height]];
      corners=cs.map(p=>ap(H,p));
      // Citrus ProjectBoxRect: cv::boundingRect of float points floors both the
      // minimum and the maximum, then adds 1 (inclusive integer rect).
      const xs=corners.map(p=>p[0]),ys=corners.map(p=>p[1]);
      const x0=Math.floor(Math.min(...xs)),x1=Math.floor(Math.max(...xs)),y0=Math.floor(Math.min(...ys)),y1=Math.floor(Math.max(...ys));
      rectC=[x0+(x1-x0+1)/2,y0+(y1-y0+1)/2];
      derivedArena=[rectC[0]-O[0],rectC[1]-O[1]];
      L.cam.box.setAttribute('points',cs.map(p=>p.join(',')).join(' '));
      L.can.box.setAttribute('points',corners.map(p=>p.join(',')).join(' '));
      L.arn.box.setAttribute('points',corners.map(p=>[p[0]-O[0],p[1]-O[1]].join(',')).join(' '));
      const camC=[b.x_min+b.width/2,b.y_min+b.height/2];
      L.cam.derived.setAttribute('cx',camC[0]);L.cam.derived.setAttribute('cy',camC[1]);
      L.can.derived.setAttribute('cx',rectC[0]);L.can.derived.setAttribute('cy',rectC[1]);
      L.arn.derived.setAttribute('cx',derivedArena[0]);L.arn.derived.setAttribute('cy',derivedArena[1]);
      trail.push({cam:camC,can:rectC,arn:derivedArena}); if(trail.length>90)trail.shift();
      for (const k of ['cam','can','arn']) L[k].trail.setAttribute('points',trail.map(t=>t[k].join(',')).join(' '));
    }
    const tArena=[r.target_pos_x,r.target_pos_y], tCan=[tArena[0]+O[0],tArena[1]+O[1]], tCam=ap(Hi,tCan);
    L.arn.citrus.setAttribute('cx',tArena[0]);L.arn.citrus.setAttribute('cy',tArena[1]);
    L.can.citrus.setAttribute('cx',tCan[0]);L.can.citrus.setAttribute('cy',tCan[1]);
    L.cam.citrus.setAttribute('cx',tCam[0]);L.cam.citrus.setAttribute('cy',tCam[1]);
    const cA=[r.chaser_pos_x,r.chaser_pos_y], cC=[cA[0]+O[0],cA[1]+O[1]], cCam=ap(Hi,cC), rr=r.chaser_radius_px||6;
    L.arn.chaser.setAttribute('cx',cA[0]);L.arn.chaser.setAttribute('cy',cA[1]);L.arn.chaser.setAttribute('r',rr);
    L.can.chaser.setAttribute('cx',cC[0]);L.can.chaser.setAttribute('cy',cC[1]);L.can.chaser.setAttribute('r',rr);
    L.cam.chaser.setAttribute('cx',cCam[0]);L.cam.chaser.setAttribute('cy',cCam[1]);L.cam.chaser.setAttribute('r',rr/Math.abs(H[0][0]));
    const d=derivedArena?Math.hypot(derivedArena[0]-tArena[0],derivedArena[1]-tArena[1]):null;
    out.innerHTML=[
      ['row / stimulus_frame_num',i+' / '+r.stimulus_frame_num],
      ['timestamp_ns_session',r.timestamp_ns_session],
      ['is_chasing · target_freshness_state · target_area_state',r.is_chasing+' · '+r.target_freshness_state+' · '+r.target_area_state],
      ['target_source_frame_id → bounding_boxes.payload_frame_id',r.target_source_frame_id+(b?' (found)':' (no bbox row)')],
      ['bbox x_min, y_min, width, height (camera_view_px)',b?[b.x_min,b.y_min,b.width,b.height].map(fmt).join(', '):'—'],
      ['corners through H → cv::boundingRect center (final_display_canvas_px)',rectC?rectC.map(fmt).join(', '):'—'],
      ['minus arena_origin_in_canvas (arena_relative_canvas_px)',derivedArena?derivedArena.map(fmt).join(', '):'—'],
      ['Citrus target_pos_x, target_pos_y (arena_relative_canvas_px)',tArena.map(fmt).join(', ')],
      ['difference, px',d===null?'—':d.toFixed(2)],
      ['Citrus chaser_pos_x, chaser_pos_y · chaser_radius_px',cA.map(fmt).join(', ')+' · '+fmt(rr)],
      ['distance_to_target_px (Citrus)',fmt(r.distance_to_target_px)],
    ].map(([k,v])=>'<div><span>'+k+'</span><br>'+v+'</div>').join('');
    slider.value=i;
  }
  let i=0, playing=false, last=null, raf=null;
  function tick(ts){ if(!playing)return; if(last===null)last=ts;
    const speed=parseFloat(spd.value); const dtWall=(ts-last)*1e6*speed; // ns of session time to advance
    let j=i; while(j+1<rows.length && rows[j+1].timestamp_ns_session-rows[i].timestamp_ns_session<=dtWall) j++;
    if (j===i && ts-last>0 && j+1<rows.length){ if (rows[i+1].timestamp_ns_session-rows[i].timestamp_ns_session<=dtWall) j=i+1; }
    if (j!==i){ i=j; last=ts; show(i); }
    if (i>=rows.length-1){ playing=false; btn.textContent='▶ play'; return; }
    raf=requestAnimationFrame(tick); }
  btn.addEventListener('click',()=>{ playing=!playing; btn.textContent=playing?'❚❚ pause':'▶ play'; last=null; if(playing){ if(i>=rows.length-1){i=0;trail.length=0;} raf=requestAnimationFrame(tick);} });
  slider.addEventListener('input',()=>{ playing=false; btn.textContent='▶ play'; i=parseInt(slider.value,10); trail.length=0; show(i); });
  root.querySelector('.step-b').addEventListener('click',()=>{playing=false;btn.textContent='▶ play';i=Math.max(0,i-1);show(i);});
  root.querySelector('.step-f').addEventListener('click',()=>{playing=false;btn.textContent='▶ play';i=Math.min(rows.length-1,i+1);show(i);});
  show(0);
})();
"""


def render_tracking_replay(window_text: str, calib_text: str, player_id: str = "replay") -> str:
    window = json.loads(window_text)
    calib = json.loads(calib_text)
    lay = _layout_from_calibration(calib)
    if window["root_attrs"].get("session_uuid") != lay["session_uuid"]:
        raise ValueError("tracking window and calibration snapshot come from different sessions")
    chaser = window["datasets"]["chaser_states"]["rows"]
    bbox = window["datasets"]["bounding_boxes"]["rows"]
    cs_attrs = window["datasets"]["chaser_states"]["attrs"]
    if cs_attrs.get("coordinate_frame") != "arena_relative_canvas_px":
        raise ValueError("chaser_states does not declare arena_relative_canvas_px")
    method = cs_attrs.get("target_point_method")
    payload = json.dumps({"calib": lay, "chaser": chaser, "bbox": bbox}, separators=(",", ":"))
    pid = html.escape(player_id)
    sel = window["selection"]
    n = len(chaser)
    dur = (chaser[-1]["timestamp_ns_session"] - chaser[0]["timestamp_ns_session"]) / 1e9 if n > 1 else 0
    return (
        f"<style>{PLAYER_CSS}</style>"
        f'<div class="replay" id="{pid}">'
        f'<div class="ctl"><button class="play">▶ play</button><button class="step-b">◀ step</button><button class="step-f">step ▶</button>'
        f'<label>speed <select><option value="0.25">0.25×</option><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="2">2×</option></select></label>'
        f'<input type="range" min="0" max="{n - 1}" value="0" step="1">'
        f'<span>{n} chaser_states rows (stride {sel["stride"]}), {dur:.1f} s of session time, arena {html.escape(str(lay["arena_id"]))}, camera {html.escape(lay["camera_id"])}</span></div>'
        '<div class="panels">'
        f'<div class="panel p-cam"><h5>camera_view_px · {lay["native"].get("w")}×{lay["native"].get("h")}</h5><svg></svg></div>'
        f'<div class="panel p-can"><h5>final_display_canvas_px · cropped to the arena region ± 15%</h5><svg></svg></div>'
        f'<div class="panel p-arn"><h5>arena_relative_canvas_px · {lay["arena"][0]:.0f}×{lay["arena"][1]:.0f}</h5><svg></svg></div>'
        "</div>"
        '<div class="readout"></div>'
        f'<p class="legend"><span class="sw" style="background:#c9641b"></span>bounding box from <code>bounding_boxes</code> and its corners through <code>homography_matrix</code>, '
        f'bounding-rect center per <code>target_point_method = {html.escape(str(method))}</code>, with a trail · '
        f'<span class="sw" style="border:2px solid #7a3fb5"></span>Citrus <code>target_pos_x/y</code> as written · '
        f'<span class="sw" style="background:#7a9a01"></span>Citrus <code>chaser_pos_x/y</code> at <code>chaser_radius_px</code> · '
        'dashed/blue = arena region and experimental area. Points in the camera panel for Citrus values use the inverse matrix.</p>'
        f'<script type="application/json" id="{pid}-data">{payload}</script>'
        f"<script>const PID={json.dumps(player_id)};{PLAYER_JS}</script>"
        "</div>"
    )
