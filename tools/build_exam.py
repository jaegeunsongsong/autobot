import re, subprocess, html, sys, os
os.chdir('/home/user/autobot/docs/강대K-23회-변형문항')
def md2html(md):
    r=subprocess.run(['pandoc','-f','markdown+tex_math_dollars+hard_line_breaks+raw_html','-t','html','--mathml'],input=md,capture_output=True,text=True)
    return r.stdout
def split_problems(md):
    """return dict num -> html fragment of problem body (without the bold number)"""
    sec=md[md.index('## 공통과목'):]
    out={}
    for m in re.finditer(r"^\*\*(\d+)\.\*\*(.*?)(?=^\*\*\d+\.\*\*|^### |^## |^---|\Z)",sec,re.M|re.S):
        n,body=m.group(1),m.group(2).strip()
        # separate last choices line
        lines=body.split('\n')
        if n not in ('18','19','20','29'):
            ci=max(i for i,l in enumerate(lines) if l.startswith('①'))
            choices=lines[ci]; body='\n'.join(lines[:ci]+lines[ci+1:])
            ch=re.findall(r"([①②③④⑤])\s*(.*?)(?=\s{2,}[①②③④⑤]|$)",choices)
            chtml='<div class="choices">'+''.join(f'<span class="ch">{c} {md2html(t).replace("<p>","").replace("</p>","").strip()}</span>' for c,t in ch)+'</div>'
        else: chtml=''
        pts=re.search(r"\[(\d)점\]",body); 
        h=md2html(body)
        h=re.sub(r'\[(\d)점\]',r'<span style="white-space:nowrap">[\1점]</span>',h)
        out[n]=(h,chtml)
    return out

CSS="""
@page{size:A4;margin:0}
*{box-sizing:border-box}
body{margin:0;font-family:"Noto Serif KR","Noto Sans KR","WenQuanYi Zen Hei","DejaVu Serif",serif;font-size:10.6pt;line-height:1.55;color:#000}
.page{width:210mm;height:297mm;padding:12mm 12mm 10mm 12mm;page-break-after:always;position:relative;overflow:hidden}
.page:last-child{page-break-after:auto}
.hdr{display:flex;align-items:flex-end;justify-content:space-between;border-bottom:2.2px solid #000;padding-bottom:2mm;margin-bottom:3mm}
.hdr .l{font-size:10pt}.hdr .l .gyosi{display:inline-block;border:1.2px solid #000;border-radius:14px;padding:0 7px;font-size:10pt;margin-right:5mm}
.hdr .c{font-size:21pt;font-weight:bold;letter-spacing:4px}
.hdr .c small{font-size:14pt;letter-spacing:0}
.hdr .r{font-size:12pt;font-weight:bold;border:1.6px solid #000;padding:0 6px}
.hdr .pg{font-size:15pt;font-weight:bold}
.top{font-size:10.5pt;text-align:center;margin-bottom:1mm}
.cols{display:flex;height:252mm}
.col{width:50%;padding:0 4mm 0 0}
.col+.col{border-left:1px solid #000;padding:0 0 0 4mm}
.secbox{display:inline-block;border:1.3px solid #000;padding:0 8px;font-weight:bold;margin:2mm 0 3mm}
.prob{margin-bottom:9mm}
.prob .num{font-weight:bold;margin-right:4px}
.prob p{margin:0 0 1.2mm;text-align:justify}
.prob .num+p{display:inline}
.prob math[display=block]{margin:1.5mm 0}
.choices{margin-top:3mm;display:flex;flex-wrap:wrap;gap:2mm 6mm}
.choices .ch{white-space:nowrap}
blockquote{border:1px solid #000;margin:2.5mm 2mm;padding:1.5mm 3mm;font-size:10.2pt}
blockquote p{margin:0.5mm 0!important;display:block!important}
img{display:block;margin:3mm auto;max-width:72mm;max-height:60mm}
.fig-wide img{max-width:80mm}
.foot{position:absolute;bottom:6mm;left:0;right:0;text-align:center;font-size:10.5pt}
.foot span{border:1px solid #000;padding:0 6px}
.confirm{border:1px solid #000;padding:2mm 3mm;font-size:9.6pt;position:absolute;bottom:14mm;right:12mm;width:87mm}
.confirm p{margin:0.5mm 0}
math{font-size:1.05em}
/* answer sheet */
.ans .cols{display:block;height:auto;column-count:2;column-gap:8mm;column-rule:1px solid #000}
.ans .sol{break-inside:avoid;margin-bottom:5mm}
.ans .sol .h{display:flex;justify-content:space-between;border-bottom:1.5px solid #000;margin-bottom:1.5mm;font-weight:bold}
.ans .sol .h .n{font-size:15pt;font-style:italic}
.ans .sol p{margin:0 0 1mm}
.ans table{border-collapse:collapse;margin:2mm auto;font-size:10pt}
.ans td,.ans th{border:1px solid #000;padding:0.5mm 2.2mm;text-align:center}
.ans .qa{break-inside:avoid;margin-bottom:5mm}
.ans .qa .t{font-weight:bold;border:1px solid #000;display:inline-block;padding:0 8px;margin-bottom:2mm}
.ans h2{font-size:12.5pt;border-bottom:1.5px solid #000;margin:2mm 0 3mm}
"""
def header(title_sub, pagenum, total, first=False, subj=None):
    c='수학 영역' + (f'<small>({subj})</small>' if subj else '')
    if first:
        return f'<div class="top">2027학년도 대학수학능력시험 대비 — {title_sub}</div><div class="hdr"><div class="l"><span class="gyosi">제 2 교시</span></div><div class="c">{c}</div><div class="r">변형형</div></div>'
    return f'<div class="hdr"><div class="pg">{pagenum}</div><div class="c">{c}</div><div class="r">변형형</div></div>'
def foot(p,t): return f'<div class="foot"><span>{p} / {t}</span></div>'
def prob(n,P):
    h,ch=P[n]; return f'<div class="prob"><span class="num">{n}.</span>{h}{ch}</div>'
def page(hdr,left,right,p,t,extra=''):
    return f'<div class="page">{hdr}<div class="cols"><div class="col">{left}</div><div class="col">{right}</div></div>{extra}{foot(p,t)}</div>'
SEC5='<div class="secbox">5지선다형</div><br>'; SECD='<div class="secbox">단답형</div><br>'
def confirm(next_subj):
    nxt=f'<p>○ 이어서, 「<b>선택과목({next_subj})</b>」 문제가 제시되니, 자신이 선택한 과목인지 확인하시오.</p>' if next_subj else ''
    return f'<div class="confirm"><p>※ 확인 사항</p><p>○ 답안지의 해당란에 필요한 내용을 정확히 기입(표기)했는지 확인하시오.</p>{nxt}</div>'

def build_exam(subj, mdfile, outhtml):
    md=open(mdfile,encoding='utf-8').read(); P=split_problems(md)
    sub=f'강대모의고사K 23회 변형 ({subj})'; T=7
    pages=[]
    pages.append(page(header(sub,1,T,True), SEC5+prob('8',P)+prob('9',P), prob('10',P)+prob('11',P),1,T))
    pages.append(page(header(sub,2,T), prob('12',P), prob('13',P),2,T))
    pages.append(page(header(sub,3,T), prob('14',P), SECD+prob('18',P)+prob('19',P),3,T))
    pages.append(page(header(sub,4,T), prob('20',P), '',4,T, confirm(subj)))
    pages.append(page(header(sub,5,T,True,subj), SEC5+prob('25',P), prob('26',P),5,T))
    pages.append(page(header(sub,6,T,None,subj), prob('27',P), prob('28',P),6,T))
    pages.append(page(header(sub,7,T,None,subj), SECD+prob('29',P), '',7,T, confirm(None)))
    doc=f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{subj} 문제지</title><style>{CSS}</style></head><body>{"".join(pages)}</body></html>'
    open(outhtml,'w',encoding='utf-8').write(doc)

def build_answer(subj, mdfile, outhtml):
    md=open(mdfile,encoding='utf-8').read()
    tables=re.findall(r"(\| 문항[^\n]*\|\n\|[-| ]*\|\n\| 정답[^\n]*\|)",md)
    thtml=''.join(md2html(t) for t in tables)
    sols=[]
    for m in re.finditer(r"^### (\d+)\. 정답 (\S+)\n(.*?)(?=^### |^---|\Z)",md,re.M|re.S):
        n,a,body=m.groups()
        sols.append(f'<div class="sol"><div class="h"><span class="n">{n}</span><span>정답 | {a}</span></div>{md2html(body.strip())}</div>')
    doc=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{subj} 정답 및 해설</title><style>{CSS}
    .ans .page{{height:auto;min-height:297mm;overflow:visible;page-break-after:auto}}
    .ans .foot{{display:none}}</style></head><body class="ans"><div class="page">
    <div class="top">2027학년도 대학수학능력시험 대비 — 강대모의고사K 23회 변형 ({subj})</div>
    <div class="hdr"><div class="l"></div><div class="c">수학 영역 <small>정답 및 해설</small></div><div class="r">변형형</div></div>
    <div class="qa"><div class="t">빠른 정답</div>{thtml}</div>
    <h2>해설</h2><div class="cols">{"".join(sols)}</div></div></body></html>'''
    open(outhtml,'w',encoding='utf-8').write(doc)

for subj,f in [('미적분','미적분'),('확률과 통계','확통'),('기하','기하')]:
    build_exam(subj,f'{f}-문항.md',f'{f}-문제지.html')
    build_answer(subj,f'{f}-답안지.md',f'{f}-정답및해설.html')
print('built')
